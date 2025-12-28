"""The Alarme Personnalisée integration."""

from __future__ import annotations

import logging
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.const import Platform
import voluptuous as vol
from homeassistant.helpers import config_validation as cv

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

PLATFORMS: list[Platform] = [Platform.ALARM_CONTROL_PANEL]

SERVICE_RESET_TRIGGER_COUNT = "reset_trigger_count"

SERVICE_RESET_TRIGGER_COUNT_SCHEMA = vol.Schema(
    {
        vol.Required("entity_id"): cv.entity_id,
    }
)

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Alarme Personnalisée from a config entry."""
    hass.data.setdefault(DOMAIN, {})
    
    # PAS DE PANNEAU POUR L'INSTANT - On se concentre sur l'alarme de base
    
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    
    # Enregistrer le service reset_trigger_count
    async def async_reset_trigger_count(call: ServiceCall) -> None:
        """Reset the trigger count for the alarm."""
        entity_id = call.data.get("entity_id")
        
        # Trouver l'entité dans hass.data
        for entry_id, entity in hass.data.get(DOMAIN, {}).items():
            if hasattr(entity, 'entity_id') and entity.entity_id == entity_id:
                entity._triggered_count = 0
                entity.async_write_ha_state()
                _LOGGER.info("Trigger count reset for %s", entity_id)
                return
        
        _LOGGER.warning("Could not find entity %s to reset trigger count", entity_id)
    
    hass.services.async_register(
        DOMAIN,
        SERVICE_RESET_TRIGGER_COUNT,
        async_reset_trigger_count,
        schema=SERVICE_RESET_TRIGGER_COUNT_SCHEMA,
    )
    
    _LOGGER.info("Alarme Personnalisée setup completed successfully")
    
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    # Supprimer le service
    hass.services.async_remove(DOMAIN, SERVICE_RESET_TRIGGER_COUNT)
    
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id, None)
    
    return unload_ok
