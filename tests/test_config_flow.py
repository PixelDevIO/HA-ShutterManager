"""Config and options flow."""

from __future__ import annotations

from homeassistant import config_entries
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.shuttermanager.const import DOMAIN


async def test_setup_and_add_room(hass: HomeAssistant) -> None:
    hass.states.async_set("cover.a", "closed", {"current_position": 0, "supported_features": 15})
    hass.states.async_set("cover.b", "closed", {"current_position": 0, "supported_features": 15})
    hass.states.async_set("binary_sensor.w", "off")
    result = await hass.config_entries.flow.async_init(DOMAIN, context={"source": config_entries.SOURCE_USER})
    result = await hass.config_entries.flow.async_configure(result["flow_id"], {"open_delay": 3, "close_delay": 5})
    assert result["type"] is FlowResultType.CREATE_ENTRY
    entry = hass.config_entries.async_entries(DOMAIN)[0]

    result = await hass.config_entries.options.async_init(entry.entry_id)
    result = await hass.config_entries.options.async_configure(result["flow_id"], {"next_step_id": "add_room"})
    result = await hass.config_entries.options.async_configure(
        result["flow_id"], {"name": "Office", "covers": ["cover.a", "cover.b"], "contacts": ["binary_sensor.w"]}
    )
    assert result["step_id"] == "room_positions"
    result = await hass.config_entries.options.async_configure(result["flow_id"], {"position_1": 25, "position_2": 40})
    assert result["type"] is FlowResultType.CREATE_ENTRY
    room = entry.options["rooms"][0]
    assert room["vent_positions"] == {"cover.a": 25, "cover.b": 40}
    assert room["lockout"] is True
    await hass.async_block_till_done()
    assert hass.states.get("switch.office_ventilation").state == "on"


async def test_cover_only_in_one_room(hass: HomeAssistant) -> None:
    entry = MockConfigEntry(
        domain=DOMAIN,
        unique_id=DOMAIN,
        options={
            "rooms": [
                {"id": "r1", "name": "A", "covers": ["cover.a"], "contacts": ["binary_sensor.w"], "vent_positions": {}}
            ],
            "open_delay": 3,
            "close_delay": 5,
        },
    )
    entry.add_to_hass(hass)
    result = await hass.config_entries.options.async_init(entry.entry_id)
    result = await hass.config_entries.options.async_configure(result["flow_id"], {"next_step_id": "add_room"})
    result = await hass.config_entries.options.async_configure(
        result["flow_id"], {"name": "B", "covers": ["cover.a"], "contacts": ["binary_sensor.w"]}
    )
    assert result["errors"] == {"covers": "cover_in_use"}


async def test_room_with_door(hass: HomeAssistant) -> None:
    hass.states.async_set("cover.a", "closed", {"current_position": 0, "supported_features": 15})
    hass.states.async_set("cover.door", "closed", {"current_position": 0, "supported_features": 15})
    entry = MockConfigEntry(domain=DOMAIN, unique_id=DOMAIN, options={"rooms": [], "open_delay": 3, "close_delay": 5})
    entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(entry.entry_id)
    result = await hass.config_entries.options.async_init(entry.entry_id)
    result = await hass.config_entries.options.async_configure(result["flow_id"], {"next_step_id": "add_room"})
    result = await hass.config_entries.options.async_configure(
        result["flow_id"], {"name": "Living", "covers": ["cover.a", "cover.door"]}
    )
    assert result["errors"] == {"contacts": "no_contact"}
    result = await hass.config_entries.options.async_configure(
        result["flow_id"],
        {
            "name": "Living",
            "covers": ["cover.a", "cover.door"],
            "contacts": ["binary_sensor.w"],
            "door_contacts": ["binary_sensor.w"],
        },
    )
    assert result["errors"] == {"door_contacts": "contact_twice"}
    result = await hass.config_entries.options.async_configure(
        result["flow_id"],
        {"name": "Living", "covers": ["cover.a", "cover.door"], "door_contacts": ["binary_sensor.d"]},
    )
    assert result["step_id"] == "room_positions"
    assert "door_position" in result["data_schema"].schema
    result = await hass.config_entries.options.async_configure(
        result["flow_id"],
        {"position_1": 30, "position_2": 30, "door_position": 90, "door_covers": ["cover.door"]},
    )
    assert result["type"] is FlowResultType.CREATE_ENTRY
    room = entry.options["rooms"][0]
    assert room["contacts"] == []
    assert room["door_contacts"] == ["binary_sensor.d"]
    assert room["door_covers"] == ["cover.door"]
    assert room["door_position"] == 90
    await hass.async_block_till_done()
    manager = entry.runtime_data
    assert manager.rooms[room["id"]].contacts == ["binary_sensor.d"]
    assert hass.states.get("switch.shuttermanager_schedule_paused") is not None
    assert hass.states.get("select.living_plan").state == "Manual"
