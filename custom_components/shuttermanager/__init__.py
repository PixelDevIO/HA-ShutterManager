"""ShutterManager: room-based shutter control for Home Assistant."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path

from homeassistant.components.frontend import add_extra_js_url
from homeassistant.components.http import StaticPathConfig
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.exceptions import ServiceValidationError
from homeassistant.helpers import config_validation as cv, device_registry as dr
from homeassistant.helpers.storage import Store
from homeassistant.helpers.typing import ConfigType
from homeassistant.util import dt as dt_util
import voluptuous as vol

from .const import CARD_FILENAME, DOMAIN, FRONTEND_URL, NAME, STORAGE_KEY, STORAGE_VERSION, VERSION
from .loader import async_ensure_loader, async_remove_loader
from .manager import ShutterManager, get_manager
from .websocket import async_register_websocket

PLATFORMS = [Platform.SELECT, Platform.SENSOR, Platform.SWITCH]

SERVICE_PAUSE = "pause"
SERVICE_RESUME = "resume"
SERVICE_START_VACATION = "start_vacation"
SERVICE_END_VACATION = "end_vacation"
SERVICE_APPLY_PLAN = "apply_plan"

PAUSE_SCHEMA = vol.Schema(
    {
        vol.Exclusive("duration", "end"): cv.positive_time_period,
        vol.Exclusive("until", "end"): cv.datetime,
    }
)
VACATION_SCHEMA = vol.Schema(
    {
        vol.Required("until"): cv.datetime,
        vol.Optional("random"): vol.All(vol.Coerce(int), vol.Range(min=0, max=120)),
    }
)
ROOM_SCHEMA = vol.Schema({vol.Required("room"): cv.string})

CONFIG_SCHEMA = cv.config_entry_only_config_schema(DOMAIN)

type ShutterManagerConfigEntry = ConfigEntry[ShutterManager]


async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    """Register the card, websocket commands and actions once."""
    hass.data.setdefault(DOMAIN, {})
    await _async_register_frontend(hass)
    async_register_websocket(hass)

    async def _pause(call: ServiceCall) -> None:
        until = None
        if (duration := call.data.get("duration")) is not None:
            until = dt_util.now() + duration
        elif (moment := call.data.get("until")) is not None:
            until = _local(moment)
        try:
            _manager(hass).set_pause(True, until)
        except ValueError as err:
            raise ServiceValidationError(str(err)) from err

    async def _resume(call: ServiceCall) -> None:
        _manager(hass).set_pause(False)

    async def _start_vacation(call: ServiceCall) -> None:
        try:
            _manager(hass).set_vacation(_local(call.data["until"]), call.data.get("random"))
        except ValueError as err:
            raise ServiceValidationError(str(err)) from err

    async def _end_vacation(call: ServiceCall) -> None:
        _manager(hass).set_vacation(None)

    async def _apply_plan(call: ServiceCall) -> None:
        manager = _manager(hass)
        try:
            manager.apply_plan_now(_room_id(manager, call.data["room"]))
        except ValueError as err:
            raise ServiceValidationError(str(err)) from err

    hass.services.async_register(DOMAIN, SERVICE_PAUSE, _pause, schema=PAUSE_SCHEMA)
    hass.services.async_register(DOMAIN, SERVICE_RESUME, _resume)
    hass.services.async_register(DOMAIN, SERVICE_START_VACATION, _start_vacation, schema=VACATION_SCHEMA)
    hass.services.async_register(DOMAIN, SERVICE_END_VACATION, _end_vacation)
    hass.services.async_register(DOMAIN, SERVICE_APPLY_PLAN, _apply_plan, schema=ROOM_SCHEMA)
    return True


async def _async_register_frontend(hass: HomeAssistant) -> None:
    """Serve the card and load it on every dashboard (no manual resource needed)."""
    await hass.http.async_register_static_paths(
        [StaticPathConfig(FRONTEND_URL, str(Path(__file__).parent / "frontend"), False)]
    )
    add_extra_js_url(hass, f"{FRONTEND_URL}/{CARD_FILENAME}?v={VERSION}")
    # pages opened while Home Assistant is still starting miss the line above
    await async_ensure_loader(hass)


def _local(moment: datetime) -> datetime:
    return dt_util.as_local(moment if moment.tzinfo else moment.replace(tzinfo=dt_util.get_default_time_zone()))


def _manager(hass: HomeAssistant) -> ShutterManager:
    try:
        return get_manager(hass)
    except LookupError as err:
        raise ServiceValidationError("ShutterManager is not set up") from err


def _room_id(manager: ShutterManager, value: str) -> str:
    """Find a room by id or name."""
    if value in manager.rooms:
        return value
    for room in manager.rooms.values():
        if room.name.casefold() == value.strip().casefold():
            return room.id
    raise ServiceValidationError(f"Unknown room {value}")


async def async_setup_entry(hass: HomeAssistant, entry: ShutterManagerConfigEntry) -> bool:
    """Set up ShutterManager from a config entry."""
    manager = ShutterManager(hass, entry)
    await manager.async_load()
    entry.runtime_data = manager
    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = manager
    # Parent device first, room devices refer to it
    dr.async_get(hass).async_get_or_create(
        config_entry_id=entry.entry_id,
        identifiers={(DOMAIN, entry.entry_id)},
        name=NAME,
        manufacturer="PixelDevIO",
        model="ShutterManager",
        sw_version=VERSION,
        entry_type=dr.DeviceEntryType.SERVICE,
    )
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    await manager.async_start()
    entry.async_on_unload(entry.add_update_listener(_async_reload))
    return True


async def _async_reload(hass: HomeAssistant, entry: ShutterManagerConfigEntry) -> None:
    await hass.config_entries.async_reload(entry.entry_id)


async def async_unload_entry(hass: HomeAssistant, entry: ShutterManagerConfigEntry) -> bool:
    """Unload a config entry."""
    entry.runtime_data.async_stop()
    unloaded = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unloaded:
        hass.data[DOMAIN].pop(entry.entry_id, None)
    return unloaded


async def async_remove_entry(hass: HomeAssistant, entry: ShutterManagerConfigEntry) -> None:
    """Remove stored state when the integration is deleted."""
    await Store(hass, STORAGE_VERSION, f"{STORAGE_KEY}.{entry.entry_id}").async_remove()
    await async_remove_loader(hass)


async def async_remove_config_entry_device(
    hass: HomeAssistant, entry: ShutterManagerConfigEntry, device: dr.DeviceEntry
) -> bool:
    """Allow deleting the device of a room that no longer exists."""
    rooms = {f"{entry.entry_id}_{room_id}" for room_id in entry.runtime_data.rooms}
    return not any(
        ident in rooms or ident == entry.entry_id for domain, ident in device.identifiers if domain == DOMAIN
    )
