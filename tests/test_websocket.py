"""WebSocket API of the card."""

from __future__ import annotations

from homeassistant.core import HomeAssistant
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.shuttermanager.const import DOMAIN


async def result(client) -> dict:
    """The next command result; state pushes of the subscription are skipped."""
    while (msg := await client.receive_json())["type"] != "result":
        pass
    return msg


async def test_profiles_over_websocket(hass: HomeAssistant, hass_ws_client) -> None:
    hass.states.async_set("cover.a", "closed", {"current_position": 0, "supported_features": 15})
    entry = MockConfigEntry(
        domain=DOMAIN,
        unique_id=DOMAIN,
        options={
            "rooms": [{"id": "r1", "name": "A", "covers": ["cover.a"], "contacts": ["binary_sensor.w"]}],
            "open_delay": 3,
            "close_delay": 5,
        },
    )
    entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    client = await hass_ws_client(hass)

    await client.send_json_auto_id({"type": "shuttermanager/subscribe"})
    first = await client.receive_json()
    assert first["success"], first
    state = (await client.receive_json())["event"]
    assert state["rooms"][0]["profile"] == "manual"
    assert set(state["sun"]) == {"monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"}

    week = {
        "monday": [
            {
                "from": "07:30",
                "to": "18:00",
                "position": 100,
                "from_sun": "sunrise",
                "from_offset": 10,
                "from_min": "06:30",
            }
        ]
    }
    await client.send_json_auto_id(
        {"type": "shuttermanager/profile/save", "name": "Work", "base_position": 0, "week": week}
    )
    msg = await result(client)
    assert msg["success"], msg
    pid = msg["result"]["profile_id"]
    saved = hass.data[DOMAIN][entry.entry_id].profiles[pid]["week"]["monday"][0]
    assert saved["from_sun"] == "sunrise" and saved["from_offset"] == 10 and saved["from_min"] == "06:30"

    await client.send_json_auto_id({"type": "shuttermanager/room/set_profile", "room_id": "r1", "profile": pid})
    assert (await result(client))["success"]

    await client.send_json_auto_id({"type": "shuttermanager/vacation", "until": "2099-01-01T10:00:00"})
    msg = await result(client)
    assert not msg["success"] and msg["error"]["message"] == "no vacation plan"

    await client.send_json_auto_id({"type": "shuttermanager/pause", "hours": 2})
    assert (await result(client))["success"]
    assert hass.states.get("switch.shuttermanager_schedule_paused").state == "on"
    await client.send_json_auto_id({"type": "shuttermanager/resume"})
    assert (await result(client))["success"]

    await client.send_json_auto_id({"type": "shuttermanager/profile/delete", "profile_id": pid})
    assert (await result(client))["success"]
