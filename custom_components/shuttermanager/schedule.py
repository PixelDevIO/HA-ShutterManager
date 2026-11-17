"""Pure weekly-schedule logic for shutters (no Home Assistant imports, easy to test).

A profile has a base position (used outside the blocks) and, per weekday, blocks
with a position. Each block edge is either a fixed time or tied to sunrise or
sunset with an offset, optionally kept between an earliest and a latest time.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from datetime import date, datetime, time, timedelta
import re
from typing import Any

DAYS = ("monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday")
SUN_EVENTS = ("sunrise", "sunset")
MINUTES_PER_DAY = 1440
_TIME_RE = re.compile(r"^(\d{1,2}):(\d{2})(?::(\d{2}))?$")

# sunrise and sunset of a date in minutes after midnight (None in polar day/night)
SunTimes = dict[str, int | None]
SunLookup = Callable[[date], SunTimes]


def parse_time(value: str) -> int:
    """Parse 'HH:MM' (or 'HH:MM:SS', '24:00') into minutes after midnight."""
    match = _TIME_RE.match(str(value).strip())
    if not match:
        raise ValueError(f"Invalid time: {value!r}")
    hours, minutes = int(match.group(1)), int(match.group(2))
    total = hours * 60 + minutes
    if minutes > 59 or total > MINUTES_PER_DAY:
        raise ValueError(f"Invalid time: {value!r}")
    return total


def format_time(minutes: int) -> str:
    return f"{minutes // 60:02d}:{minutes % 60:02d}"


def _position(value: Any) -> int:
    pos = int(round(float(value)))
    if not 0 <= pos <= 100:
        raise ValueError(f"position {value} out of range")
    return pos


def _edge(raw: dict[str, Any], side: str) -> dict[str, Any]:
    """Validate one block edge ('from' or 'to') and return its canonical keys."""
    minute = parse_time(raw[side])
    if side == "to" and minute == 0:
        minute = MINUTES_PER_DAY
    out: dict[str, Any] = {side: format_time(minute)}
    sun = raw.get(f"{side}_sun")
    if sun:
        if sun not in SUN_EVENTS:
            raise ValueError(f"unknown sun event {sun!r}")
        offset = int(raw.get(f"{side}_offset") or 0)
        if not -240 <= offset <= 240:
            raise ValueError("sun offset must be within ±240 minutes")
        out[f"{side}_sun"] = sun
        out[f"{side}_offset"] = offset
        for bound in ("min", "max"):
            value = raw.get(f"{side}_{bound}")
            out[f"{side}_{bound}"] = format_time(parse_time(value)) if value else None
        if (
            out[f"{side}_min"]
            and out[f"{side}_max"]
            and parse_time(out[f"{side}_min"]) > parse_time(out[f"{side}_max"])
        ):
            raise ValueError("earliest is after latest")
    return out


def normalize_week(week: dict[str, Any] | None) -> dict[str, list[dict[str, Any]]]:
    """Validate a week and return it in canonical form.

    Per day a list of {"from", "to", "position"} plus optional sun keys per edge
    ("from_sun": "sunrise"/"sunset", "from_offset", "from_min", "from_max", same for "to").
    "from"/"to" are the times shown in the grid and used for fixed edges; they must not overlap.
    """
    week = week or {}
    unknown = set(week) - set(DAYS)
    if unknown:
        raise ValueError(f"Unknown day(s): {', '.join(sorted(unknown))}")
    result: dict[str, list[dict[str, Any]]] = {}
    for day in DAYS:
        blocks = []
        for raw in week.get(day) or []:
            block = {**_edge(raw, "from"), **_edge(raw, "to"), "position": _position(raw["position"])}
            if parse_time(block["to"]) <= parse_time(block["from"]):
                raise ValueError(f"{day}: block {block['from']}-{block['to']} is empty or reversed")
            blocks.append(block)
        blocks.sort(key=lambda b: parse_time(b["from"]))
        for prev, nxt in zip(blocks, blocks[1:], strict=False):
            if parse_time(nxt["from"]) < parse_time(prev["to"]):
                raise ValueError(f"{day}: blocks {prev['from']} and {nxt['from']} overlap")
        result[day] = blocks
    return result


def resolve_edge(block: dict[str, Any], side: str, sun: SunTimes) -> int:
    """Minute of the day an edge falls on, given that day's sun times."""
    fixed = parse_time(block[side]) or (MINUTES_PER_DAY if side == "to" else 0)
    event = block.get(f"{side}_sun")
    if not event or sun.get(event) is None:
        return fixed
    minute = int(sun[event]) + int(block.get(f"{side}_offset") or 0)
    if block.get(f"{side}_min"):
        minute = max(minute, parse_time(block[f"{side}_min"]))
    if block.get(f"{side}_max"):
        minute = min(minute, parse_time(block[f"{side}_max"]))
    return max(0, min(MINUTES_PER_DAY, minute))


@dataclass(frozen=True)
class Segment:
    start: int
    end: int
    position: int


def day_segments(profile: dict[str, Any], day: date, sun: SunTimes) -> list[Segment]:
    """The blocks of a date with sun edges resolved; overlaps cut, empty blocks dropped."""
    out: list[Segment] = []
    for block in profile.get("week", {}).get(DAYS[day.weekday()], []):
        start, end = resolve_edge(block, "from", sun), resolve_edge(block, "to", sun)
        if out and start < out[-1].end:
            start = out[-1].end
        if end > start:
            out.append(Segment(start, end, int(block["position"])))
    return out


def base_position(profile: dict[str, Any]) -> int:
    return int(profile.get("base_position", 0))


def position_at(profile: dict[str, Any], moment: datetime, sun_for: SunLookup) -> int:
    minute = moment.hour * 60 + moment.minute
    for seg in day_segments(profile, moment.date(), sun_for(moment.date())):
        if seg.start <= minute < seg.end:
            return seg.position
    return base_position(profile)


def day_plan(profile: dict[str, Any], day: date, sun: SunTimes) -> list[tuple[int, int, int]]:
    """The whole day as (from, to, position), base position filling the gaps."""
    base, out, cursor = base_position(profile), [], 0
    for seg in day_segments(profile, day, sun):
        if seg.start > cursor:
            out.append((cursor, seg.start, base))
        out.append((seg.start, seg.end, seg.position))
        cursor = seg.end
    if cursor < MINUTES_PER_DAY:
        out.append((cursor, MINUTES_PER_DAY, base))
    return out


def next_edge(profile: dict[str, Any], moment: datetime, sun_for: SunLookup) -> tuple[datetime, int] | None:
    """The next moment the profile's position changes, and the position from then on."""
    current = position_at(profile, moment, sun_for)
    midnight = datetime.combine(moment.date(), time(0), tzinfo=moment.tzinfo)
    for offset in range(8):
        day_start = midnight + timedelta(days=offset)
        for start, _end, position in day_plan(profile, day_start.date(), sun_for(day_start.date())):
            when = day_start + timedelta(minutes=start)
            if when <= moment:
                continue
            if position != current:
                return when, position
    return None
