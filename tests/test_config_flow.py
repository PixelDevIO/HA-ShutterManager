"""Config and options flow."""

from __future__ import annotations

from homeassistant import config_entries
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.shuttermanager.const import DOMAIN
from custom_components.shuttermanager.manager import cover_settings


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
    assert result["step_id"] == "room_covers"
    result = await hass.config_entries.options.async_configure(
        result["flow_id"],
        {"contact_1": "any", "kind_1": "window", "position_1": 25, "contact_2": "any", "kind_2": "window"},
    )
    assert result["type"] is FlowResultType.CREATE_ENTRY
    room = entry.options["rooms"][0]
    assert room["cover_settings"] == {
        "cover.a": {"contact": None, "kind": "window", "position": 25},
        "cover.b": {"contact": None, "kind": "window", "position": 30},
    }
    assert "lockout" not in room
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
        result["flow_id"], {"name": "Living", "covers": ["cover.a", "cover.door"], "contacts": []}
    )
    assert result["errors"] == {"contacts": "no_contact"}
    result = await hass.config_entries.options.async_configure(
        result["flow_id"],
        {"name": "Living", "covers": ["cover.a", "cover.door"], "contacts": ["binary_sensor.w", "binary_sensor.d"]},
    )
    assert result["step_id"] == "room_covers"
    result = await hass.config_entries.options.async_configure(
        result["flow_id"],
        {
            "contact_1": "binary_sensor.w",
            "kind_1": "window",
            "contact_2": "binary_sensor.d",
            "kind_2": "door",
        },
    )
    assert result["type"] is FlowResultType.CREATE_ENTRY
    room = entry.options["rooms"][0]
    assert room["contacts"] == ["binary_sensor.w", "binary_sensor.d"]
    assert room["cover_settings"] == {
        "cover.a": {"contact": "binary_sensor.w", "kind": "window", "position": 30},
        "cover.door": {"contact": "binary_sensor.d", "kind": "door", "position": 100},
    }
    await hass.async_block_till_done()
    manager = entry.runtime_data
    assert manager.rooms[room["id"]].contacts_of("cover.door") == ["binary_sensor.d"]

    # editing shows the stored settings again
    result = await hass.config_entries.options.async_init(entry.entry_id)
    result = await hass.config_entries.options.async_configure(result["flow_id"], {"next_step_id": "edit_room"})
    result = await hass.config_entries.options.async_configure(result["flow_id"], {"room": room["id"]})
    result = await hass.config_entries.options.async_configure(
        result["flow_id"],
        {"name": "Living", "covers": ["cover.a", "cover.door"], "contacts": ["binary_sensor.w", "binary_sensor.d"]},
    )
    assert result["step_id"] == "room_covers"
    defaults = {str(k): k.default() for k in result["data_schema"].schema if callable(k.default)}
    assert defaults["contact_2"] == "binary_sensor.d"
    assert defaults["kind_2"] == "door"


def test_migrates_rooms_from_0_3_0() -> None:
    raw = {
        "covers": ["cover.a", "cover.door"],
        "contacts": ["binary_sensor.w"],
        "door_contacts": ["binary_sensor.d"],
        "door_covers": ["cover.door"],
        "door_position": 90,
        "vent_positions": {"cover.a": 20},
        "lockout": False,
    }
    settings = cover_settings(raw)
    assert settings["cover.a"].as_dict() == {"contact": None, "kind": "window", "position": 20}
    assert settings["cover.door"].as_dict() == {"contact": "binary_sensor.d", "kind": "door", "position": 90}
    plain = cover_settings({"covers": ["cover.a"], "contacts": ["binary_sensor.w"]})
    assert plain["cover.a"].as_dict() == {"contact": None, "kind": "window", "position": 30}
