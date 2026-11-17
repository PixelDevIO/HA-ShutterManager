"""Behaviour tests for ShutterManager ventilation."""

from __future__ import annotations

from datetime import timedelta

from freezegun.api import FrozenDateTimeFactory
from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.util import dt as dt_util
import pytest
from pytest_homeassistant_custom_component.common import MockConfigEntry, async_fire_time_changed

from custom_components.shuttermanager.const import DOMAIN
from custom_components.shuttermanager.diagnostics import async_get_config_entry_diagnostics
from custom_components.shuttermanager.manager import ShutterManager

LEFT = "cover.bedroom_left"
RIGHT = "cover.bedroom_right"
WINDOW = "binary_sensor.bedroom_window"
DOOR = "binary_sensor.bedroom_door"
STATUS = "sensor.bedroom_status"
SWITCH = "switch.bedroom_ventilation"


def cover(hass: HomeAssistant, entity_id: str, position: int | None, state: str | None = None, features: int = 15):
    attrs = {"supported_features": features}
    if position is not None:
        attrs["current_position"] = position
    if state is None:
        state = "closed" if not position else "open"
    hass.states.async_set(entity_id, state, attrs)


class Covers:
    """Fake covers that follow the commands they get."""

    def __init__(self, hass: HomeAssistant) -> None:
        self.hass = hass
        self.calls: list[ServiceCall] = []
        for service in ("set_cover_position", "open_cover", "close_cover"):
            hass.services.async_register("cover", service, self._handle)

    def _handle(self, call: ServiceCall) -> None:
        self.calls.append(call)
        entity_id = call.data["entity_id"]
        st = self.hass.states.get(entity_id)
        features = st.attributes.get("supported_features", 15)
        if call.service == "set_cover_position":
            cover(self.hass, entity_id, call.data["position"], features=features)
        elif call.service == "open_cover":
            cover(self.hass, entity_id, 100 if "current_position" in st.attributes else None, "open", features)
        else:
            cover(self.hass, entity_id, 0 if "current_position" in st.attributes else None, "closed", features)

    def summary(self) -> list[tuple[str, str, int | None]]:
        return [(c.service, c.data["entity_id"], c.data.get("position")) for c in self.calls]


async def tick(hass: HomeAssistant, freezer: FrozenDateTimeFactory, seconds: float) -> None:
    freezer.tick(timedelta(seconds=seconds))
    async_fire_time_changed(hass)
    await hass.async_block_till_done()


async def set_contact(hass: HomeAssistant, entity_id: str, state: str) -> None:
    hass.states.async_set(entity_id, state, {"device_class": "window"})
    await hass.async_block_till_done()


@pytest.fixture
async def setup(hass: HomeAssistant, freezer: FrozenDateTimeFactory):
    """One room with two shutters (closed and half open) and two contacts."""
    freezer.move_to(dt_util.parse_datetime("2026-11-17T20:00:00+01:00"))
    cover(hass, LEFT, 0)
    cover(hass, RIGHT, 60)
    hass.states.async_set(WINDOW, "off", {"device_class": "window"})
    hass.states.async_set(DOOR, "off", {"device_class": "door"})
    covers = Covers(hass)
    entry = MockConfigEntry(
        domain=DOMAIN,
        unique_id=DOMAIN,
        options={
            "rooms": [
                {
                    "id": "r1",
                    "name": "Bedroom",
                    "covers": [LEFT, RIGHT],
                    "contacts": [WINDOW, DOOR],
                    "vent_positions": {LEFT: 30, RIGHT: 30},
                    "lockout": True,
                    "area": None,
                }
            ],
            "open_delay": 3,
            "close_delay": 5,
        },
    )
    entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    manager: ShutterManager = entry.runtime_data
    return manager, covers, entry


