"""Fixtures for ShutterManager tests."""

from __future__ import annotations

from unittest.mock import patch

from homeassistant.core import HomeAssistant
import pytest


@pytest.fixture(autouse=True)
def auto_enable_custom_integrations(enable_custom_integrations):
    """Allow loading custom_components/shuttermanager."""
    return


@pytest.fixture(autouse=True)
def no_frontend(hass: HomeAssistant):
    """The frontend package is not installed in the test environment."""
    hass.config.components.add("frontend")
    with patch("custom_components.shuttermanager._async_register_frontend"):
        yield
