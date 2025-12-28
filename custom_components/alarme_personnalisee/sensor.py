"""Sensor entities for Alarme Personnalisee."""
from __future__ import annotations

import logging
from datetime import datetime
from homeassistant.components.sensor import SensorEntity, SensorDeviceClass
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.event import async_track_state_change_event

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up sensor entities."""
    alarm_entity_id = f"alarm_control_panel.alarme"
    
    async_add_entities([
        TriggerCountSensor(hass, entry, alarm_entity_id),
        LastTriggeredBySensor(hass, entry, alarm_entity_id),
        LastChangedAtSensor(hass, entry, alarm_entity_id),
    ])


class AlarmBaseSensor(SensorEntity):
    """Base class for alarm sensors."""

    _attr_has_entity_name = True
    _attr_should_poll = False

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry, alarm_entity_id: str) -> None:
        """Initialize the sensor."""
        self.hass = hass
        self._entry = entry
        self._alarm_entity_id = alarm_entity_id
        self._attr_device_info = {
            "identifiers": {(DOMAIN, entry.entry_id)},
            "name": "Alarme Personnalisee",
            "manufacturer": "Custom",
            "model": "Alarme Personnalisee",
        }

    async def async_added_to_hass(self) -> None:
        """Run when entity about to be added to hass."""
        await super().async_added_to_hass()
        
        # Ecouter les changements de l'entite alarme
        self.async_on_remove(
            async_track_state_change_event(
                self.hass,
                [self._alarm_entity_id],
                self._async_alarm_state_changed,
            )
        )
        
        # Mettre a jour immediatement
        self._update_from_alarm()

    @callback
    def _async_alarm_state_changed(self, event) -> None:
        """Handle alarm state changes."""
        self._update_from_alarm()
        self.async_write_ha_state()

    def _update_from_alarm(self) -> None:
        """Update sensor from alarm entity - to be overridden."""
        pass


class TriggerCountSensor(AlarmBaseSensor):
    """Sensor for trigger count."""

    _attr_icon = "mdi:counter"
    _attr_native_unit_of_measurement = "declenchements"

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry, alarm_entity_id: str) -> None:
        """Initialize the sensor."""
        super().__init__(hass, entry, alarm_entity_id)
        self._attr_unique_id = f"{entry.entry_id}_trigger_count"
        self._attr_name = "Nombre de declenchements"

    def _update_from_alarm(self) -> None:
        """Update from alarm entity."""
        alarm_state = self.hass.states.get(self._alarm_entity_id)
        if alarm_state:
            self._attr_native_value = alarm_state.attributes.get("triggered_count", 0)


class LastTriggeredBySensor(AlarmBaseSensor):
    """Sensor for last triggered by."""

    _attr_icon = "mdi:motion-sensor"

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry, alarm_entity_id: str) -> None:
        """Initialize the sensor."""
        super().__init__(hass, entry, alarm_entity_id)
        self._attr_unique_id = f"{entry.entry_id}_last_triggered_by"
        self._attr_name = "Dernier capteur declencheur"

    def _update_from_alarm(self) -> None:
        """Update from alarm entity."""
        alarm_state = self.hass.states.get(self._alarm_entity_id)
        if alarm_state:
            triggered_by = alarm_state.attributes.get("last_triggered_by")
            if triggered_by:
                # Essayer de recuperer le nom convivial du capteur
                sensor_state = self.hass.states.get(triggered_by)
                if sensor_state:
                    self._attr_native_value = sensor_state.attributes.get("friendly_name", triggered_by)
                else:
                    self._attr_native_value = triggered_by
            else:
                self._attr_native_value = "Aucun"


class LastChangedAtSensor(AlarmBaseSensor):
    """Sensor for last changed at."""

    _attr_icon = "mdi:clock-outline"
    _attr_device_class = SensorDeviceClass.TIMESTAMP

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry, alarm_entity_id: str) -> None:
        """Initialize the sensor."""
        super().__init__(hass, entry, alarm_entity_id)
        self._attr_unique_id = f"{entry.entry_id}_last_changed_at"
        self._attr_name = "Dernier changement"

    def _update_from_alarm(self) -> None:
        """Update from alarm entity."""
        alarm_state = self.hass.states.get(self._alarm_entity_id)
        if alarm_state:
            last_changed = alarm_state.attributes.get("last_changed_at")
            if last_changed:
                self._attr_native_value = last_changed
            else:
                self._attr_native_value = None
