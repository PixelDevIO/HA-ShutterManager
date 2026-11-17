"""Diagnostics for bug reports (Settings › Devices & services › ShutterManager › ⋮ › Download diagnostics)."""

from __future__ import annotations

from typing import Any

from homeassistant.core import HomeAssistant

from . import ShutterManagerConfigEntry
from .const import VERSION

COVER_ATTRS = ("current_position", "supported_features", "device_class")


async def async_get_config_entry_diagnostics(hass: HomeAssistant, entry: ShutterManagerConfigEntry) -> dict[str, Any]:
    manager = entry.runtime_data

    def _state(entity_id: str) -> dict[str, Any] | None:
        st = hass.states.get(entity_id)
        if st is None:
            return None
        return {
            "state": st.state,
            "attributes": {k: st.attributes[k] for k in COVER_ATTRS if k in st.attributes},
            "last_changed": st.last_changed.isoformat(),
        }

    rooms = []
    for room in manager.rooms.values():
        rt = manager.runtime[room.id]
        rooms.append(
            {
                **manager.room_info(room),
                "status": manager.status(room),
                "enabled": rt.enabled,
                "cover_states": {c: _state(c) for c in room.covers},
                "contact_states": {c: _state(c) for c in room.contacts},
            }
        )
    return {"version": VERSION, "options": dict(entry.options), "rooms": rooms}
