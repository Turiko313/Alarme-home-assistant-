"""Platform for alarm control panel integration."""
from __future__ import annotations

import logging

from homeassistant.components.alarm_control_panel import (
    AlarmControlPanelEntity,
    AlarmControlPanelEntityFeature,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    STATE_ALARM_ARMED_AWAY,
    STATE_ALARM_ARMED_HOME,
    STATE_ALARM_ARMED_VACATION,
    STATE_ALARM_DISARMED,
    STATE_ALARM_TRIGGERED,
)
from homeassistant.core import Event, HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.event import async_track_state_change_event

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the alarm control panel platform."""
    async_add_entities([AlarmePersonnaliseeEntity(entry)])


class AlarmePersonnaliseeEntity(AlarmControlPanelEntity):
    """Representation of an Alarme Personnalisée."""

    _attr_has_entity_name = True

    def __init__(self, entry: ConfigEntry) -> None:
        """Initialize the alarm control panel."""
        self._entry = entry
        self._attr_unique_id = entry.entry_id
        self._attr_name = "Alarme"
        self._state = STATE_ALARM_DISARMED

        # Get sensor lists from config entry
        self._away_sensors = self._entry.data.get("away_sensors", [])
        self._home_sensors = self._entry.data.get("home_sensors", [])
        self._vacation_sensors = self._entry.data.get("vacation_sensors", [])

        # Combine all sensors into one list for the listener
        self._all_sensors = list(
            set(self._away_sensors + self._home_sensors + self._vacation_sensors)
        )
        self._unsub_listener = None

    @property
    def state(self) -> str | None:
        """Return the state of the entity."""
        return self._state

    @property
    def supported_features(self) -> AlarmControlPanelEntityFeature:
        """Return the list of supported features."""
        return (
            AlarmControlPanelEntityFeature.ARM_HOME
            | AlarmControlPanelEntityFeature.ARM_AWAY
            | AlarmControlPanelEntityFeature.ARM_VACATION
        )

    async def async_added_to_hass(self) -> None:
        """Run when entity about to be added to hass."""
        await super().async_added_to_hass()
        self._unsub_listener = async_track_state_change_event(
            self.hass, self._all_sensors, self._sensor_state_changed
        )

    async def async_will_remove_from_hass(self) -> None:
        """Run when entity will be removed from hass."""
        await super().async_will_remove_from_hass()
        if self._unsub_listener:
            self._unsub_listener()

    @callback
    def _sensor_state_changed(self, event: Event) -> None:
        """Handle sensor state changes."""
        new_state = event.data.get("new_state")
        if new_state is None or new_state.state != "on":
            return

        entity_id = event.data.get("entity_id")

        if self._state == STATE_ALARM_DISARMED:
            return

        triggered = False
        if self._state == STATE_ALARM_ARMED_AWAY and entity_id in self._away_sensors:
            _LOGGER.info("Alarm triggered by %s in away mode", entity_id)
            triggered = True
        elif self._state == STATE_ALARM_ARMED_HOME and entity_id in self._home_sensors:
            _LOGGER.info("Alarm triggered by %s in home mode", entity_id)
            triggered = True
        elif self._state == STATE_ALARM_ARMED_VACATION and entity_id in self._vacation_sensors:
            _LOGGER.info("Alarm triggered by %s in vacation mode", entity_id)
            triggered = True

        if triggered:
            self._state = STATE_ALARM_TRIGGERED
            self.async_write_ha_state()

    async def async_alarm_disarm(self, code: str | None = None) -> None:
        """Send disarm command."""
        self._state = STATE_ALARM_DISARMED
        self.async_write_ha_state()

    async def async_alarm_arm_home(self, code: str | None = None) -> None:
        """Send arm home command."""
        self._state = STATE_ALARM_ARMED_HOME
        self.async_write_ha_state()

    async def async_alarm_arm_away(self, code: str | None = None) -> None:
        """Send arm away command."""
        self._state = STATE_ALARM_ARMED_AWAY
        self.async_write_ha_state()

    async def async_alarm_arm_vacation(self, code: str | None = None) -> None:
        """Send arm vacation command."""
        self._state = STATE_ALARM_ARMED_VACATION
        self.async_write_ha_state()
