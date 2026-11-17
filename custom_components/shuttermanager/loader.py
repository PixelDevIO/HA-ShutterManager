"""Make sure the card loads even when the browser was faster than Home Assistant.

``add_extra_js_url`` only reaches pages that are opened after ShutterManager has
started. A dashboard opened (or reloaded by the frontend) while Home Assistant
is still starting never gets the card and shows a configuration error until the
user reloads the tab.

Dashboard resources (storage mode) are read by the frontend right at page start,
long before custom integrations are ready. ShutterManager therefore keeps one small
resource there: a loader that waits until ``/shuttermanager_static`` is served and
then imports the card. Once the element is defined, the frontend redraws the
card on its own. The loader is inline (a ``data:`` URL) because our own static
path does not exist yet when the page loads.

Users with YAML resources are left alone; for them ``add_extra_js_url`` still
covers every page opened after the start.
"""

from __future__ import annotations

import logging
from typing import Any
from urllib.parse import quote, unquote

from homeassistant.core import HomeAssistant

from .const import CARD_FILENAME, FRONTEND_URL, VERSION

_LOGGER = logging.getLogger(__name__)

LOADER_MARKER = "ShutterManager card loader"
LOADER_PREFIX = "data:text/javascript,"

# Tries for about ten minutes, slowing down from 2 s to 15 s between attempts.
LOADER_JS = (
    f"/* {LOADER_MARKER} */"
    "(async()=>{"
    'const tag="shuttermanager-card";'
    f'const base=new URL("{FRONTEND_URL}/{CARD_FILENAME}?v={VERSION}",location.origin).href;'
    "for(let i=0;i<60;i++){"
    "if(customElements.get(tag))return;"
    # a failed import may be cached per URL, so retries use a fresh one
    'try{await import(i?base+"&r="+i:base);return}'
    "catch(e){await new Promise(r=>setTimeout(r,Math.min(2000+i*1000,15000)))}"
    "}"
    "})();"
)


def loader_url() -> str:
    """The resource URL of the loader for this version."""
    return LOADER_PREFIX + quote(LOADER_JS, safe="/*(){};:=,.?+&<>!\"'")


def is_loader(item: dict[str, Any]) -> bool:
    """Whether a dashboard resource is (any version of) our loader."""
    url = str(item.get("url", ""))
    return url.startswith(LOADER_PREFIX) and LOADER_MARKER in unquote(url)


def _storage_resources(hass: HomeAssistant) -> Any | None:
    """The dashboard resource collection, if resources are kept in storage."""
    try:
        from homeassistant.components.lovelace.const import LOVELACE_DATA  # noqa: PLC0415
        from homeassistant.components.lovelace.resources import ResourceStorageCollection  # noqa: PLC0415
    except ImportError:
        return None
    data = hass.data.get(LOVELACE_DATA)
    resources = getattr(data, "resources", None)
    if not isinstance(resources, ResourceStorageCollection):
        return None
    return resources


async def _loaded(resources: Any) -> Any:
    if not resources.loaded:
        await resources.async_load()
        resources.loaded = True
    return resources


async def async_ensure_loader(hass: HomeAssistant) -> None:
    """Add or update the loader resource; never fails the setup."""
    try:
        if (resources := _storage_resources(hass)) is None:
            _LOGGER.debug("Dashboard resources are not in storage mode, no loader added")
            return
        await _loaded(resources)
        url = loader_url()
        ours = [item for item in resources.async_items() if is_loader(item)]
        if not ours:
            await resources.async_create_item({"res_type": "module", "url": url})
            return
        first, *duplicates = ours
        if first.get("url") != url or first.get("type") != "module":
            await resources.async_update_item(first["id"], {"res_type": "module", "url": url})
        for item in duplicates:
            await resources.async_delete_item(item["id"])
    except Exception:  # noqa: BLE001 - the card still loads the normal way
        _LOGGER.warning("Could not register the ShutterManager card loader", exc_info=True)


async def async_remove_loader(hass: HomeAssistant) -> None:
    """Remove the loader when ShutterManager is deleted."""
    try:
        if (resources := _storage_resources(hass)) is None:
            return
        await _loaded(resources)
        for item in [i for i in resources.async_items() if is_loader(i)]:
            await resources.async_delete_item(item["id"])
    except Exception:  # noqa: BLE001
        _LOGGER.warning("Could not remove the ShutterManager card loader", exc_info=True)