async def test_window_opens_and_closes(hass: HomeAssistant, freezer: FrozenDateTimeFactory, setup) -> None:
    manager, covers, _ = setup
    assert hass.states.get(STATUS).state == "idle"
    await set_contact(hass, WINDOW, "on")
    assert hass.states.get(STATUS).state == "waiting"
    assert covers.calls == []
    await tick(hass, freezer, 3)
    # only the closed shutter goes up, the half open one is already above 30 %
    assert covers.summary() == [("set_cover_position", LEFT, 30)]
    assert hass.states.get(STATUS).state == "venting"
    assert hass.states.get(STATUS).attributes["vented_covers"] == [LEFT]

    await set_contact(hass, WINDOW, "off")
    await tick(hass, freezer, 5)
    assert covers.summary()[-1] == ("set_cover_position", LEFT, 0)
    assert hass.states.get(LEFT).attributes["current_position"] == 0
    assert hass.states.get(STATUS).state == "idle"


async def test_short_opening_is_ignored(hass: HomeAssistant, freezer: FrozenDateTimeFactory, setup) -> None:
    _, covers, _ = setup
    await set_contact(hass, WINDOW, "on")
    await tick(hass, freezer, 1)
    await set_contact(hass, WINDOW, "off")
    await tick(hass, freezer, 10)
    assert covers.calls == []


async def test_restores_previous_partial_position(hass: HomeAssistant, freezer: FrozenDateTimeFactory, setup) -> None:
    _, covers, _ = setup
    cover(hass, LEFT, 10)
    await set_contact(hass, WINDOW, "on")
    await tick(hass, freezer, 3)
    await set_contact(hass, WINDOW, "off")
    await tick(hass, freezer, 5)
    assert covers.summary() == [("set_cover_position", LEFT, 30), ("set_cover_position", LEFT, 10)]


async def test_several_contacts(hass: HomeAssistant, freezer: FrozenDateTimeFactory, setup) -> None:
    _, covers, _ = setup
    await set_contact(hass, WINDOW, "on")
    await tick(hass, freezer, 3)
    await set_contact(hass, DOOR, "on")
    await set_contact(hass, WINDOW, "off")
    await tick(hass, freezer, 30)
    # the door is still open: stays up
    assert covers.summary() == [("set_cover_position", LEFT, 30)]
    await set_contact(hass, DOOR, "off")
    await tick(hass, freezer, 5)
    assert covers.summary()[-1] == ("set_cover_position", LEFT, 0)


async def test_manual_move_is_respected(hass: HomeAssistant, freezer: FrozenDateTimeFactory, setup) -> None:
    _, covers, _ = setup
    await set_contact(hass, WINDOW, "on")
    await tick(hass, freezer, 3)
    await tick(hass, freezer, 300)
    cover(hass, LEFT, 80)  # somebody opened it further by hand
    await set_contact(hass, WINDOW, "off")
    await tick(hass, freezer, 5)
    assert covers.summary() == [("set_cover_position", LEFT, 30)]
    assert hass.states.get(STATUS).state == "idle"


async def test_unavailable_contact_holds(hass: HomeAssistant, freezer: FrozenDateTimeFactory, setup) -> None:
    _, covers, _ = setup
    await set_contact(hass, WINDOW, "on")
    await tick(hass, freezer, 3)
    await set_contact(hass, WINDOW, "unavailable")
    await tick(hass, freezer, 60)
    # we cannot tell whether the window is closed: nothing moves
    assert covers.summary() == [("set_cover_position", LEFT, 30)]
    await set_contact(hass, WINDOW, "off")
    await tick(hass, freezer, 5)
    assert covers.summary()[-1] == ("set_cover_position", LEFT, 0)


async def test_unavailable_contact_does_not_open(hass: HomeAssistant, freezer: FrozenDateTimeFactory, setup) -> None:
    _, covers, _ = setup
    await set_contact(hass, WINDOW, "unavailable")
    await tick(hass, freezer, 10)
    assert covers.calls == []


