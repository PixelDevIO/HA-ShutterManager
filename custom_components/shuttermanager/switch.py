"""Ventilation on/off per room."""

from __future__ import annotations

from typing import Any

from homeassistant.components.switch import SwitchEntity
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from . import ShutterManagerConfigEntry
from .entity import ShutterManagerEntity


async def async_setup_entry(
    hass: HomeAssistant, entry: ShutterManagerConfigEntry, async_add_entities: AddConfigEntryEntitiesCallback
) -> None:
    manager = entry.runtime_data
    async_add_entities(VentilationSwitch(manager, room) for room in manager.rooms.values())


class VentilationSwitch(ShutterManagerEntity, SwitchEntity):
    """Off: the room's shutters are never moved for ventilation."""

    _attr_translation_key = "ventilation"
    _attr_icon = "mdi:window-shutter-cog"

    def __init__(self, manager, room) -> None:
        super().__init__(manager, room, "ventilation")

    @property
    def is_on(self) -> bool:
        return self.manager.runtime[self.room.id].enabled

    async def async_turn_on(self, **kwargs: Any) -> None:
        self.manager.set_enabled(self.room.id, True)

    async def async_turn_off(self, **kwargs: Any) -> None:
        self.manager.set_enabled(self.room.id, False)
