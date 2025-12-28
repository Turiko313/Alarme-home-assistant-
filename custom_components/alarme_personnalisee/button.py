"""Button entities for Alarme Personnalisee."""
from __future__ import annotations

import logging
from homeassistant.components.button import ButtonEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up button entities."""
    async_add_entities([ResetTriggerCountButton(hass, entry)])


class ResetTriggerCountButton(ButtonEntity):
    """Button to reset the trigger count."""

    _attr_has_entity_name = True
    _attr_icon = "mdi:counter"

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        """Initialize the button."""
        self.hass = hass
        self._entry = entry
        self._attr_unique_id = f"{entry.entry_id}_reset_trigger_count"
        self._attr_name = "Reinitialiser le compteur"
        self._attr_device_info = {
            "identifiers": {(DOMAIN, entry.entry_id)},
            "name": "Alarme Personnalisee",
            "manufacturer": "Custom",
            "model": "Alarme Personnalisee",
        }

    async def async_press(self) -> None:
        """Handle the button press."""
        # Trouver l'entite alarme
        for entry_id, entity in self.hass.data.get(DOMAIN, {}).items():
            if hasattr(entity, '_triggered_count'):
                entity._triggered_count = 0
                entity.async_write_ha_state()
                _LOGGER.info("Trigger count reset via button")
                return
        
        _LOGGER.warning("Could not find alarm entity to reset trigger count")
