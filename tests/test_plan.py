"""Week plans, vacation, pause and door contacts."""

from __future__ import annotations

from datetime import timedelta

from freezegun.api import FrozenDateTimeFactory
from homeassistant.core import HomeAssistant
from homeassistant.util import dt as dt_util
import pytest
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.shuttermanager.const import DOMAIN
from custom_components.shuttermanager.manager import ShutterManager

from .test_init import DOOR, LEFT, RIGHT, WINDOW, Covers, cover, set_contact, tick

ALL_DAYS = ("monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday")
DAY_PLAN = {d: [{"from": "08:00", "to": "20:00", "position": 100}] for d in ALL_DAYS}


async def make(hass: HomeAssistant, freezer: FrozenDateTimeFactory, **room) -> tuple[ShutterManager, Covers]:
    # 11:00 local time (the test instance runs on US/Pacific)
    freezer.move_to(dt_util.parse_datetime("2026-11-17T11:00:00-08:00"))
    cover(hass, LEFT, 0)
    cover(hass, RIGHT, 60)
    hass.states.async_set(WINDOW, "off", {"device_class": "window"})
    hass.states.async_set(DOOR, "off", {"device_class": "door"})
    covers = Covers(hass)
    base = {
        "id": "r1",
        "name": "Bedroom",
        "covers": [LEFT, RIGHT],
        "contacts": [WINDOW],
        "vent_positions": {LEFT: 30, RIGHT: 30},
        "lockout": True,
        "area": None,
    }
    entry = MockConfigEntry(
        domain=DOMAIN,
        unique_id=DOMAIN,
        options={"rooms": [{**base, **room}], "open_delay": 3, "close_delay": 5},
    )
    entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    return entry.runtime_data, covers


async def until(hass: HomeAssistant, freezer: FrozenDateTimeFactory, hhmm: str) -> None:
    now = dt_util.now()
    hour, minute = map(int, hhmm.split(":"))
    target = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
    if target <= now:
        target += timedelta(days=1)
    await tick(hass, freezer, (target - now).total_seconds() + 1)


async def test_plan_moves_shutters_at_its_changes(hass: HomeAssistant, freezer: FrozenDateTimeFactory) -> None:
    manager, covers = await make(hass, freezer)
    pid = manager.save_profile({"name": "Day", "base_position": 0, "week": DAY_PLAN})
    manager.set_assignment("r1", pid)
    # assigning a plan moves nothing until its next change
    await hass.async_block_till_done()
    assert covers.calls == []
    info = manager.room_info(manager.rooms["r1"])
    assert info["next_position"] == 0
    assert dt_util.parse_datetime(info["next_change"]).hour == 20

    await until(hass, freezer, "20:00")
    assert sorted(covers.summary()) == [("set_cover_position", LEFT, 0), ("set_cover_position", RIGHT, 0)]
    await until(hass, freezer, "08:00")
    assert sorted(covers.summary()[-2:]) == [("set_cover_position", LEFT, 100), ("set_cover_position", RIGHT, 100)]


async def test_plan_waits_for_closed_window(hass: HomeAssistant, freezer: FrozenDateTimeFactory) -> None:
    manager, covers = await make(hass, freezer)
    manager.set_assignment("r1", manager.save_profile({"name": "Day", "week": DAY_PLAN}))
    await set_contact(hass, WINDOW, "on")
    await tick(hass, freezer, 3)
    assert covers.summary() == [("set_cover_position", LEFT, 30)]

    await until(hass, freezer, "20:00")
    # window open: both shutters go only down to the vent position
    assert hass.states.get(LEFT).attributes["current_position"] == 30
    assert hass.states.get(RIGHT).attributes["current_position"] == 30

    await set_contact(hass, WINDOW, "off")
    await tick(hass, freezer, 5)
    assert hass.states.get(LEFT).attributes["current_position"] == 0
    assert hass.states.get(RIGHT).attributes["current_position"] == 0


async def test_pause_skips_changes(hass: HomeAssistant, freezer: FrozenDateTimeFactory) -> None:
    manager, covers = await make(hass, freezer)
    manager.set_assignment("r1", manager.save_profile({"name": "Day", "week": DAY_PLAN}))
    manager.set_pause(True, dt_util.now() + timedelta(hours=10))
    await until(hass, freezer, "20:00")
    assert covers.calls == []
    # the pause has ended by tomorrow morning
    await until(hass, freezer, "08:00")
    assert not manager.pause_active
    assert ("set_cover_position", RIGHT, 100) in covers.summary()


