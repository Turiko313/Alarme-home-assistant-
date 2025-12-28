"""Services for Alarme Personnalisée integration."""
from __future__ import annotations

import logging
import voluptuous as vol

from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.helpers import config_validation as cv

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

SERVICE_RESET_TRIGGER_COUNT = "reset_trigger_count"

SERVICE_RESET_TRIGGER_COUNT_SCHEMA = vol.Schema(
    {
        vol.Required("entity_id"): cv.entity_id,
    }
)


async def async_setup_services(hass: HomeAssistant) -> None:
    """Set up services for Alarme Personnalisée integration."""

    async def async_reset_trigger_count(call: ServiceCall) -> None:
        """Reset the trigger count for the alarm."""
        entity_id = call.data.get("entity_id")
        
        # Get the entity from the registry
        entity_registry = hass.data.get("entity_registry")
        if entity_registry:
            entity = entity_registry.async_get(entity_id)
            if entity and entity.platform == DOMAIN:
                # Find the alarm entity
                for entity_obj in hass.data.get(DOMAIN, {}).values():
                    if entity_obj.entity_id == entity_id:
                        entity_obj._triggered_count = 0
                        entity_obj.async_write_ha_state()
                        _LOGGER.info("Trigger count reset for %s", entity_id)
                        return
        
        _LOGGER.warning("Could not find entity %s to reset trigger count", entity_id)

    hass.services.async_register(
        DOMAIN,
        SERVICE_RESET_TRIGGER_COUNT,
        async_reset_trigger_count,
        schema=SERVICE_RESET_TRIGGER_COUNT_SCHEMA,
    )


async def async_unload_services(hass: HomeAssistant) -> None:
    """Unload services for Alarme Personnalisée integration."""
    hass.services.async_remove(DOMAIN, SERVICE_RESET_TRIGGER_COUNT)
