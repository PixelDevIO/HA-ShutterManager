"""Schedule profile per room."""

from __future__ import annotations

from homeassistant.components.select import SelectEntity
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ServiceValidationError
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from . import ShutterManagerConfigEntry
from .const import ASSIGN_MANUAL
from .entity import ShutterManagerEntity

LABELS = {"de": {ASSIGN_MANUAL: "Manuell"}, "en": {ASSIGN_MANUAL: "Manual"}}


async def async_setup_entry(
    hass: HomeAssistant, entry: ShutterManagerConfigEntry, async_add_entities: AddConfigEntryEntitiesCallback
) -> None:
    manager = entry.runtime_data
    async_add_entities(RoomProfileSelect(manager, room) for room in manager.rooms.values())


class RoomProfileSelect(ShutterManagerEntity, SelectEntity):
    """Choose which weekly plan moves a room's shutters (Manual: none)."""

    _attr_translation_key = "profile"
    _attr_icon = "mdi:calendar-clock"

    def __init__(self, manager, room) -> None:
        super().__init__(manager, room, "profile")

    def _choices(self) -> dict[str, str]:
        """Map option label -> assignment value."""
        lang = (self.hass.config.language or "en").split("-")[0]
        labels = LABELS.get(lang, LABELS["en"])
        choices = {p["name"]: pid for pid, p in self.manager.profiles.items() if not p.get("vacation")}
        choices[labels[ASSIGN_MANUAL]] = ASSIGN_MANUAL
        return choices

    @property
    def options(self) -> list[str]:
        return list(self._choices())

    @property
    def current_option(self) -> str | None:
        value = self.manager.assignments.get(self.room.id, ASSIGN_MANUAL)
        for label, assigned in self._choices().items():
            if assigned == value:
                return label
        return None

    async def async_select_option(self, option: str) -> None:
        value = self._choices().get(option)
        if value is None:
            raise ServiceValidationError(f"Unknown profile {option}")
        self.manager.set_assignment(self.room.id, value)
