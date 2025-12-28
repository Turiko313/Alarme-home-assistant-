"""Switch entities for Alarme Personnalisée."""
from __future__ import annotations

import logging
from homeassistant.components.switch import SwitchEntity
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
    """Set up switch entities."""
    async_add_entities([RearmAfterTriggerSwitch(hass, entry)])


class RearmAfterTriggerSwitch(SwitchEntity):
    """Switch to enable/disable rearm after trigger."""

    _attr_has_entity_name = True
    _attr_icon = "mdi:reload"

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        """Initialize the switch."""
        self.hass = hass
        self._entry = entry
        self._attr_unique_id = f"{entry.entry_id}_rearm_after_trigger"
        self._attr_name = "Réarmer après déclenchement"
        self._attr_device_info = {
            "identifiers": {(DOMAIN, entry.entry_id)},
            "name": "Alarme Personnalisée",
            "manufacturer": "Custom",
            "model": "Alarme Personnalisée",
        }
        self._update_state()

    def _update_state(self) -> None:
        """Update state from config entry options."""
        self._attr_is_on = self._entry.options.get("rearm_after_trigger", False)

    @property
    def is_on(self) -> bool:
        """Return true if switch is on."""
        return self._entry.options.get("rearm_after_trigger", False)

    async def async_turn_on(self, **kwargs) -> None:
        """Turn the switch on."""
        new_options = {**self._entry.options, "rearm_after_trigger": True}
        self.hass.config_entries.async_update_entry(self._entry, options=new_options)
        self._attr_is_on = True
        self.async_write_ha_state()
        _LOGGER.info("Rearm after trigger enabled")

    async def async_turn_off(self, **kwargs) -> None:
        """Turn the switch off."""
        new_options = {**self._entry.options, "rearm_after_trigger": False}
        self.hass.config_entries.async_update_entry(self._entry, options=new_options)
        self._attr_is_on = False
        self.async_write_ha_state()
        _LOGGER.info("Rearm after trigger disabled")
