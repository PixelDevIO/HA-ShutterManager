"""WebSocket API used by the ShutterManager card."""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any

from homeassistant.components import websocket_api
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.dispatcher import async_dispatcher_connect
from homeassistant.util import dt as dt_util
import voluptuous as vol

from .const import SIGNAL_UPDATE
from .manager import ShutterManager, get_manager

_EDGE_KEYS = {
    vol.Optional(f"{side}_{key}"): vol.Any(None, str, int)
    for side in ("from", "to")
    for key in ("sun", "offset", "min", "max")
}
_BLOCK = vol.Schema(
    {vol.Required("from"): str, vol.Required("to"): str, vol.Required("position"): vol.Coerce(float), **_EDGE_KEYS}
)


@callback
def async_register_websocket(hass: HomeAssistant) -> None:
    """Register all commands."""
    for handler in (
        ws_subscribe,
        ws_save_profile,
        ws_delete_profile,
        ws_set_room_profile,
        ws_room_apply,
        ws_pause,
        ws_resume,
        ws_vacation,
    ):
        websocket_api.async_register_command(hass, handler)


def _manager_or_error(
    hass: HomeAssistant, connection: websocket_api.ActiveConnection, msg_id: int
) -> ShutterManager | None:
    try:
        return get_manager(hass)
    except LookupError:
        connection.send_error(msg_id, "not_loaded", "ShutterManager is not set up")
        return None


def parse_moment(value: str) -> datetime | None:
    """A local datetime from an ISO string; naive values count as local time."""
    parsed = dt_util.parse_datetime(value)
    if parsed is None:
        return None
    return dt_util.as_local(parsed if parsed.tzinfo else parsed.replace(tzinfo=dt_util.get_default_time_zone()))


@websocket_api.websocket_command({vol.Required("type"): "shuttermanager/subscribe"})
@callback
def ws_subscribe(hass: HomeAssistant, connection: websocket_api.ActiveConnection, msg: dict[str, Any]) -> None:
    """Send the full state now and after every change."""
    manager = _manager_or_error(hass, connection, msg["id"])
    if manager is None:
        return

    @callback
    def _push() -> None:
        connection.send_message(websocket_api.event_message(msg["id"], manager.as_dict()))

    unsub = async_dispatcher_connect(hass, f"{SIGNAL_UPDATE}_{manager.entry.entry_id}", _push)
    connection.subscriptions[msg["id"]] = unsub
    connection.send_result(msg["id"])
    _push()


@websocket_api.require_admin
@websocket_api.websocket_command(
    {
        vol.Required("type"): "shuttermanager/profile/save",
        vol.Optional("profile_id"): str,
        vol.Required("name"): str,
        vol.Optional("icon"): str,
        vol.Optional("color"): vol.Any(None, str),
        vol.Optional("base_position"): vol.Coerce(float),
        vol.Optional("vacation"): bool,
        vol.Optional("week"): {str: [_BLOCK]},
    }
)
@callback
def ws_save_profile(hass: HomeAssistant, connection: websocket_api.ActiveConnection, msg: dict[str, Any]) -> None:
    """Create or update a profile."""
    manager = _manager_or_error(hass, connection, msg["id"])
    if manager is None:
        return
    data = {k: msg[k] for k in ("name", "icon", "color", "base_position", "vacation", "week") if k in msg}
    existing = manager.profiles.get(msg.get("profile_id", ""))
    if existing:
        data = {**existing, **data}
    try:
        profile_id = manager.save_profile(data, msg.get("profile_id"))
    except KeyError:
        connection.send_error(msg["id"], "not_found", "Unknown profile")
        return
    except (TypeError, ValueError) as err:
        connection.send_error(msg["id"], "invalid_format", str(err))
        return
    connection.send_result(msg["id"], {"profile_id": profile_id})


@websocket_api.require_admin
@websocket_api.websocket_command(
    {vol.Required("type"): "shuttermanager/profile/delete", vol.Required("profile_id"): str}
)
@callback
def ws_delete_profile(hass: HomeAssistant, connection: websocket_api.ActiveConnection, msg: dict[str, Any]) -> None:
    """Delete a profile."""
    manager = _manager_or_error(hass, connection, msg["id"])
    if manager is None:
        return
    try:
        manager.delete_profile(msg["profile_id"])
    except KeyError:
        connection.send_error(msg["id"], "not_found", "Unknown profile")
        return
    connection.send_result(msg["id"])