async def test_unavailable_cover_catches_up(hass: HomeAssistant, freezer: FrozenDateTimeFactory, setup) -> None:
    _, covers, _ = setup
    hass.states.async_set(LEFT, "unavailable", {"supported_features": 15})
    await set_contact(hass, WINDOW, "on")
    await tick(hass, freezer, 3)
    assert covers.calls == []
    cover(hass, LEFT, 0)
    await hass.async_block_till_done()
    assert covers.summary() == [("set_cover_position", LEFT, 30)]

    # goes away again, window closes, comes back: goes down then
    hass.states.async_set(LEFT, "unavailable", {"supported_features": 15})
    await set_contact(hass, WINDOW, "off")
    await tick(hass, freezer, 5)
    assert len(covers.calls) == 1
    cover(hass, LEFT, 30)
    await hass.async_block_till_done()
    assert covers.summary()[-1] == ("set_cover_position", LEFT, 0)


async def test_reopen_while_going_down_keeps_original(
    hass: HomeAssistant, freezer: FrozenDateTimeFactory, setup
) -> None:
    _, covers, _ = setup
    await set_contact(hass, WINDOW, "on")
    await tick(hass, freezer, 3)
    await set_contact(hass, WINDOW, "off")
    await tick(hass, freezer, 5)
    cover(hass, LEFT, 15, "closing")  # still on its way down
    await set_contact(hass, WINDOW, "on")
    await tick(hass, freezer, 3)
    await set_contact(hass, WINDOW, "off")
    await tick(hass, freezer, 5)
    assert covers.summary()[-1] == ("set_cover_position", LEFT, 0)


async def test_window_closed_while_still_moving_up(hass: HomeAssistant, freezer: FrozenDateTimeFactory, setup) -> None:
    _, covers, _ = setup
    await set_contact(hass, WINDOW, "on")
    await tick(hass, freezer, 3)
    cover(hass, LEFT, 12, "opening")  # slow shutter, not there yet
    await set_contact(hass, WINDOW, "off")
    await tick(hass, freezer, 5)
    assert covers.summary()[-1] == ("set_cover_position", LEFT, 0)


async def test_cover_without_position(hass: HomeAssistant, freezer: FrozenDateTimeFactory, setup) -> None:
    _, covers, _ = setup
    cover(hass, LEFT, None, "closed", features=3)  # open/close only
    await set_contact(hass, WINDOW, "on")
    await tick(hass, freezer, 3)
    assert covers.summary() == [("open_cover", LEFT, None)]
    await set_contact(hass, WINDOW, "off")
    await tick(hass, freezer, 5)
    assert covers.summary()[-1] == ("close_cover", LEFT, None)


async def test_switch_off_leaves_everything(hass: HomeAssistant, freezer: FrozenDateTimeFactory, setup) -> None:
    manager, covers, _ = setup
    await set_contact(hass, WINDOW, "on")
    await tick(hass, freezer, 3)
    await hass.services.async_call("switch", "turn_off", {"entity_id": SWITCH}, blocking=True)
    assert hass.states.get(STATUS).state == "disabled"
    await set_contact(hass, WINDOW, "off")
    await tick(hass, freezer, 5)
    await set_contact(hass, WINDOW, "on")
    await tick(hass, freezer, 5)
    assert len(covers.calls) == 1
    await hass.services.async_call("switch", "turn_on", {"entity_id": SWITCH}, blocking=True)
    assert hass.states.get(STATUS).state == "idle"
    # the window was already open when switched on: nothing until it opens again
    await tick(hass, freezer, 5)
    assert len(covers.calls) == 1
    await set_contact(hass, WINDOW, "off")
    await set_contact(hass, WINDOW, "on")
    await tick(hass, freezer, 3)
    # LEFT stayed at 30 %, so it is not below its vent position
    assert len(covers.calls) == 1


async def test_restart_while_venting(hass: HomeAssistant, freezer: FrozenDateTimeFactory, setup) -> None:
    manager, covers, entry = setup
    await set_contact(hass, WINDOW, "on")
    await tick(hass, freezer, 3)
    await tick(hass, freezer, 2)  # let the store write
    assert await hass.config_entries.async_unload(entry.entry_id)
    await set_contact(hass, WINDOW, "off")  # closed while we were away
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    await tick(hass, freezer, 5)
    assert covers.summary()[-1] == ("set_cover_position", LEFT, 0)


