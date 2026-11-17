"""ShutterManager runtime: rooms, window and door contacts, ventilation and weekly plans."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime, timedelta
import logging
import random
import re
from typing import Any

from homeassistant.components.cover import (
    ATTR_CURRENT_POSITION,
    ATTR_POSITION,
    DOMAIN as COVER_DOMAIN,
    CoverEntityFeature,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    ATTR_ENTITY_ID,
    ATTR_SUPPORTED_FEATURES,
    SERVICE_CLOSE_COVER,
    SERVICE_OPEN_COVER,
    SERVICE_SET_COVER_POSITION,
    STATE_CLOSED,
    STATE_CLOSING,
    STATE_OFF,
    STATE_ON,
    STATE_OPENING,
    STATE_UNAVAILABLE,
    STATE_UNKNOWN,
)
from homeassistant.core import CALLBACK_TYPE, Event, EventStateChangedData, HomeAssistant, State, callback
from homeassistant.helpers import area_registry as ar
from homeassistant.helpers.dispatcher import async_dispatcher_send
from homeassistant.helpers.event import (
    async_call_later,
    async_track_point_in_time,
    async_track_state_change_event,
)
from homeassistant.helpers.start import async_at_started
from homeassistant.helpers.storage import Store
from homeassistant.helpers.sun import get_astral_event_date
from homeassistant.util import dt as dt_util, slugify

from .const import (
    ASSIGN_MANUAL,
    CONF_AREA,
    CONF_CLOSE_DELAY,
    CONF_CONTACTS,
    CONF_COVER_SETTINGS,
    CONF_COVERS,
    CONF_DOOR_CONTACTS,
    CONF_DOOR_COVERS,
    CONF_DOOR_POSITION,
    CONF_OPEN_DELAY,
    CONF_ROOM_ID,
    CONF_ROOM_NAME,
    CONF_ROOMS,
    CONF_VENT_POSITIONS,
    DEFAULT_CLOSE_DELAY,
    DEFAULT_DOOR_POSITION,
    DEFAULT_OPEN_DELAY,
    DEFAULT_VACATION_RANDOM,
    DEFAULT_VENT_POSITION,
    DOMAIN,
    GUARD_REPEAT_S,
    KIND_DOOR,
    KIND_WINDOW,
    KINDS,
    MOVE_GRACE_S,
    POSITION_TOLERANCE,
    SIGNAL_UPDATE,
    STATUS_DISABLED,
    STATUS_IDLE,
    STATUS_VENTING,
    STATUS_WAITING,
    STORAGE_KEY,
    STORAGE_VERSION,
)
from .schedule import DAYS, SUN_EVENTS, SunTimes, day_plan, next_edge, normalize_week, position_at

_LOGGER = logging.getLogger(__name__)

NOT_KNOWN = (None, STATE_UNAVAILABLE, STATE_UNKNOWN)


@dataclass
class CoverSetting:
    """What opens a shutter and how far: its contact (None: any contact of the room) and its kind."""

    contact: str | None = None
    kind: str = KIND_WINDOW
    position: int = DEFAULT_VENT_POSITION

    def as_dict(self) -> dict[str, Any]:
        return {"contact": self.contact, "kind": self.kind, "position": self.position}


@dataclass
class Room:
    """A room: its shutters and the window/door contacts in front of them."""

    id: str
    name: str
    covers: list[str]
    contacts: list[str]
    settings: dict[str, CoverSetting] = field(default_factory=dict)
    area: str | None = None
    area_name: str | None = None

    def setting(self, cover: str) -> CoverSetting:
        return self.settings.get(cover) or CoverSetting()

    def contacts_of(self, cover: str) -> list[str]:
        """The contacts that open this shutter."""
        own = self.setting(cover).contact
        return [own] if own and own in self.contacts else self.contacts

    def vent_position(self, cover: str) -> int:
        return int(self.setting(cover).position)

    def is_door_cover(self, cover: str) -> bool:
        return self.setting(cover).kind == KIND_DOOR


def cover_settings(raw: dict[str, Any]) -> dict[str, CoverSetting]:
    """Per-cover settings of a stored room; rooms from before 0.3.1 are converted."""
    covers = list(raw.get(CONF_COVERS) or [])
    contacts = list(dict.fromkeys([*(raw.get(CONF_CONTACTS) or []), *(raw.get(CONF_DOOR_CONTACTS) or [])]))
    stored = raw.get(CONF_COVER_SETTINGS)
    out: dict[str, CoverSetting] = {}
    if isinstance(stored, dict):
        for cover in covers:
            item = stored.get(cover) or {}
            kind = item.get("kind") if item.get("kind") in KINDS else KIND_WINDOW
            contact = item.get("contact") if item.get("contact") in contacts else None
            default = DEFAULT_DOOR_POSITION if kind == KIND_DOOR else DEFAULT_VENT_POSITION
            out[cover] = CoverSetting(contact, kind, int(item.get("position", default)))
        return out
    # 0.1–0.3.0: vent position per cover, optional door contacts and door covers
    vents = raw.get(CONF_VENT_POSITIONS) or {}
    doors = [c for c in raw.get(CONF_DOOR_CONTACTS) or [] if c in contacts]
    door_covers = [c for c in raw.get(CONF_DOOR_COVERS) or [] if c in covers] if doors else []
    for cover in covers:
        if cover in door_covers or (doors and not raw.get(CONF_DOOR_COVERS)):
            position = int(raw.get(CONF_DOOR_POSITION, DEFAULT_DOOR_POSITION))
            out[cover] = CoverSetting(doors[0] if len(doors) == 1 else None, KIND_DOOR, position)
        else:
            out[cover] = CoverSetting(None, KIND_WINDOW, int(vents.get(cover, DEFAULT_VENT_POSITION)))
    return out


@dataclass
class Vented:
    """A cover ShutterManager raised for ventilation and where it came from."""

    # position before (0–100); None for covers that report no position
    previous: int | None
    target: int
    at: datetime
    # sent back up by lockout protection (not raised for ventilation)
    guarded: bool = False

    def as_dict(self) -> dict[str, Any]:
        return {"previous": self.previous, "target": self.target, "at": self.at.isoformat()}

    @classmethod
    def from_dict(cls, raw: dict[str, Any]) -> Vented:
        return cls(raw.get("previous"), int(raw["target"]), dt_util.parse_datetime(raw["at"]) or dt_util.now())


@dataclass
class RoomRuntime:
    enabled: bool = True
    # covers whose contact is open (after the open delay)
    open: set[str] = field(default_factory=set)
    open_timers: dict[str, CALLBACK_TYPE] = field(default_factory=dict)
    close_timers: dict[str, CALLBACK_TYPE] = field(default_factory=dict)
    vented: dict[str, Vented] = field(default_factory=dict)
    # covers that were unavailable when the window opened; vented once they are back
    pending: set[str] = field(default_factory=set)
    # recently restored covers, so a window reopened at once keeps the original position
    restored: dict[str, tuple[Vented, datetime]] = field(default_factory=dict)
    # schedule: the next planned move and its timer
    next_edge: tuple[datetime, int] | None = None
    schedule_timer: CALLBACK_TYPE | None = None


def _position(state: State) -> int | None:
    pos = state.attributes.get(ATTR_CURRENT_POSITION)
    try:
        return None if pos is None else int(pos)
    except (TypeError, ValueError):
        return None


def _supports_position(state: State) -> bool:
    return bool(int(state.attributes.get(ATTR_SUPPORTED_FEATURES) or 0) & CoverEntityFeature.SET_POSITION)


class ShutterManager:
    """Opens shutters to a vent position while a window is open and closes them again."""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        self.hass = hass
        self.entry = entry
        self.rooms: dict[str, Room] = {}
        self.runtime: dict[str, RoomRuntime] = {}
        self._store: Store = Store(hass, STORAGE_VERSION, f"{STORAGE_KEY}.{entry.entry_id}")
        self._unsubs: list[CALLBACK_TYPE] = []
        # schedule
        self.profiles: dict[str, dict[str, Any]] = {}
        self.assignments: dict[str, str] = {}
        self.pause_active = False
        self.pause_until: datetime | None = None
        self.vacation_until: datetime | None = None
        self.vacation_random = DEFAULT_VACATION_RANDOM
        self._pause_unsub: CALLBACK_TYPE | None = None
        self._vacation_unsub: CALLBACK_TYPE | None = None
        self._sun_cache: dict[date, SunTimes] = {}

    @property
    def open_delay(self) -> int:
        return int(self.entry.options.get(CONF_OPEN_DELAY, DEFAULT_OPEN_DELAY))

    @property
    def close_delay(self) -> int:
        return int(self.entry.options.get(CONF_CLOSE_DELAY, DEFAULT_CLOSE_DELAY))

    # ---------------------------------------------------------------- lifecycle
    async def async_load(self) -> None:
        areas = ar.async_get(self.hass)
        for raw in self.entry.options.get(CONF_ROOMS, []):
            room = Room(
                id=raw[CONF_ROOM_ID],
                name=raw[CONF_ROOM_NAME],
                covers=list(raw.get(CONF_COVERS) or []),
                # rooms from 0.3.0 kept door contacts apart
                contacts=list(dict.fromkeys([*(raw.get(CONF_CONTACTS) or []), *(raw.get(CONF_DOOR_CONTACTS) or [])])),
                settings=cover_settings(raw),
                area=raw.get(CONF_AREA),
            )
            if room.area and (area := areas.async_get_area(room.area)):
                room.area_name = area.name
            self.rooms[room.id] = room
            self.runtime[room.id] = RoomRuntime()

        data = await self._store.async_load() or {}
        self.profiles = dict(data.get("profiles") or {})
        self.assignments = {k: v for k, v in (data.get("assignments") or {}).items() if k in self.rooms}
        pause = data.get("pause") or {}
        self.pause_active = bool(pause.get("active"))
        self.pause_until = _parse(pause.get("until"))
        vacation = data.get("vacation") or {}
        self.vacation_until = _parse(vacation.get("until"))
        self.vacation_random = int(vacation.get("random", DEFAULT_VACATION_RANDOM))
        now = dt_util.now()
        if self.pause_until is not None and self.pause_until <= now:
            self.pause_active, self.pause_until = False, None
        if self.vacation_until is not None and self.vacation_until <= now:
            self.vacation_until = None
        for room_id, enabled in (data.get("enabled") or {}).items():
            if room_id in self.runtime:
                self.runtime[room_id].enabled = bool(enabled)
        for room_id, covers in (data.get("vented") or {}).items():
            if room_id not in self.rooms:
                continue
            room, rt = self.rooms[room_id], self.runtime[room_id]
            for cover, raw in covers.items():
                if cover in room.covers:
                    try:
                        rt.vented[cover] = Vented.from_dict(raw)
                    except (KeyError, TypeError, ValueError):
                        _LOGGER.debug("Dropping unreadable record for %s", cover)

    async def async_start(self) -> None:
        contacts = sorted({c for room in self.rooms.values() for c in room.contacts})
        covers = sorted({c for room in self.rooms.values() for c in room.covers})
        if contacts:
            self._unsubs.append(async_track_state_change_event(self.hass, contacts, self._on_contact_event))
        if covers:
            self._unsubs.append(async_track_state_change_event(self.hass, covers, self._on_cover_event))
        self._unsubs.append(async_at_started(self.hass, self._on_started))

    @callback
    def async_stop(self) -> None:
        for unsub in self._unsubs:
            unsub()
        self._unsubs.clear()
        for rt in self.runtime.values():
            self._cancel_timers(rt)
            self._cancel(rt, "schedule_timer")
        for attr in ("_pause_unsub", "_vacation_unsub"):
            if (unsub := getattr(self, attr)) is not None:
                unsub()
                setattr(self, attr, None)

    async def _on_started(self, _hass: HomeAssistant) -> None:
        """Pick up where we were before a restart. Windows already open do not move anything new."""
        for room in self.rooms.values():
            rt = self.runtime[room.id]
            if not rt.enabled:
                continue
            for cover in room.covers:
                state = self.contact_state(room, cover)
                if state == STATE_ON:
                    rt.open.add(cover)
                elif state == STATE_OFF and cover in rt.vented:
                    # the window was closed while Home Assistant was down
                    rt.open.add(cover)
                    self._start_close_timer(room, cover)
        self._schedule_pause_end()
        self._schedule_vacation_end()
        # the schedule only acts at its next change: a restart never moves anything
        self.schedule_all()

    # ---------------------------------------------------------------- contacts
    def contact_state(self, room: Room, cover: str) -> str | None:
        """For one shutter: on = one of its contacts is open, off = all are known to be closed,
        None = unclear (some unavailable)."""
        states = [self.hass.states.get(c) for c in room.contacts_of(cover)]
        if any(st is not None and st.state == STATE_ON for st in states):
            return STATE_ON
        if states and all(st is not None and st.state == STATE_OFF for st in states):
            return STATE_OFF
        return None

    def open_contacts(self, room: Room) -> list[str]:
        return [c for c in room.contacts if (st := self.hass.states.get(c)) is not None and st.state == STATE_ON]

    def _rooms_with(self, entity_id: str, attr: str) -> list[Room]:
        return [room for room in self.rooms.values() if entity_id in getattr(room, attr)]

    @callback
    def _on_contact_event(self, event: Event[EventStateChangedData]) -> None:
        for room in self._rooms_with(event.data["entity_id"], "contacts"):
            self._evaluate_contacts(room)

    @callback
    def _evaluate_contacts(self, room: Room) -> None:
        rt = self.runtime[room.id]
        if not rt.enabled:
            return
        changed = False
        for cover in room.covers:
            state = self.contact_state(room, cover)
            if state == STATE_ON:
                self._cancel_cover(rt.close_timers, cover)
                if cover in rt.open:
                    # already open: a shutter may still have to catch up (e.g. it was moved meanwhile)
                    self._vent(room, cover)
                    changed = True
                elif cover not in rt.open_timers:
                    rt.open_timers[cover] = async_call_later(
                        self.hass, self.open_delay, self._timer(self._opened, room, cover)
                    )
            elif state == STATE_OFF:
                self._cancel_cover(rt.open_timers, cover)
                # rt.vented also covers a restart while the contacts were unclear
                if (cover in rt.open or cover in rt.vented) and cover not in rt.close_timers:
                    self._start_close_timer(room, cover)
            else:
                # a contact is unavailable and none reports open: we cannot tell whether the
                # window is closed, so nothing moves until the contacts report again
                self._cancel_cover(rt.open_timers, cover)
                self._cancel_cover(rt.close_timers, cover)
        if changed:
            self._save()
        self._notify()

    def _start_close_timer(self, room: Room, cover: str) -> None:
        rt = self.runtime[room.id]
        rt.close_timers[cover] = async_call_later(self.hass, self.close_delay, self._timer(self._closed, room, cover))

    def _timer(self, action, room: Room, cover: str):
        @callback
        def _fire(_now: datetime) -> None:
            action(room, cover)

        return _fire

    @staticmethod
    def _cancel(rt: RoomRuntime, attr: str) -> None:
        if (unsub := getattr(rt, attr)) is not None:
            unsub()
            setattr(rt, attr, None)

    @staticmethod
    def _cancel_cover(timers: dict[str, CALLBACK_TYPE], cover: str) -> None:
        if (unsub := timers.pop(cover, None)) is not None:
            unsub()

    def _cancel_timers(self, rt: RoomRuntime) -> None:
        for timers in (rt.open_timers, rt.close_timers):
            for unsub in timers.values():
                unsub()
            timers.clear()

    # ---------------------------------------------------------------- venting
    @callback
    def _opened(self, room: Room, cover: str) -> None:
        rt = self.runtime[room.id]
        rt.open_timers.pop(cover, None)
        rt.open.add(cover)
        self._vent(room, cover)
        self._save()
        self._notify()

    def floor(self, room: Room, cover: str) -> int:
        """The lowest position a shutter may have now: its vent or door position while its contact is open."""
        if not self.runtime[room.id].enabled or self.contact_state(room, cover) != STATE_ON:
            return 0
        return room.vent_position(cover)

    def _vent(self, room: Room, cover: str) -> None:
        """Raise one cover to its position if it is below it."""
        rt = self.runtime[room.id]
        target = self.floor(room, cover)
        current = rt.vented.get(cover)
        if current is not None and current.target >= target:
            return
        st = self.hass.states.get(cover)
        if st is None or st.state in NOT_KNOWN:
            rt.pending.add(cover)
            return
        rt.pending.discard(cover)
        if target <= 0:
            return
        if current is not None:
            current.target = target
            self._send(cover, st, target)
            return
        pos = _position(st)
        if pos is None:
            below = st.state == STATE_CLOSED
        else:
            below = pos + POSITION_TOLERANCE < target
        if not below:
            return
        now = dt_util.now()
        previous = pos
        recent = rt.restored.pop(cover, None)
        if recent is not None and now - recent[1] < timedelta(seconds=MOVE_GRACE_S):
            # window reopened while the cover was still going back: keep the original position
            previous = recent[0].previous
        rt.vented[cover] = Vented(previous, target, now)
        self._send(cover, st, target)

    def _send(self, cover: str, st: State, position: int) -> None:
        """Move a cover; without positioning anything above 0 opens it fully."""
        if _supports_position(st):
            self._call(SERVICE_SET_COVER_POSITION, cover, {ATTR_POSITION: position})
        elif position > 0:
            self._call(SERVICE_OPEN_COVER, cover)
        else:
            self._call(SERVICE_CLOSE_COVER, cover)

    @callback
    def _closed(self, room: Room, cover: str) -> None:
        rt = self.runtime[room.id]
        rt.close_timers.pop(cover, None)
        rt.open.discard(cover)
        rt.pending.discard(cover)
        if cover in rt.vented:
            st = self.hass.states.get(cover)
            if st is not None and st.state not in NOT_KNOWN:
                self._restore(room, cover, st)
            # otherwise restored once the cover is back
        self._save()
        self._notify()

    def _restore(self, room: Room, cover: str, st: State) -> None:
        rt = self.runtime[room.id]
        vented = rt.vented.pop(cover)
        if not self._untouched(vented, st):
            _LOGGER.debug("%s was moved by hand while venting, leaving it", cover)
            return
        rt.restored[cover] = (vented, dt_util.now())
        if vented.previous is not None and _supports_position(st):
            self._call(SERVICE_SET_COVER_POSITION, cover, {ATTR_POSITION: vented.previous})
        else:
            self._call(SERVICE_CLOSE_COVER, cover)

    @staticmethod
    def _untouched(vented: Vented, st: State) -> bool:
        """Is the cover still where we put it (or on its way there)?"""
        pos = _position(st)
        if pos is None:
            return st.state != STATE_CLOSED
        if abs(pos - vented.target) <= POSITION_TOLERANCE:
            return True
        moving = st.state in (STATE_OPENING, STATE_CLOSING) or dt_util.now() - vented.at < timedelta(
            seconds=MOVE_GRACE_S
        )
        low = min(vented.previous or 0, vented.target) - POSITION_TOLERANCE
        high = max(vented.previous or 0, vented.target) + POSITION_TOLERANCE
        return moving and low <= pos <= high

    @callback
    def _on_cover_event(self, event: Event[EventStateChangedData]) -> None:
        old, new = event.data["old_state"], event.data["new_state"]
        if new is None or new.state in NOT_KNOWN:
            return
        cover = event.data["entity_id"]
        if old is not None and old.state not in NOT_KNOWN:
            for room in self._rooms_with(cover, "covers"):
                if self.runtime[room.id].enabled and self.contact_state(room, cover) == STATE_ON:
                    self._guard(room, cover, new)
            return
        # a cover that was unavailable is back: catch up on what it missed
        for room in self._rooms_with(cover, "covers"):
            rt = self.runtime[room.id]
            if not rt.enabled:
                continue
            if cover in rt.open and cover in rt.pending:
                self._vent(room, cover)
            elif (
                cover not in rt.open
                and cover not in rt.close_timers
                and cover in rt.vented
                and self.contact_state(room, cover) == STATE_OFF
            ):
                self._restore(room, cover, new)
            else:
                continue
            self._save()
            self._notify()

    def _guard(self, room: Room, cover: str, st: State) -> None:
        """Lockout protection: something moves the shutter below its position while its contact is open.

        Send it back up and remember where it was meant to go; that happens once the contact is closed.
        """
        rt = self.runtime[room.id]
        if st.state == STATE_OPENING:
            return
        target = self.floor(room, cover)
        if target <= 0:
            return
        pos = _position(st)
        if pos is None:
            if st.state not in (STATE_CLOSED, STATE_CLOSING):
                return
        elif pos + POSITION_TOLERANCE >= target:
            return
        now = dt_util.now()
        current = rt.vented.get(cover)
        if current is not None and current.guarded and now - current.at < timedelta(seconds=GUARD_REPEAT_S):
            return  # already sent it back up, the cover is still reporting the old movement
        if pos is None:
            wanted = None
        elif st.state == STATE_CLOSING:
            wanted = 0  # on its way down: where it stops is unknown, closed is what was asked for
        else:
            wanted = pos
        recent = rt.restored.pop(cover, None)
        if recent is not None and now - recent[1] < timedelta(seconds=MOVE_GRACE_S):
            # our own return movement, interrupted by the window opening again
            wanted = recent[0].previous
        _LOGGER.debug("Lockout protection: keeping %s at %s %%, later %s", cover, target, wanted)
        rt.vented[cover] = Vented(wanted, target, now, guarded=True)
        rt.pending.discard(cover)
        if _supports_position(st):
            self._call(SERVICE_SET_COVER_POSITION, cover, {ATTR_POSITION: target})
        else:
            self._call(SERVICE_OPEN_COVER, cover)
        self._save()
        self._notify()

    def _call(self, service: str, cover: str, data: dict[str, Any] | None = None) -> None:
        self.hass.async_create_task(
            self.hass.services.async_call(
                COVER_DOMAIN, service, {ATTR_ENTITY_ID: cover, **(data or {})}, blocking=False
            ),
            eager_start=True,
        )

    # ---------------------------------------------------------------- switches
    def set_enabled(self, room_id: str, enabled: bool) -> None:
        room, rt = self.rooms[room_id], self.runtime[room_id]
        rt.enabled = enabled
        self._cancel_timers(rt)
        rt.pending.clear()
        if enabled:
            # an already open window only counts once it is closed and opened again
            rt.open = {c for c in room.covers if self.contact_state(room, c) == STATE_ON}
        else:
            # switched off: leave every shutter where it is
            rt.open = set()
            rt.vented.clear()
            rt.restored.clear()
        self._save()
        self._notify()

    def status(self, room: Room) -> str:
        rt = self.runtime[room.id]
        if not rt.enabled:
            return STATUS_DISABLED
        if rt.open_timers or rt.close_timers:
            return STATUS_WAITING
        if rt.vented or rt.pending:
            return STATUS_VENTING
        return STATUS_IDLE

    def room_info(self, room: Room) -> dict[str, Any]:
        rt = self.runtime[room.id]
        active = self.active_profile(room)
        today = dt_util.now().date()
        door_covers = [c for c in room.covers if room.is_door_cover(c)]
        door_contacts = sorted({c for cover in door_covers for c in room.contacts_of(cover)})
        return {
            "id": room.id,
            "name": room.name,
            "covers": room.covers,
            "contacts": room.contacts,
            "cover_settings": {c: room.setting(c).as_dict() for c in room.covers},
            "window_contacts": [c for c in room.contacts if c not in door_contacts],
            "door_contacts": door_contacts,
            "door_covers": door_covers,
            "enabled": rt.enabled,
            "status": self.status(room),
            "profile": self.assignments.get(room.id, ASSIGN_MANUAL),
            "following": active[0] if active else None,
            "next_change": _iso(rt.next_edge[0]) if rt.next_edge else None,
            "next_position": rt.next_edge[1] if rt.next_edge else None,
            "today": [list(seg) for seg in day_plan(active[1], today, self.sun(today))] if active else [],
            "room": room.name,
            "window_open": bool(self.open_contacts(room)),
            "open_contacts": self.open_contacts(room),
            "vented": {c: v.as_dict() for c, v in rt.vented.items()},
            "pending": sorted(rt.pending),
            "vent_positions": {c: room.vent_position(c) for c in room.covers},
        }

    # ---------------------------------------------------------------- schedule
    def sun(self, day: date) -> SunTimes:
        """Sunrise and sunset of a date in local minutes after midnight."""
        if (cached := self._sun_cache.get(day)) is not None:
            return cached
        out: SunTimes = {}
        for event in SUN_EVENTS:
            moment = get_astral_event_date(self.hass, event, day)
            if moment is None:
                out[event] = None
            else:
                local = dt_util.as_local(moment)
                out[event] = local.hour * 60 + local.minute
        if len(self._sun_cache) > 30:
            self._sun_cache.clear()
        self._sun_cache[day] = out
        return out

    @property
    def vacation_profile(self) -> str | None:
        return next((pid for pid, p in self.profiles.items() if p.get("vacation")), None)

    @property
    def vacation_active(self) -> bool:
        return self.vacation_until is not None

    def active_profile(self, room: Room) -> tuple[str, dict[str, Any]] | None:
        """The profile a room follows right now (the vacation plan while on vacation)."""
        assigned = self.assignments.get(room.id, ASSIGN_MANUAL)
        if assigned not in self.profiles:
            return None
        if self.vacation_active and (vac := self.vacation_profile) is not None:
            return vac, self.profiles[vac]
        return assigned, self.profiles[assigned]

    @callback
    def schedule_all(self) -> None:
        for room in self.rooms.values():
            self._schedule(room)
        self._notify()

    @callback
    def _schedule(self, room: Room) -> None:
        rt = self.runtime[room.id]
        self._cancel(rt, "schedule_timer")
        rt.next_edge = None
        active = self.active_profile(room)
        if active is None:
            return
        _pid, profile = active
        found = next_edge(profile, dt_util.now(), self.sun)
        if found is None:
            return
        when, position = found
        rt.next_edge = found
        fire = when
        if self.vacation_active and self.vacation_random > 0:
            # nobody is home: not every day at the same minute
            fire = when + timedelta(seconds=random.randint(0, self.vacation_random * 60))

        @callback
        def _run(_now: datetime) -> None:
            rt.schedule_timer = None
            if not self.pause_active:
                self.apply_position(room, position)
            self._schedule(room)
            self._notify()

        rt.schedule_timer = async_track_point_in_time(self.hass, _run, fire)

    def apply_position(self, room: Room, position: int) -> None:
        """Move all shutters of a room, respecting ventilation and lockout."""
        for cover in room.covers:
            self.request_position(room, cover, position)
        self._save()
        self._notify()

    def apply_plan_now(self, room_id: str) -> None:
        """Move a room's shutters to the position its plan has right now."""
        room = self.rooms[room_id]
        active = self.active_profile(room)
        if active is None:
            raise ValueError("room follows no plan")
        self.apply_position(room, position_at(active[1], dt_util.now(), self.sun))

    def request_position(self, room: Room, cover: str, position: int) -> None:
        """Move a cover; while a contact keeps it up, the move happens once the contacts are closed."""
        st = self.hass.states.get(cover)
        if st is None or st.state in NOT_KNOWN:
            _LOGGER.debug("%s is not available, skipping the planned move", cover)
            return
        rt = self.runtime[room.id]
        floor = self.floor(room, cover)
        if floor and position + POSITION_TOLERANCE < floor:
            current = rt.vented.get(cover)
            if current is not None:
                current.previous = position
            else:
                rt.vented[cover] = Vented(position, floor, dt_util.now())
            # as low as allowed for now, the rest once the contacts are closed
            pos = _position(st)
            if pos is None or abs(pos - floor) > POSITION_TOLERANCE:
                self._send(cover, st, floor)
            return
        rt.vented.pop(cover, None)
        self._send(cover, st, position)

    # ------------------------------------------------------------ profiles
    def save_profile(self, data: dict[str, Any], profile_id: str | None = None) -> str:
        """Create or update a profile; return its id."""
        name = str(data.get("name", "")).strip()
        if not name:
            raise ValueError("name required")
        week = normalize_week(data.get("week"))
        base = int(round(float(data.get("base_position", 0))))
        if not 0 <= base <= 100:
            raise ValueError("base position out of range")
        for pid, other in self.profiles.items():
            if pid != profile_id and other["name"].casefold() == name.casefold():
                raise ValueError("name already used")
        if profile_id is None:
            base_id = slugify(name) or "profile"
            profile_id, n = base_id, 2
            while profile_id in self.profiles or profile_id == ASSIGN_MANUAL:
                profile_id, n = f"{base_id}_{n}", n + 1
        elif profile_id not in self.profiles:
            raise KeyError(profile_id)
        color = data.get("color") or None
        if color is not None and not re.fullmatch(r"#[0-9a-fA-F]{6}", str(color)):
            raise ValueError("invalid color")
        vacation = bool(data.get("vacation", False))
        if vacation:
            # only one vacation plan
            for other in self.profiles.values():
                other["vacation"] = False
        self.profiles[profile_id] = {
            "name": name,
            "icon": str(data.get("icon") or "mdi:window-shutter"),
            "color": color,
            "base_position": base,
            "vacation": vacation,
            "week": week,
        }
        self._save()
        self.schedule_all()
        return profile_id

    def delete_profile(self, profile_id: str) -> None:
        """Delete a profile; rooms using it are left alone from then on."""
        if profile_id not in self.profiles:
            raise KeyError(profile_id)
        del self.profiles[profile_id]
        for room_id, value in list(self.assignments.items()):
            if value == profile_id:
                self.assignments[room_id] = ASSIGN_MANUAL
        self._save()
        self.schedule_all()

    def set_assignment(self, room_id: str, value: str) -> None:
        if room_id not in self.rooms:
            raise KeyError(room_id)
        if value != ASSIGN_MANUAL and value not in self.profiles:
            raise ValueError(f"unknown profile {value}")
        self.assignments[room_id] = value
        self._save()
        self._schedule(self.rooms[room_id])
        self._notify()

    def set_pause(self, active: bool, until: datetime | None = None) -> None:
        """Pause the schedule (optionally until a moment) or resume it."""
        if active and until is not None and until <= dt_util.now():
            raise ValueError("end must be in the future")
        self.pause_active = active
        self.pause_until = until if active else None
        self._schedule_pause_end()
        self._save()
        self._notify()

    @callback
    def _schedule_pause_end(self) -> None:
        if self._pause_unsub:
            self._pause_unsub()
            self._pause_unsub = None
        if self.pause_active and self.pause_until:
            self._pause_unsub = async_track_point_in_time(
                self.hass, callback(lambda _now: self.set_pause(False)), self.pause_until
            )

    def set_vacation(self, until: datetime | None, random_minutes: int | None = None) -> None:
        """Follow the vacation plan until a moment (None ends it)."""
        if until is not None:
            if until <= dt_util.now():
                raise ValueError("end must be in the future")
            if self.vacation_profile is None:
                raise ValueError("no vacation plan")
        if random_minutes is not None:
            self.vacation_random = max(0, min(120, int(random_minutes)))
        self.vacation_until = until
        self._schedule_vacation_end()
        self._save()
        self.schedule_all()

    @callback
    def _schedule_vacation_end(self) -> None:
        if self._vacation_unsub:
            self._vacation_unsub()
            self._vacation_unsub = None
        if self.vacation_until:
            self._vacation_unsub = async_track_point_in_time(
                self.hass, callback(lambda _now: self.set_vacation(None)), self.vacation_until
            )

    def as_dict(self) -> dict[str, Any]:
        """Full state for the card."""
        today = dt_util.now().date()
        week_sun = {}
        for offset in range(7):
            day = today + timedelta(days=offset)
            week_sun[DAYS[day.weekday()]] = self.sun(day)
        return {
            "profiles": [{"id": pid, **p} for pid, p in self.profiles.items()],
            "rooms": [self.room_info(r) for r in self.rooms.values()],
            "pause": {"active": self.pause_active, "until": _iso(self.pause_until)},
            "vacation": {
                "until": _iso(self.vacation_until),
                "profile": self.vacation_profile,
                "random": self.vacation_random,
            },
            "sun": week_sun,
            "settings": {"open_delay": self.open_delay, "close_delay": self.close_delay},
        }

    # ---------------------------------------------------------------- storage
    def _save(self) -> None:
        self._store.async_delay_save(self._data, 1)

    def _data(self) -> dict[str, Any]:
        return {
            "profiles": self.profiles,
            "assignments": self.assignments,
            "pause": {"active": self.pause_active, "until": _iso(self.pause_until)},
            "vacation": {"until": _iso(self.vacation_until), "random": self.vacation_random},
            "enabled": {rid: rt.enabled for rid, rt in self.runtime.items()},
            "vented": {
                rid: {c: v.as_dict() for c, v in rt.vented.items()} for rid, rt in self.runtime.items() if rt.vented
            },
        }

    def _notify(self) -> None:
        async_dispatcher_send(self.hass, f"{SIGNAL_UPDATE}_{self.entry.entry_id}")


def _parse(value: Any) -> datetime | None:
    if not value:
        return None
    parsed = dt_util.parse_datetime(str(value))
    return dt_util.as_local(parsed) if parsed else None


def _iso(value: datetime | None) -> str | None:
    return value.isoformat() if value else None


def get_manager(hass: HomeAssistant) -> ShutterManager:
    for manager in hass.data.get(DOMAIN, {}).values():
        return manager
    raise LookupError("ShutterManager is not set up")
