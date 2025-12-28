"""The Alarme Personnalisée integration."""

from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.const import Platform
from homeassistant.components import frontend

PLATFORMS: list[Platform] = [Platform.ALARM_CONTROL_PANEL]

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Alarme Personnalisée from a config entry."""
    frontend.async_register_built_in_panel(
        hass,
        "iframe",
        "Alarme Personnalisée",
        "mdi:shield-home",
        "alarme_personnalisee",
        {"url": f"/config/integrations/config_entry/{entry.entry_id}"},
        require_admin=True,
    )
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    frontend.async_remove_panel(hass, "alarme_personnalisee")
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
