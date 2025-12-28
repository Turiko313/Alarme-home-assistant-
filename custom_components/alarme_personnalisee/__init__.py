"""The Alarme Personnalisée integration."""

from __future__ import annotations

import os
from pathlib import Path
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.const import Platform
from homeassistant.components import frontend

from .const import DOMAIN

PLATFORMS: list[Platform] = [Platform.ALARM_CONTROL_PANEL]

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Alarme Personnalisée from a config entry."""
    hass.data.setdefault(DOMAIN, {})
    
    # Enregistrer le fichier du panneau
    panel_dir = Path(__file__).parent
    panel_url = f"/alarme_personnalisee_panel/panel.html"
    
    hass.http.register_static_path(
        panel_url,
        str(panel_dir / "panel.html"),
        cache_headers=False
    )
    
    # Enregistrer le panneau dans la sidebar
    frontend.async_register_built_in_panel(
        hass,
        component_name="iframe",
        sidebar_title="Alarme",
        sidebar_icon="mdi:shield-home",
        frontend_url_path="alarme",
        config={"url": panel_url},
        require_admin=False,
    )
    
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    frontend.async_remove_panel(hass, "alarme")
    
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id, None)
    
    return unload_ok
