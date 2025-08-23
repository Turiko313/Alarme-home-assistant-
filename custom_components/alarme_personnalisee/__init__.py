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

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Alarme Personnalisée from a config entry."""

    _LOGGER.info("Setting up Alarme Personnalisée integration.")

    # Forward the setup to the alarm_control_panel platform
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    # Register the frontend panel
    # The 'webcomponent' key in manifest.json handles the JS loading.
    await frontend.async_register_panel(
        hass,
        panel_url="alarme-personnalisee",
        webcomponent_name="alarme-panel",
        sidebar_title="Alarme",
        sidebar_icon="mdi:shield-lock",
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
        frontend.async_remove_panel(hass, "alarme-personnalisee")

    return unload_ok
