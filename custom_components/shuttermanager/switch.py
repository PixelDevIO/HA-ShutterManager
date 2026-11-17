"""Ventilation on/off per room and the schedule pause."""

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
    entities: list[SwitchEntity] = [PauseSwitch(manager)]
    entities += [VentilationSwitch(manager, room) for room in manager.rooms.values()]
    async_add_entities(entities)


class PauseSwitch(ShutterManagerEntity, SwitchEntity):
    """On while the schedule is paused. Ventilation and lockout protection keep working."""

    _attr_translation_key = "pause"
    _attr_icon = "mdi:calendar-remove"

    def __init__(self, manager) -> None:
        super().__init__(manager, None, "pause")

    @property
    def is_on(self) -> bool:
        return self.manager.pause_active

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        until = self.manager.pause_until
        return {"until": until.isoformat() if until else None}

    async def async_turn_on(self, **kwargs: Any) -> None:
        self.manager.set_pause(True)

    async def async_turn_off(self, **kwargs: Any) -> None:
        self.manager.set_pause(False)


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