async def test_vacation_follows_vacation_plan(hass: HomeAssistant, freezer: FrozenDateTimeFactory) -> None:
    manager, covers = await make(hass, freezer)
    manager.set_assignment("r1", manager.save_profile({"name": "Day", "week": DAY_PLAN}))
    with pytest.raises(ValueError):
        manager.set_vacation(dt_util.now() + timedelta(days=3))
    evening = {d: [{"from": "10:00", "to": "18:00", "position": 50}] for d in ALL_DAYS}
    vac = manager.save_profile({"name": "Away", "vacation": True, "week": evening})
    manager.set_vacation(dt_util.now() + timedelta(days=3), random_minutes=0)
    room = manager.rooms["r1"]
    assert manager.active_profile(room)[0] == vac
    await until(hass, freezer, "18:00")
    assert sorted(covers.summary()) == [("set_cover_position", LEFT, 0), ("set_cover_position", RIGHT, 0)]
    manager.set_vacation(None)
    assert manager.active_profile(room)[0] != vac
    # only one vacation plan
    other = manager.save_profile({"name": "Away 2", "vacation": True})
    assert manager.vacation_profile == other
    assert manager.profiles[vac]["vacation"] is False


async def test_vacation_random_delay(hass: HomeAssistant, freezer: FrozenDateTimeFactory) -> None:
    manager, covers = await make(hass, freezer)
    manager.set_assignment("r1", manager.save_profile({"name": "Day", "week": DAY_PLAN}))
    manager.save_profile({"name": "Away", "vacation": True, "week": DAY_PLAN})
    manager.set_vacation(dt_util.now() + timedelta(days=3), random_minutes=30)
    await until(hass, freezer, "19:59")
    assert covers.calls == []
    await tick(hass, freezer, 31 * 60)
    assert len(covers.calls) == 2


async def test_apply_plan_now(hass: HomeAssistant, freezer: FrozenDateTimeFactory) -> None:
    manager, covers = await make(hass, freezer)
    with pytest.raises(ValueError):
        manager.apply_plan_now("r1")
    manager.set_assignment("r1", manager.save_profile({"name": "Day", "week": DAY_PLAN}))
    await hass.services.async_call(DOMAIN, "apply_plan", {"room": "bedroom"}, blocking=True)
    await hass.async_block_till_done()
    assert sorted(covers.summary()) == [("set_cover_position", LEFT, 100), ("set_cover_position", RIGHT, 100)]


async def test_deleting_a_plan_sets_rooms_manual(hass: HomeAssistant, freezer: FrozenDateTimeFactory) -> None:
    manager, _ = await make(hass, freezer)
    pid = manager.save_profile({"name": "Day", "week": DAY_PLAN})
    manager.set_assignment("r1", pid)
    manager.delete_profile(pid)
    assert manager.assignments["r1"] == "manual"
    assert manager.runtime["r1"].next_edge is None


async def test_door_keeps_door_shutter_up(hass: HomeAssistant, freezer: FrozenDateTimeFactory) -> None:
    manager, covers = await make(
        hass, freezer, lockout=False, door_contacts=[DOOR], door_covers=[RIGHT], door_position=100
    )
    room = manager.rooms["r1"]
    assert room.contacts == [WINDOW, DOOR]
    await set_contact(hass, DOOR, "on")
    await tick(hass, freezer, 3)
    assert sorted(covers.summary()) == [("set_cover_position", LEFT, 30), ("set_cover_position", RIGHT, 100)]

    # without "keep vent position" the window shutter may go down, the door shutter not
    await tick(hass, freezer, 15)
    await hass.services.async_call("cover", "close_cover", {"entity_id": LEFT}, blocking=True)
    await hass.services.async_call("cover", "close_cover", {"entity_id": RIGHT}, blocking=True)
    await hass.async_block_till_done()
    assert hass.states.get(LEFT).attributes["current_position"] == 0
    assert hass.states.get(RIGHT).attributes["current_position"] == 100

    await set_contact(hass, DOOR, "off")
    await tick(hass, freezer, 5)
    # what was asked while the door was open happens now
    assert hass.states.get(RIGHT).attributes["current_position"] == 0


async def test_door_opened_after_window_raises_further(hass: HomeAssistant, freezer: FrozenDateTimeFactory) -> None:
    manager, covers = await make(hass, freezer, door_contacts=[DOOR], door_covers=[], door_position=80)
    cover(hass, RIGHT, 0)
    await set_contact(hass, WINDOW, "on")
    await tick(hass, freezer, 3)
    assert hass.states.get(RIGHT).attributes["current_position"] == 30
    await set_contact(hass, DOOR, "on")
    # no door covers chosen: all shutters of the room are door shutters
    assert hass.states.get(LEFT).attributes["current_position"] == 80
    assert hass.states.get(RIGHT).attributes["current_position"] == 80
    await set_contact(hass, DOOR, "off")
    await set_contact(hass, WINDOW, "off")
    await tick(hass, freezer, 5)
    assert hass.states.get(LEFT).attributes["current_position"] == 0
    assert hass.states.get(RIGHT).attributes["current_position"] == 0
