"""What ShutterManager is doing in a room."""

from __future__ import annotations

from typing import Any

from homeassistant.components.sensor import SensorDeviceClass, SensorEntity
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from . import ShutterManagerConfigEntry
from .const import STATUSES
from .entity import ShutterManagerEntity


async def async_setup_entry(
    hass: HomeAssistant, entry: ShutterManagerConfigEntry, async_add_entities: AddConfigEntryEntitiesCallback
) -> None:
    manager = entry.runtime_data
    async_add_entities(RoomStatusSensor(manager, room) for room in manager.rooms.values())


class RoomStatusSensor(ShutterManagerEntity, SensorEntity):
    """idle, waiting (delay running), venting or disabled."""

    _attr_translation_key = "status"
    _attr_device_class = SensorDeviceClass.ENUM
    _attr_options = list(STATUSES)
    _attr_icon = "mdi:window-shutter-open"

    def __init__(self, manager, room) -> None:
        super().__init__(manager, room, "status")

    @property
    def native_value(self) -> str:
        return self.manager.status(self.room)

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        info = self.manager.room_info(self.room)
        return {
            "window_open": info["window_open"],
            "open_contacts": info["open_contacts"],
            "vented_covers": sorted(info["vented"]),
            "vent_positions": info["vent_positions"],
        }
