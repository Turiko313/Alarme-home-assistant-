"""Diagnostic sensors for Alarme Personnalisée."""

from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import datetime

from homeassistant.components.sensor import SensorDeviceClass, SensorEntity
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.dispatcher import async_dispatcher_connect
from homeassistant.helpers.entity import DeviceInfo, EntityCategory
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import SIGNAL_STATE_UPDATED
from .entity import alarm_device_info
from .runtime_data import AlarmConfigEntry


async def async_setup_entry(
    hass: HomeAssistant,
    entry: AlarmConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up diagnostic sensors."""
    async_add_entities(
        [
            TriggerCountSensor(entry),
            LastTriggeredBySensor(entry),
            LastChangedAtSensor(entry),
        ]
    )


class AlarmBaseSensor(SensorEntity, ABC):
    """Base class for alarm diagnostic sensors."""

    _attr_has_entity_name = True
    _attr_should_poll = False
    _attr_entity_category = EntityCategory.DIAGNOSTIC

    def __init__(self, entry: AlarmConfigEntry) -> None:
        """Initialize a diagnostic sensor."""
        self._entry = entry

    @property
    def device_info(self) -> DeviceInfo:
        """Return the device information."""
        return alarm_device_info(self._entry)

    async def async_added_to_hass(self) -> None:
        """Subscribe to alarm state updates."""
        await super().async_added_to_hass()
        self.async_on_remove(
            async_dispatcher_connect(
                self.hass,
                f"{SIGNAL_STATE_UPDATED}_{self._entry.entry_id}",
                self._handle_alarm_update,
            )
        )
        self._update_from_alarm()

    @callback
    def _handle_alarm_update(self) -> None:
        """Refresh the sensor when its alarm changes."""
        self._update_from_alarm()
        self.async_write_ha_state()

    @abstractmethod
    def _update_from_alarm(self) -> None:
        """Update the native value from the alarm."""


class TriggerCountSensor(AlarmBaseSensor):
    """Number of alarm triggers."""

    _attr_translation_key = "trigger_count"
    _attr_icon = "mdi:counter"

    def __init__(self, entry: AlarmConfigEntry) -> None:
        """Initialize the trigger count sensor."""
        super().__init__(entry)
        self._attr_unique_id = f"{entry.entry_id}_trigger_count"
        self._attr_native_value = 0

    def _update_from_alarm(self) -> None:
        """Update from the alarm entity."""
        if (alarm := self._entry.runtime_data.alarm) is not None:
            self._attr_native_value = alarm.triggered_count


class LastTriggeredBySensor(AlarmBaseSensor):
    """Entity that most recently triggered the alarm."""

    _attr_translation_key = "last_triggered_by"
    _attr_icon = "mdi:motion-sensor"

    def __init__(self, entry: AlarmConfigEntry) -> None:
        """Initialize the last-triggered-by sensor."""
        super().__init__(entry)
        self._attr_unique_id = f"{entry.entry_id}_last_triggered_by"

    def _update_from_alarm(self) -> None:
        """Update from the alarm entity."""
        alarm = self._entry.runtime_data.alarm
        self._attr_native_value = alarm.last_triggered_by_name if alarm else None


class LastChangedAtSensor(AlarmBaseSensor):
    """Time of the latest alarm transition."""

    _attr_translation_key = "last_changed_at"
    _attr_icon = "mdi:clock-outline"
    _attr_device_class = SensorDeviceClass.TIMESTAMP

    def __init__(self, entry: AlarmConfigEntry) -> None:
        """Initialize the timestamp sensor."""
        super().__init__(entry)
        self._attr_unique_id = f"{entry.entry_id}_last_changed_at"
        self._attr_native_value: datetime | None = None

    def _update_from_alarm(self) -> None:
        """Update from the alarm entity."""
        if (alarm := self._entry.runtime_data.alarm) is not None:
            self._attr_native_value = alarm.last_changed_at
