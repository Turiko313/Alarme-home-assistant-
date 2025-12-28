"""Number entities for Alarme Personnalisee."""
from __future__ import annotations

import logging
from homeassistant.components.number import NumberEntity, NumberMode
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
    """Set up number entities."""
    async_add_entities([
        ArmingTimeNumber(hass, entry),
        DelayTimeNumber(hass, entry),
        TriggerTimeNumber(hass, entry),
    ])


class AlarmTimeNumber(NumberEntity):
    """Base class for time configuration numbers."""

    _attr_has_entity_name = True
    _attr_mode = NumberMode.BOX
    _attr_native_unit_of_measurement = "s"
    _attr_native_min_value = 0
    _attr_native_max_value = 600
    _attr_native_step = 5

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry, config_key: str, name: str, icon: str) -> None:
        """Initialize the number entity."""
        self.hass = hass
        self._entry = entry
        self._config_key = config_key
        self._attr_unique_id = f"{entry.entry_id}_{config_key}"
        self._attr_name = name
        self._attr_icon = icon
        self._attr_device_info = {
            "identifiers": {(DOMAIN, entry.entry_id)},
            "name": "Alarme Personnalisee",
            "manufacturer": "Custom",
            "model": "Alarme Personnalisee",
        }
        self._update_value()

    def _update_value(self) -> None:
        """Update value from config entry options."""
        self._attr_native_value = self._entry.options.get(self._config_key, 30)

    @property
    def native_value(self) -> float:
        """Return the current value."""
        return self._entry.options.get(self._config_key, 30)

    async def async_set_native_value(self, value: float) -> None:
        """Update the value."""
        new_options = {**self._entry.options, self._config_key: int(value)}
        self.hass.config_entries.async_update_entry(self._entry, options=new_options)
        self._attr_native_value = int(value)
        self.async_write_ha_state()
        _LOGGER.info("Updated %s to %s seconds", self._config_key, int(value))


class ArmingTimeNumber(AlarmTimeNumber):
    """Number entity for arming time."""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        """Initialize arming time number."""
        super().__init__(
            hass,
            entry,
            "arming_time",
            "Delai d'armement",
            "mdi:timer-sand"
        )


class DelayTimeNumber(AlarmTimeNumber):
    """Number entity for delay time."""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        """Initialize delay time number."""
        super().__init__(
            hass,
            entry,
            "delay_time",
            "Delai d'entree",
            "mdi:timer-outline"
        )


class TriggerTimeNumber(AlarmTimeNumber):
    """Number entity for trigger time."""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        """Initialize trigger time number."""
        super().__init__(
            hass,
            entry,
            "trigger_time",
            "Duree de declenchement",
            "mdi:timer-alert-outline"
        )
        self._attr_native_max_value = 1800  # 30 minutes max
