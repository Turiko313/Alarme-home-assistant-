"""The Alarme Personnalisée integration."""

from __future__ import annotations

from homeassistant.components import frontend
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.const import Platform

from .const import DOMAIN

PLATFORMS: list[Platform] = [Platform.ALARM_CONTROL_PANEL]
PANEL_URL_PATH = "alarme-personnalisee"
PANEL_WEB_COMPONENT = "alarme-panel"
PANEL_TITLE = "Alarme Personnalisée"
PANEL_ICON = "mdi:shield-lock"

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Alarme Personnalisée from a config entry."""

    # Forward the setup to the alarm_control_panel platform
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    # Register the frontend panel
    js_url = f"/{DOMAIN}/panel.js"

    # Serve the panel's JS file
    hass.http.register_static_path(
        hass.config.path(f"custom_components/{DOMAIN}/www/alarme_panel.js"),
        js_url,
    )

    frontend.async_register_panel(
        hass,
        PANEL_URL_PATH,
        PANEL_WEB_COMPONENT,
        PANEL_TITLE,
        PANEL_ICON,
        js_url=js_url,
    )

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""

    # Unload the alarm_control_panel platform
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)

    if unload_ok:
        # Remove the frontend panel
        frontend.async_remove_panel(hass, PANEL_URL_PATH)

    return unload_ok
