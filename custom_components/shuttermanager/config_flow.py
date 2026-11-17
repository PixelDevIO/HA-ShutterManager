"""Config and options flow for ShutterManager."""

from __future__ import annotations

from typing import Any
import uuid

from homeassistant.config_entries import ConfigEntry, ConfigFlow, ConfigFlowResult, OptionsFlow
from homeassistant.core import callback
from homeassistant.helpers import selector
import voluptuous as vol

from .const import (
    CONF_AREA,
    CONF_CLOSE_DELAY,
    CONF_CONTACT,
    CONF_CONTACTS,
    CONF_COVER_SETTINGS,
    CONF_COVERS,
    CONF_DOOR_CONTACTS,
    CONF_KIND,
    CONF_OPEN_DELAY,
    CONF_POSITION,
    CONF_ROOM_ID,
    CONF_ROOM_NAME,
    CONF_ROOMS,
    CONTACT_ANY,
    DEFAULT_CLOSE_DELAY,
    DEFAULT_DOOR_POSITION,
    DEFAULT_OPEN_DELAY,
    DEFAULT_VENT_POSITION,
    DOMAIN,
    KIND_DOOR,
    KIND_WINDOW,
    KINDS,
    NAME,
)
from .manager import cover_settings

CONF_ROOM = "room"
# per-cover fields are numbered (contact_1, kind_1, position_1 …) so they get proper labels
MAX_COVERS = 10


def _box(low: float, high: float, step: float, unit: str) -> selector.NumberSelector:
    return selector.NumberSelector(
        selector.NumberSelectorConfig(
            min=low, max=high, step=step, unit_of_measurement=unit, mode=selector.NumberSelectorMode.BOX
        )
    )


def _settings_schema(open_delay: int, close_delay: int) -> vol.Schema:
    return vol.Schema(
        {
            vol.Required(CONF_OPEN_DELAY, default=open_delay): _box(0, 300, 1, "s"),
            vol.Required(CONF_CLOSE_DELAY, default=close_delay): _box(0, 600, 1, "s"),
        }
    )


def _room_schema(room: dict[str, Any] | None = None) -> vol.Schema:
    room = room or {}
    contacts = list(dict.fromkeys([*(room.get(CONF_CONTACTS) or []), *(room.get(CONF_DOOR_CONTACTS) or [])]))
    return vol.Schema(
        {
            vol.Required(CONF_ROOM_NAME, default=room.get(CONF_ROOM_NAME, vol.UNDEFINED)): selector.TextSelector(),
            vol.Optional(CONF_AREA, description={"suggested_value": room.get(CONF_AREA)}): selector.AreaSelector(),
            vol.Required(CONF_COVERS, default=room.get(CONF_COVERS, vol.UNDEFINED)): selector.EntitySelector(
                selector.EntitySelectorConfig(domain="cover", multiple=True)
            ),
            vol.Required(CONF_CONTACTS, default=contacts or vol.UNDEFINED): selector.EntitySelector(
                selector.EntitySelectorConfig(domain="binary_sensor", multiple=True)
            ),
        }
    )


