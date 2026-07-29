"""Number entities for Alarme Personnalisée."""

from __future__ import annotations

from homeassistant.components.number import NumberEntity, NumberMode
from homeassistant.const import UnitOfTime
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo, EntityCategory
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import (
    CONF_ARMING_TIME,
    CONF_DELAY_TIME,
    CONF_TRIGGER_TIME,
    DEFAULT_ARMING_TIME,
    DEFAULT_DELAY_TIME,
    DEFAULT_TRIGGER_TIME,
)
from .entity import alarm_device_info
from .runtime_data import AlarmConfigEntry


async def async_setup_entry(
    hass: HomeAssistant,
    entry: AlarmConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up number entities."""
    async_add_entities(
        [
            AlarmTimeNumber(
                entry,
                CONF_ARMING_TIME,
                DEFAULT_ARMING_TIME,
                "arming_time",
                "mdi:timer-sand",
                600,
            ),
            AlarmTimeNumber(
                entry,
                CONF_DELAY_TIME,
                DEFAULT_DELAY_TIME,
                "delay_time",
                "mdi:timer-outline",
                600,
            ),
            AlarmTimeNumber(
                entry,
                CONF_TRIGGER_TIME,
                DEFAULT_TRIGGER_TIME,
                "trigger_time",
                "mdi:timer-alert-outline",
                1800,
            ),
        ]
    )


class AlarmTimeNumber(NumberEntity):
    """Editable alarm delay."""

    _attr_has_entity_name = True
    _attr_mode = NumberMode.BOX
    _attr_native_unit_of_measurement = UnitOfTime.SECONDS
    _attr_native_min_value = 0
    _attr_native_step = 5
    _attr_entity_category = EntityCategory.CONFIG

    def __init__(
        self,
        entry: AlarmConfigEntry,
        config_key: str,
        default: int,
        translation_key: str,
        icon: str,
        maximum: int,
    ) -> None:
        """Initialize an alarm delay."""
        self._entry = entry
        self._config_key = config_key
        self._default = default
        self._attr_unique_id = f"{entry.entry_id}_{config_key}"
        self._attr_translation_key = translation_key
        self._attr_icon = icon
        self._attr_native_max_value = maximum

    @property
    def device_info(self) -> DeviceInfo:
        """Return the device information."""
        return alarm_device_info(self._entry)

    @property
    def native_value(self) -> float:
        """Return the configured delay."""
        return self._entry.options.get(self._config_key, self._default)

    async def async_set_native_value(self, value: float) -> None:
        """Update the configured delay."""
        new_options = {**self._entry.options, self._config_key: int(value)}
        self.hass.config_entries.async_update_entry(self._entry, options=new_options)