@websocket_api.websocket_command(
    {
        vol.Required("type"): "shuttermanager/room/set_profile",
        vol.Required("room_id"): str,
        vol.Required("profile"): str,
    }
)
@callback
def ws_set_room_profile(hass: HomeAssistant, connection: websocket_api.ActiveConnection, msg: dict[str, Any]) -> None:
    """Assign a profile to a room."""
    manager = _manager_or_error(hass, connection, msg["id"])
    if manager is None:
        return
    try:
        manager.set_assignment(msg["room_id"], msg["profile"])
    except (KeyError, ValueError) as err:
        connection.send_error(msg["id"], "invalid_format", str(err))
        return
    connection.send_result(msg["id"])


@websocket_api.websocket_command({vol.Required("type"): "shuttermanager/room/apply", vol.Required("room_id"): str})
@callback
def ws_room_apply(hass: HomeAssistant, connection: websocket_api.ActiveConnection, msg: dict[str, Any]) -> None:
    """Move a room's shutters to where its plan has them right now."""
    manager = _manager_or_error(hass, connection, msg["id"])
    if manager is None:
        return
    try:
        manager.apply_plan_now(msg["room_id"])
    except (KeyError, ValueError) as err:
        connection.send_error(msg["id"], "invalid_format", str(err))
        return
    connection.send_result(msg["id"])


@websocket_api.websocket_command(
    {
        vol.Required("type"): "shuttermanager/pause",
        vol.Exclusive("hours", "end"): vol.All(vol.Coerce(float), vol.Range(min=0.1, max=24 * 60)),
        vol.Exclusive("until", "end"): str,
    }
)
@callback
def ws_pause(hass: HomeAssistant, connection: websocket_api.ActiveConnection, msg: dict[str, Any]) -> None:
    """Pause the schedule for some hours, until a moment, or indefinitely."""
    manager = _manager_or_error(hass, connection, msg["id"])
    if manager is None:
        return
    until = None
    if "hours" in msg:
        until = dt_util.now() + timedelta(hours=msg["hours"])
    elif "until" in msg and (until := parse_moment(msg["until"])) is None:
        connection.send_error(msg["id"], "invalid_format", "Invalid date")
        return
    try:
        manager.set_pause(True, until)
    except ValueError as err:
        connection.send_error(msg["id"], "invalid_format", str(err))
        return
    connection.send_result(msg["id"])


@websocket_api.websocket_command({vol.Required("type"): "shuttermanager/resume"})
@callback
def ws_resume(hass: HomeAssistant, connection: websocket_api.ActiveConnection, msg: dict[str, Any]) -> None:
    """Resume the schedule."""
    manager = _manager_or_error(hass, connection, msg["id"])
    if manager is None:
        return
    manager.set_pause(False)
    connection.send_result(msg["id"])


@websocket_api.websocket_command(
    {
        vol.Required("type"): "shuttermanager/vacation",
        vol.Exclusive("until", "v"): str,
        vol.Exclusive("end", "v"): bool,
        vol.Optional("random"): vol.All(vol.Coerce(int), vol.Range(min=0, max=120)),
    }
)
@callback
def ws_vacation(hass: HomeAssistant, connection: websocket_api.ActiveConnection, msg: dict[str, Any]) -> None:
    """Follow the vacation plan until a moment, or end the vacation."""
    manager = _manager_or_error(hass, connection, msg["id"])
    if manager is None:
        return
    until = None
    if "until" in msg:
        if (until := parse_moment(msg["until"])) is None:
            connection.send_error(msg["id"], "invalid_format", "Invalid date")
            return
    elif not msg.get("end"):
        connection.send_error(msg["id"], "invalid_format", "until or end required")
        return
    try:
        manager.set_vacation(until, msg.get("random"))
    except ValueError as err:
        connection.send_error(msg["id"], "invalid_format", str(err))
        return
    connection.send_result(msg["id"])