async def test_open_window_at_start_moves_nothing(hass: HomeAssistant, freezer: FrozenDateTimeFactory, setup) -> None:
    manager, covers, entry = setup
    assert await hass.config_entries.async_unload(entry.entry_id)
    await set_contact(hass, WINDOW, "on")
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    await tick(hass, freezer, 10)
    assert covers.calls == []
    await set_contact(hass, WINDOW, "off")
    await tick(hass, freezer, 10)
    assert covers.calls == []


async def test_diagnostics(hass: HomeAssistant, freezer: FrozenDateTimeFactory, setup) -> None:
    _, _, entry = setup
    await set_contact(hass, WINDOW, "on")
    await tick(hass, freezer, 3)
    diag = await async_get_config_entry_diagnostics(hass, entry)
    assert diag["rooms"][0]["status"] == "venting"
    assert diag["rooms"][0]["vented"][LEFT]["previous"] == 0


async def test_lockout_keeps_shutter_up_and_closes_later(
    hass: HomeAssistant, freezer: FrozenDateTimeFactory, setup
) -> None:
    _, covers, _ = setup
    await set_contact(hass, DOOR, "on")
    await tick(hass, freezer, 3)
    assert covers.summary() == [("set_cover_position", LEFT, 30)]
    await tick(hass, freezer, 60)
    # an evening automation closes the right shutter while the door is open
    cover(hass, RIGHT, 40, "closing")
    await hass.async_block_till_done()
    assert covers.calls == [covers.calls[0]]  # still above 30 %
    cover(hass, RIGHT, 20, "closing")
    await hass.async_block_till_done()
    assert covers.summary()[-1] == ("set_cover_position", RIGHT, 30)
    # it keeps reporting the old movement for a moment: no second command
    cover(hass, RIGHT, 15, "closing")
    await hass.async_block_till_done()
    assert len(covers.calls) == 2
    assert sorted(hass.states.get(STATUS).attributes["vented_covers"]) == [LEFT, RIGHT]

    await set_contact(hass, DOOR, "off")
    await tick(hass, freezer, 5)
    # the automation wanted it closed: done now
    assert ("set_cover_position", RIGHT, 0) in covers.summary()
    assert ("set_cover_position", LEFT, 0) in covers.summary()


async def test_lockout_remembers_a_stopped_position(hass: HomeAssistant, freezer: FrozenDateTimeFactory, setup) -> None:
    _, covers, _ = setup
    await set_contact(hass, DOOR, "on")
    await tick(hass, freezer, 3)
    cover(hass, RIGHT, 10, "open")  # set to 10 % in one go
    await hass.async_block_till_done()
    assert covers.summary()[-1] == ("set_cover_position", RIGHT, 30)
    await set_contact(hass, DOOR, "off")
    await tick(hass, freezer, 5)
    assert ("set_cover_position", RIGHT, 10) in covers.summary()


async def test_lockout_acts_before_the_open_delay(hass: HomeAssistant, freezer: FrozenDateTimeFactory, setup) -> None:
    _, covers, _ = setup
    await set_contact(hass, DOOR, "on")
    cover(hass, RIGHT, 5, "closing")
    await hass.async_block_till_done()
    assert covers.summary() == [("set_cover_position", RIGHT, 30)]
    await set_contact(hass, DOOR, "off")
    await tick(hass, freezer, 5)
    assert covers.summary()[-1] == ("set_cover_position", RIGHT, 0)


async def test_no_lockout_when_window_closed(hass: HomeAssistant, freezer: FrozenDateTimeFactory, setup) -> None:
    _, covers, _ = setup
    cover(hass, RIGHT, 0, "closed")
    await hass.async_block_till_done()
    assert covers.calls == []


async def test_lockout_off(hass: HomeAssistant, freezer: FrozenDateTimeFactory, setup) -> None:
    manager, covers, _ = setup
    manager.rooms["r1"].lockout = False
    await set_contact(hass, DOOR, "on")
    await tick(hass, freezer, 3)
    cover(hass, RIGHT, 0, "closed")
    await hass.async_block_till_done()
    assert covers.summary() == [("set_cover_position", LEFT, 30)]
