"""The Alarme Personnalisée integration."""

from __future__ import annotations

import logging

from homeassistant.components import frontend
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.const import Platform

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

PLATFORMS: list[Platform] = [Platform.ALARM_CONTROL_PANEL]
PANEL_URL = "alarme-personnalisee"
PANEL_WEBCOMPONENT = "alarme-panel"
PANEL_TITLE = "Alarme"
PANEL_ICON = "mdi:shield-lock"

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Alarme Personnalisée from a config entry."""

    _LOGGER.info("Setting up Alarme Personnalisée integration.")

    # Forward the setup to the alarm_control_panel platform
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    # Register the frontend panel

    # Serve the www directory
    static_path = hass.config.path(f"custom_components/{DOMAIN}/www")
    url_path = f"/{DOMAIN}_files"
    hass.http.register_static_path(url_path, static_path)

    # Register the panel
    await hass.components.frontend.async_register_panel(
        hass,
        PANEL_WEBCOMPONENT,
        PANEL_URL,
        PANEL_TITLE,
        PANEL_ICON,
        f"{url_path}/alarme_panel.js",
        require_admin=True,
    )

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""

    _LOGGER.info("Unloading Alarme Personnalisée integration.")

    # Unload the alarm_control_panel platform
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)

    if unload_ok:
        # Remove the frontend panel
        frontend.async_remove_panel(hass, PANEL_URL)

    return unload_ok
