"""Button entities for Alarme Personnalisée."""

from __future__ import annotations

from homeassistant.components.button import ButtonEntity
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.entity import DeviceInfo, EntityCategory
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .entity import alarm_device_info
from .runtime_data import AlarmConfigEntry


async def async_setup_entry(
    hass: HomeAssistant,
    entry: AlarmConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up button entities."""
    async_add_entities([ResetTriggerCountButton(entry)])


class ResetTriggerCountButton(ButtonEntity):
    """Button that resets the trigger count."""

    _attr_has_entity_name = True
    _attr_translation_key = "reset_trigger_count"
    _attr_icon = "mdi:counter"
    _attr_entity_category = EntityCategory.CONFIG

    def __init__(self, entry: AlarmConfigEntry) -> None:
        """Initialize the button."""
        self._entry = entry
        self._attr_unique_id = f"{entry.entry_id}_reset_trigger_count"

    @property
    def device_info(self) -> DeviceInfo:
        """Return the device information."""
        return alarm_device_info(self._entry)

    async def async_press(self) -> None:
        """Reset the trigger count for this config entry."""
        if (alarm := self._entry.runtime_data.alarm) is None:
            raise HomeAssistantError("Alarm entity is not available")
        alarm.reset_trigger_count()
