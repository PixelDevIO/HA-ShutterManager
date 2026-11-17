"""Pure schedule logic."""

from __future__ import annotations

from datetime import date, datetime

import pytest

from custom_components.shuttermanager.schedule import day_plan, next_edge, normalize_week, position_at, resolve_edge

MONDAY = date(2026, 11, 16)
SUN = {"sunrise": 7 * 60 + 40, "sunset": 16 * 60 + 37}


def sun_for(_day: date) -> dict[str, int | None]:
    return SUN


def profile(blocks, base=0):
    return {"base_position": base, "week": normalize_week({"monday": blocks, "tuesday": blocks})}


def test_normalize_rejects_overlap_and_bad_values() -> None:
    with pytest.raises(ValueError):
        normalize_week(
            {
                "monday": [
                    {"from": "08:00", "to": "10:00", "position": 50},
                    {"from": "09:00", "to": "11:00", "position": 0},
                ]
            }
        )
    with pytest.raises(ValueError):
        normalize_week({"monday": [{"from": "08:00", "to": "07:00", "position": 50}]})
    with pytest.raises(ValueError):
        normalize_week({"monday": [{"from": "08:00", "to": "09:00", "position": 101}]})
    with pytest.raises(ValueError):
        normalize_week({"funday": []})
    with pytest.raises(ValueError):
        normalize_week({"monday": [{"from": "08:00", "to": "09:00", "position": 1, "from_sun": "noon"}]})
    with pytest.raises(ValueError):
        normalize_week(
            {"monday": [{"from": "08:00", "to": "09:00", "position": 1, "from_sun": "sunrise", "from_offset": 300}]}
        )


def test_sun_edges_with_offset_and_bounds() -> None:
    week = normalize_week(
        {
            "monday": [
                {
                    "from": "07:00",
                    "to": "00:00",
                    "position": 100,
                    "from_sun": "sunrise",
                    "from_offset": -10,
                    "from_min": "06:30",
                    "to_sun": "sunset",
                    "to_offset": 30,
                    "to_max": "17:00",
                }
            ]
        }
    )
    block = week["monday"][0]
    assert block["to"] == "24:00"
    assert resolve_edge(block, "from", SUN) == 7 * 60 + 30
    # sunset + 30 is 17:07, the latest allowed is 17:00
    assert resolve_edge(block, "to", SUN) == 17 * 60
    # earliest wins when the sun is up early
    assert resolve_edge(block, "from", {"sunrise": 5 * 60, "sunset": 21 * 60}) == 6 * 60 + 30
    # polar night: the shown time is used
    assert resolve_edge(block, "from", {"sunrise": None, "sunset": None}) == 7 * 60


def test_day_plan_fills_gaps_with_base() -> None:
    p = profile([{"from": "08:00", "to": "12:00", "position": 50}], base=10)
    assert day_plan(p, MONDAY, SUN) == [(0, 480, 10), (480, 720, 50), (720, 1440, 10)]
    assert position_at(p, datetime(2026, 11, 16, 9, 0), sun_for) == 50
    assert position_at(p, datetime(2026, 11, 16, 13, 0), sun_for) == 10


def test_next_edge_skips_equal_positions_and_days() -> None:
    p = profile(
        [
            {"from": "08:00", "to": "12:00", "position": 100},
            {"from": "12:00", "to": "18:00", "position": 100},
        ]
    )
    assert next_edge(p, datetime(2026, 11, 16, 9, 0), sun_for) == (datetime(2026, 11, 16, 18, 0), 0)
    # after Tuesday's evening the next change is next Monday morning
    assert next_edge(p, datetime(2026, 11, 17, 19, 0), sun_for) == (datetime(2026, 11, 23, 8, 0), 100)
    assert next_edge({"base_position": 0, "week": normalize_week({})}, datetime(2026, 11, 16, 9, 0), sun_for) is None
