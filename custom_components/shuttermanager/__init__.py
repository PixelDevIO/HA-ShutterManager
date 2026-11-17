"""ShutterManager: room-based shutter control for Home Assistant."""

from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers import config_validation as cv, device_registry as dr
from homeassistant.helpers.storage import Store
from homeassistant.helpers.typing import ConfigType

from .const import DOMAIN, NAME, STORAGE_KEY, STORAGE_VERSION, VERSION
from .manager import ShutterManager

PLATFORMS = [Platform.SENSOR, Platform.SWITCH]

CONFIG_SCHEMA = cv.config_entry_only_config_schema(DOMAIN)

type ShutterManagerConfigEntry = ConfigEntry[ShutterManager]


async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    hass.data.setdefault(DOMAIN, {})
    return True


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


async def async_remove_config_entry_device(
    hass: HomeAssistant, entry: ShutterManagerConfigEntry, device: dr.DeviceEntry
) -> bool:
    """Allow deleting the device of a room that no longer exists."""
    rooms = {f"{entry.entry_id}_{room_id}" for room_id in entry.runtime_data.rooms}
    return not any(
        ident in rooms or ident == entry.entry_id for domain, ident in device.identifiers if domain == DOMAIN
    )