class ShutterManagerConfigFlow(ConfigFlow, domain=DOMAIN):
    """Initial setup: global settings. Rooms are added in the options."""

    VERSION = 1

    async def async_step_user(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        await self.async_set_unique_id(DOMAIN)
        self._abort_if_unique_id_configured()
        if user_input is not None:
            return self.async_create_entry(
                title=NAME,
                data={},
                options={
                    CONF_ROOMS: [],
                    CONF_OPEN_DELAY: int(user_input[CONF_OPEN_DELAY]),
                    CONF_CLOSE_DELAY: int(user_input[CONF_CLOSE_DELAY]),
                },
            )
        return self.async_show_form(
            step_id="user", data_schema=_settings_schema(DEFAULT_OPEN_DELAY, DEFAULT_CLOSE_DELAY)
        )

    @staticmethod
    @callback
    def async_get_options_flow(config_entry: ConfigEntry) -> OptionsFlow:
        return ShutterManagerOptionsFlow()


class ShutterManagerOptionsFlow(OptionsFlow):
    """Manage rooms and settings."""

    def __init__(self) -> None:
        self._room_id: str | None = None
        # room being added or edited, saved after its last step
        self._pending: dict[str, Any] = {}

    @property
    def _rooms(self) -> list[dict[str, Any]]:
        return list(self.config_entry.options.get(CONF_ROOMS, []))

    def _save(self, **changes: Any) -> ConfigFlowResult:
        return self.async_create_entry(data={**self.config_entry.options, **changes})

    async def async_step_init(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        options = ["add_room"]
        if self._rooms:
            options += ["edit_room", "remove_room"]
        options += ["settings"]
        return self.async_show_menu(step_id="init", menu_options=options)

    def _validate(self, room: dict[str, Any]) -> dict[str, str]:
        others = [r for r in self._rooms if r[CONF_ROOM_ID] != room[CONF_ROOM_ID]]
        if not room[CONF_COVERS]:
            return {CONF_COVERS: "no_cover"}
        if len(room[CONF_COVERS]) > MAX_COVERS:
            return {CONF_COVERS: "too_many_covers"}
        if not room[CONF_CONTACTS]:
            return {CONF_CONTACTS: "no_contact"}
        if any(r[CONF_ROOM_NAME].casefold() == room[CONF_ROOM_NAME].casefold() for r in others):
            return {CONF_ROOM_NAME: "name_exists"}
        # one cover belongs to one room, otherwise two rooms would fight over it
        used = {c for r in others for c in r.get(CONF_COVERS) or []}
        if used & set(room[CONF_COVERS]):
            return {CONF_COVERS: "cover_in_use"}
        return {}

    async def async_step_add_room(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        errors: dict[str, str] = {}
        if user_input is not None:
            room = self._clean_room(user_input, uuid.uuid4().hex[:8])
            if not (errors := self._validate(room)):
                self._pending = room
                return await self.async_step_room_covers()
        return self.async_show_form(step_id="add_room", data_schema=_room_schema(user_input), errors=errors)

    async def async_step_room_covers(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        """Per shutter: the contact in front of it, window or door, and its position."""
        room = self._pending
        numbered = list(enumerate(room[CONF_COVERS], 1))
        if user_input is not None:
            settings = {}
            for i, cover in numbered:
                kind = user_input.get(f"kind_{i}", KIND_WINDOW)
                contact = user_input.get(f"contact_{i}", CONTACT_ANY)
                position = user_input.get(f"position_{i}")
                if position is None:
                    position = DEFAULT_DOOR_POSITION if kind == KIND_DOOR else DEFAULT_VENT_POSITION
                settings[cover] = {
                    CONF_CONTACT: contact if contact in room[CONF_CONTACTS] else None,
                    CONF_KIND: kind if kind in KINDS else KIND_WINDOW,
                    CONF_POSITION: int(position),
                }
            room[CONF_COVER_SETTINGS] = settings
            return self._store_room(room)
        current = room.pop("_current", {})
        names = {e: st.name if (st := self.hass.states.get(e)) else e for e in room[CONF_COVERS] + room[CONF_CONTACTS]}
        contact_choice = selector.SelectSelector(
            selector.SelectSelectorConfig(
                options=[selector.SelectOptionDict(value=CONTACT_ANY, label=CONTACT_ANY)]
                + [selector.SelectOptionDict(value=c, label=names[c]) for c in room[CONF_CONTACTS]],
                mode=selector.SelectSelectorMode.DROPDOWN,
                translation_key="contact",
            )
        )
        kind_choice = selector.SelectSelector(
            selector.SelectSelectorConfig(
                options=list(KINDS), mode=selector.SelectSelectorMode.LIST, translation_key="kind"
            )
        )
        schema: dict[Any, Any] = {}
        for i, cover in numbered:
            setting = current.get(cover)
            contact = setting.contact if setting and setting.contact in room[CONF_CONTACTS] else None
            if contact is None and len(room[CONF_CONTACTS]) == 1:
                contact = room[CONF_CONTACTS][0]
            schema[vol.Required(f"contact_{i}", default=contact or CONTACT_ANY)] = contact_choice
            schema[vol.Required(f"kind_{i}", default=setting.kind if setting else KIND_WINDOW)] = kind_choice
            # empty: 30 % for a window, 100 % for a door
            suggested = setting.position if setting else None
            schema[vol.Optional(f"position_{i}", description={"suggested_value": suggested})] = _box(1, 100, 1, "%")
        legend = "\n".join(f"{i} = {names[c]}" for i, c in numbered)
        return self.async_show_form(
            step_id="room_covers",
            data_schema=vol.Schema(schema),
            description_placeholders={"room": room[CONF_ROOM_NAME], "covers": legend},
        )

    def _store_room(self, room: dict[str, Any]) -> ConfigFlowResult:
        rooms = self._rooms
        if any(r[CONF_ROOM_ID] == room[CONF_ROOM_ID] for r in rooms):
            rooms = [room if r[CONF_ROOM_ID] == room[CONF_ROOM_ID] else r for r in rooms]
        else:
            rooms.append(room)
        return self._save(**{CONF_ROOMS: rooms})

    def _room_choices(self, multiple: bool = False) -> selector.SelectSelector:
        return selector.SelectSelector(
            selector.SelectSelectorConfig(
                options=[
                    selector.SelectOptionDict(value=r[CONF_ROOM_ID], label=r[CONF_ROOM_NAME]) for r in self._rooms
                ],
                multiple=multiple,
            )
        )

    async def async_step_edit_room(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        if user_input is not None:
            self._room_id = user_input[CONF_ROOM]
            return await self.async_step_edit_room_details()
        return self.async_show_form(
            step_id="edit_room", data_schema=vol.Schema({vol.Required(CONF_ROOM): self._room_choices()})
        )

    async def async_step_edit_room_details(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        current = next(r for r in self._rooms if r[CONF_ROOM_ID] == self._room_id)
        errors: dict[str, str] = {}
        if user_input is not None:
            room = self._clean_room(user_input, current[CONF_ROOM_ID])
            if not (errors := self._validate(room)):
                # the settings of shutters that stay in the room are kept
                room["_current"] = cover_settings(current)
                self._pending = room
                return await self.async_step_room_covers()
        return self.async_show_form(
            step_id="edit_room_details",
            data_schema=_room_schema(user_input or current),
            errors=errors,
            description_placeholders={"room": current[CONF_ROOM_NAME]},
        )

    async def async_step_remove_room(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        if user_input is not None:
            remove = set(user_input[CONF_ROOMS])
            return self._save(**{CONF_ROOMS: [r for r in self._rooms if r[CONF_ROOM_ID] not in remove]})
        return self.async_show_form(
            step_id="remove_room", data_schema=vol.Schema({vol.Required(CONF_ROOMS): self._room_choices(True)})
        )

    async def async_step_settings(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        options = self.config_entry.options
        if user_input is not None:
            return self._save(
                **{
                    CONF_OPEN_DELAY: int(user_input[CONF_OPEN_DELAY]),
                    CONF_CLOSE_DELAY: int(user_input[CONF_CLOSE_DELAY]),
                }
            )
        return self.async_show_form(
            step_id="settings",
            data_schema=_settings_schema(
                options.get(CONF_OPEN_DELAY, DEFAULT_OPEN_DELAY), options.get(CONF_CLOSE_DELAY, DEFAULT_CLOSE_DELAY)
            ),
        )

    @staticmethod
    def _clean_room(user_input: dict[str, Any], room_id: str) -> dict[str, Any]:
        return {
            CONF_ROOM_ID: room_id,
            CONF_ROOM_NAME: str(user_input[CONF_ROOM_NAME]).strip(),
            CONF_COVERS: list(user_input.get(CONF_COVERS) or []),
            CONF_CONTACTS: list(user_input.get(CONF_CONTACTS) or []),
            CONF_AREA: user_input.get(CONF_AREA) or None,
        }
