"""Switch entities for Alarme Personnalisée."""

from __future__ import annotations

from homeassistant.components.switch import SwitchEntity
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo, EntityCategory
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import CONF_REARM_AFTER_TRIGGER
from .entity import alarm_device_info
from .runtime_data import AlarmConfigEntry


async def async_setup_entry(
    hass: HomeAssistant,
    entry: AlarmConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up switch entities."""
    async_add_entities([RearmAfterTriggerSwitch(entry)])


class RearmAfterTriggerSwitch(SwitchEntity):
    """Switch that controls automatic rearming."""

    _attr_has_entity_name = True
    _attr_translation_key = "rearm_after_trigger"
    _attr_icon = "mdi:reload"
    _attr_entity_category = EntityCategory.CONFIG

    def __init__(self, entry: AlarmConfigEntry) -> None:
        """Initialize the switch."""
        self._entry = entry
        self._attr_unique_id = f"{entry.entry_id}_rearm_after_trigger"

    @property
    def device_info(self) -> DeviceInfo:
        """Return the device information."""
        return alarm_device_info(self._entry)

    @property
    def is_on(self) -> bool:
        """Return whether automatic rearming is enabled."""
        return self._entry.options.get(CONF_REARM_AFTER_TRIGGER, False)

    async def async_turn_on(self, **kwargs) -> None:
        """Enable automatic rearming."""
        self._set_option(True)

    async def async_turn_off(self, **kwargs) -> None:
        """Disable automatic rearming."""
        self._set_option(False)

    def _set_option(self, enabled: bool) -> None:
        """Store the switch option."""
        new_options = {
            **self._entry.options,
            CONF_REARM_AFTER_TRIGGER: enabled,
        }
        self.hass.config_entries.async_update_entry(self._entry, options=new_options)
