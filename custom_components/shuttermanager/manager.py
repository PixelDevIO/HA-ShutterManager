"""ShutterManager runtime: rooms, window contacts and ventilation."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta
import logging
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
from homeassistant.helpers.event import async_call_later, async_track_state_change_event
from homeassistant.helpers.start import async_at_started
from homeassistant.helpers.storage import Store
from homeassistant.util import dt as dt_util

from .const import (
    CONF_AREA,
    CONF_CLOSE_DELAY,
    CONF_CONTACTS,
    CONF_COVERS,
    CONF_LOCKOUT,
    CONF_OPEN_DELAY,
    CONF_ROOM_ID,
    CONF_ROOM_NAME,
    CONF_ROOMS,
    CONF_VENT_POSITIONS,
    DEFAULT_CLOSE_DELAY,
    DEFAULT_OPEN_DELAY,
    DEFAULT_VENT_POSITION,
    DOMAIN,
    GUARD_REPEAT_S,
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

_LOGGER = logging.getLogger(__name__)

NOT_KNOWN = (None, STATE_UNAVAILABLE, STATE_UNKNOWN)


@dataclass
class Room:
    """A room: its shutters and the window/door contacts that open it."""

    id: str
    name: str
    covers: list[str]
    contacts: list[str]
    vent_positions: dict[str, int]
    # keep shutters at least at their vent position while a contact is open
    lockout: bool = False
    area: str | None = None
    area_name: str | None = None

    def vent_position(self, cover: str) -> int:
        return int(self.vent_positions.get(cover, DEFAULT_VENT_POSITION))


@dataclass
class Vented:
    """A cover ShutterManager raised for ventilation and where it came from."""

    # position before (0–100); None for covers that report no position
    previous: int | None
    target: int
    at: datetime

    def as_dict(self) -> dict[str, Any]:
        return {"previous": self.previous, "target": self.target, "at": self.at.isoformat()}

    @classmethod
    def from_dict(cls, raw: dict[str, Any]) -> Vented:
        return cls(raw.get("previous"), int(raw["target"]), dt_util.parse_datetime(raw["at"]) or dt_util.now())


@dataclass
class RoomRuntime:
    enabled: bool = True
    # a window of the room is open (after the open delay)
    open: bool = False
    open_timer: CALLBACK_TYPE | None = None
    close_timer: CALLBACK_TYPE | None = None
    vented: dict[str, Vented] = field(default_factory=dict)
    # covers that were unavailable when the window opened; vented once they are back
    pending: set[str] = field(default_factory=set)
    # recently restored covers, so a window reopened at once keeps the original position
    restored: dict[str, tuple[Vented, datetime]] = field(default_factory=dict)


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
                contacts=list(raw.get(CONF_CONTACTS) or []),
                vent_positions={k: int(v) for k, v in (raw.get(CONF_VENT_POSITIONS) or {}).items()},
                lockout=bool(raw.get(CONF_LOCKOUT, False)),
                area=raw.get(CONF_AREA),
            )
            if room.area and (area := areas.async_get_area(room.area)):
                room.area_name = area.name
            self.rooms[room.id] = room
            self.runtime[room.id] = RoomRuntime()

        data = await self._store.async_load() or {}
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

    async def _on_started(self, _hass: HomeAssistant) -> None:
        """Pick up where we were before a restart. Windows already open do not move anything new."""
        for room in self.rooms.values():
            rt = self.runtime[room.id]
            if not rt.enabled:
                continue
            state = self._contacts_state(room)
            if state == STATE_ON:
                rt.open = True
            elif state == STATE_OFF and rt.vented:
                # the window was closed while Home Assistant was down
                rt.open = True
                self._start_close_timer(room)
        self._notify()

    # ---------------------------------------------------------------- contacts
    def _contacts_state(self, room: Room) -> str | None:
        """on: a contact is open. off: all are known to be closed. None: unclear (some unavailable)."""
        states = [self.hass.states.get(c) for c in room.contacts]
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
        state = self._contacts_state(room)
        if state == STATE_ON:
            self._cancel(rt, "close_timer")
            if not rt.open and rt.open_timer is None:
                rt.open_timer = async_call_later(self.hass, self.open_delay, self._timer(self._opened, room))
        elif state == STATE_OFF:
            self._cancel(rt, "open_timer")
            # rt.vented also covers a restart while the contacts were unclear
            if (rt.open or rt.vented) and rt.close_timer is None:
                self._start_close_timer(room)
        else:
            # a contact is unavailable and none reports open: we cannot tell whether the
            # window is closed, so nothing moves until the contacts report again
            self._cancel(rt, "open_timer")
            self._cancel(rt, "close_timer")
        self._notify()

    def _start_close_timer(self, room: Room) -> None:
        rt = self.runtime[room.id]
        rt.close_timer = async_call_later(self.hass, self.close_delay, self._timer(self._closed, room))

    def _timer(self, action, room: Room):
        @callback
        def _fire(_now: datetime) -> None:
            action(room)

        return _fire

    @staticmethod
    def _cancel(rt: RoomRuntime, attr: str) -> None:
        if (unsub := getattr(rt, attr)) is not None:
            unsub()
            setattr(rt, attr, None)

    def _cancel_timers(self, rt: RoomRuntime) -> None:
        self._cancel(rt, "open_timer")
        self._cancel(rt, "close_timer")

    # ---------------------------------------------------------------- venting
    @callback
    def _opened(self, room: Room) -> None:
        rt = self.runtime[room.id]
        rt.open_timer = None
        rt.open = True
        for cover in room.covers:
            self._vent(room, cover)
        self._save()
        self._notify()

    def _vent(self, room: Room, cover: str) -> None:
        """Raise one cover to its vent position if it is below it."""
        rt = self.runtime[room.id]
        if cover in rt.vented:
            return
        st = self.hass.states.get(cover)
        if st is None or st.state in NOT_KNOWN:
            rt.pending.add(cover)
            return
        rt.pending.discard(cover)
        target = room.vent_position(cover)
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
        if _supports_position(st):
            self._call(SERVICE_SET_COVER_POSITION, cover, {ATTR_POSITION: target})
        else:
            # no positioning: open it fully, that still lets air in
            self._call(SERVICE_OPEN_COVER, cover)

    @callback
    def _closed(self, room: Room) -> None:
        rt = self.runtime[room.id]
        rt.close_timer = None
        rt.open = False
        rt.pending.clear()
        for cover in list(rt.vented):
            st = self.hass.states.get(cover)
            if st is None or st.state in NOT_KNOWN:
                continue  # restored once the cover is back
            self._restore(room, cover, st)
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
                if room.lockout and self.runtime[room.id].enabled and self._contacts_state(room) == STATE_ON:
                    self._guard(room, cover, new)
            return
        # a cover that was unavailable is back: catch up on what it missed
        for room in self._rooms_with(cover, "covers"):
            rt = self.runtime[room.id]
            if not rt.enabled:
                continue
            if rt.open and cover in rt.pending:
                self._vent(room, cover)
            elif (
                not rt.open
                and rt.close_timer is None
                and cover in rt.vented
                and self._contacts_state(room) == STATE_OFF
            ):
                self._restore(room, cover, new)
            else:
                continue
            self._save()
            self._notify()

    def _guard(self, room: Room, cover: str, st: State) -> None:
        """Lockout protection: something moves the cover below its vent position while a contact is open.

        Send it back up and remember where it was meant to go; that happens once all contacts are closed.
        """
        rt = self.runtime[room.id]
        if st.state == STATE_OPENING:
            return
        target = room.vent_position(cover)
        pos = _position(st)
        if pos is None:
            if st.state not in (STATE_CLOSED, STATE_CLOSING):
                return
        elif pos + POSITION_TOLERANCE >= target:
            return
        now = dt_util.now()
        current = rt.vented.get(cover)
        if current is not None and now - current.at < timedelta(seconds=GUARD_REPEAT_S):
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
        rt.vented[cover] = Vented(wanted, target, now)
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
            rt.open = self._contacts_state(room) == STATE_ON
        else:
            # switched off: leave every shutter where it is
            rt.open = False
            rt.vented.clear()
            rt.restored.clear()
        self._save()
        self._notify()

    def status(self, room: Room) -> str:
        rt = self.runtime[room.id]
        if not rt.enabled:
            return STATUS_DISABLED
        if rt.open_timer is not None or rt.close_timer is not None:
            return STATUS_WAITING
        if rt.vented or rt.pending:
            return STATUS_VENTING
        return STATUS_IDLE

    def room_info(self, room: Room) -> dict[str, Any]:
        rt = self.runtime[room.id]
        return {
            "room": room.name,
            "window_open": rt.open,
            "open_contacts": self.open_contacts(room),
            "vented": {c: v.as_dict() for c, v in rt.vented.items()},
            "pending": sorted(rt.pending),
            "lockout": room.lockout,
            "vent_positions": {c: room.vent_position(c) for c in room.covers},
        }

    # ---------------------------------------------------------------- storage
    def _save(self) -> None:
        self._store.async_delay_save(self._data, 1)

    def _data(self) -> dict[str, Any]:
        return {
            "enabled": {rid: rt.enabled for rid, rt in self.runtime.items()},
            "vented": {
                rid: {c: v.as_dict() for c, v in rt.vented.items()} for rid, rt in self.runtime.items() if rt.vented
            },
        }

    def _notify(self) -> None:
        async_dispatcher_send(self.hass, f"{SIGNAL_UPDATE}_{self.entry.entry_id}")


def get_manager(hass: HomeAssistant) -> ShutterManager:
    for manager in hass.data.get(DOMAIN, {}).values():
        return manager
    raise LookupError("ShutterManager is not set up")
