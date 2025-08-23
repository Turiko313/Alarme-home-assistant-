"""Platform for alarm control panel integration."""
from __future__ import annotations

import logging
from datetime import datetime, timedelta

from homeassistant.components.alarm_control_panel import (
    AlarmControlPanelEntity,
    AlarmControlPanelEntityFeature,
    CodeFormat,
)
from homeassistant.components.alarm_control_panel.const import AlarmControlPanelState
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import Event, HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.event import async_call_later, async_track_state_change_event

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the alarm control panel platform."""
    async_add_entities([AlarmePersonnaliseeEntity(hass, entry)])


class AlarmePersonnaliseeEntity(AlarmControlPanelEntity):
    """Representation of an Alarme Personnalisée."""

    _attr_has_entity_name = True

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        """Initialize the alarm control panel."""
        self.hass = hass
        self._entry = entry
        self._attr_unique_id = entry.entry_id
        self._attr_name = "Alarme"
        self._state = AlarmControlPanelState.DISARMED
        self._last_armed_state = None
        self._timer_handle = None

        self._update_options()
        self._unsub_listener = None
        self._unsub_options_update_listener = entry.add_update_listener(
            self._options_update_listener
        )

    @callback
    def _update_options(self):
        """Update options from the config entry."""
        options = self._entry.options
        data = self._entry.data
        self._code = options.get("code", "")
        self._require_arm_code = options.get("require_arm_code", False)
        self._require_disarm_code = options.get("require_disarm_code", True)
        self._emergency_code = options.get("emergency_code", "")
        self._arming_time = options.get("arming_time", 30)
        self._delay_time = options.get("delay_time", 30)
        self._trigger_time = options.get("trigger_time", 180)
        self._rearm_after_trigger = options.get("rearm_after_trigger", False)
        self._trigger_actions = options.get("trigger_actions", [])

        self._away_sensors = options.get("away_sensors", data.get("away_sensors", []))
        self._home_sensors = options.get("home_sensors", data.get("home_sensors", []))
        self._vacation_sensors = options.get("vacation_sensors", data.get("vacation_sensors", []))

        self._all_sensors = list(set(self._away_sensors + self._home_sensors + self._vacation_sensors))

    async def _options_update_listener(self, hass: HomeAssistant, entry: ConfigEntry):
        """Handle options update."""
        self._update_options()
        if self._unsub_listener:
            self._unsub_listener()
        self._unsub_listener = async_track_state_change_event(
            self.hass, self._all_sensors, self._sensor_state_changed
        )
        self.async_write_ha_state()

    @property
    def state(self) -> str | None:
        """Return the state of the entity."""
        return self._state

    @property
    def code_format(self) -> CodeFormat | None:
        """Return the code format."""
        return CodeFormat.NUMBER if self._code else None

    @property
    def code_arm_required(self) -> bool:
        """Whether the code is required for arming."""
        return self._require_arm_code

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
        self._unsub_options_update_listener()
        if self._unsub_listener:
            self._unsub_listener()
        self._cancel_timer()

    def _cancel_timer(self):
        if self._timer_handle:
            self._timer_handle.cancel()
            self._timer_handle = None

    @callback
    def _sensor_state_changed(self, event: Event) -> None:
        """Handle sensor state changes."""
        new_state = event.data.get("new_state")
        if new_state is None or new_state.state != "on":
            return

        entity_id = event.data.get("entity_id")

        if self._state not in [
            AlarmControlPanelState.ARMED_AWAY,
            AlarmControlPanelState.ARMED_HOME,
            AlarmControlPanelState.ARMED_VACATION,
        ]:
            return

        is_relevant_sensor = (
            (self._state == AlarmControlPanelState.ARMED_AWAY and entity_id in self._away_sensors)
            or (self._state == AlarmControlPanelState.ARMED_HOME and entity_id in self._home_sensors)
            or (self._state == AlarmControlPanelState.ARMED_VACATION and entity_id in self._vacation_sensors)
        )

        if not is_relevant_sensor:
            return

        _LOGGER.info("Alarm pending due to sensor %s", entity_id)
        self._state = AlarmControlPanelState.PENDING
        self.async_write_ha_state()
        self._timer_handle = async_call_later(self.hass, self._delay_time, self._trigger_alarm)

    @callback
    def _trigger_alarm(self, now: datetime):
        """Trigger the alarm."""
        _LOGGER.warning("Alarm triggered!")
        self._state = AlarmControlPanelState.TRIGGERED
        self.hass.async_create_task(self._async_execute_actions("turn_on"))
        self.async_write_ha_state()
        self._timer_handle = async_call_later(self.hass, self._trigger_time, self._post_trigger_action)

    @callback
    def _post_trigger_action(self, now: datetime):
        """Action after trigger duration."""
        self.hass.async_create_task(self._async_execute_actions("turn_off"))
        if self._rearm_after_trigger and self._last_armed_state:
            _LOGGER.info("Rearming alarm to %s", self._last_armed_state)
            self._state = self._last_armed_state
        else:
            _LOGGER.info("Disarming alarm after trigger.")
            self._state = AlarmControlPanelState.DISARMED
        self.async_write_ha_state()

    async def _async_execute_actions(self, service: str):
        """Execute the trigger actions."""
        if not self._trigger_actions:
            return

        _LOGGER.info("Executing %s on trigger actions", service)
        await self.hass.services.async_call(
            "homeassistant",
            service,
            {"entity_id": self._trigger_actions},
            blocking=False,
        )

    async def async_alarm_disarm(self, code: str | None = None) -> None:
        """Send disarm command."""
        # Check for emergency code first
        if self._emergency_code and code == self._emergency_code:
            _LOGGER.warning("Emergency code used to disarm alarm!")
            self.hass.bus.async_fire(f"{DOMAIN}.urgence", {"entity_id": self.entity_id})
            # Disarm without further checks

        # Check for regular code if required
        elif self._require_disarm_code:
            if not self._code:
                _LOGGER.warning("Disarm requires a code, but none is set.")
                return
            if code != self._code:
                _LOGGER.warning("Invalid code provided for disarming.")
                return

        # If we reach here, disarming is successful
        if self._state == AlarmControlPanelState.TRIGGERED:
            self.hass.async_create_task(self._async_execute_actions("turn_off"))

        _LOGGER.info("Alarm disarmed")
        self._state = AlarmControlPanelState.DISARMED
        self._last_armed_state = None
        self._cancel_timer()
        self.async_write_ha_state()

    async def _arm(self, state: str, code: str | None = None):
        if self._require_arm_code:
            if not self._code:
                _LOGGER.warning("Arming requires a code, but none is set.")
                return
            if code != self._code:
                _LOGGER.warning("Invalid code provided for arming.")
                return

        self._cancel_timer()
        self._last_armed_state = state
        _LOGGER.info("Alarm arming to %s in %s seconds", state, self._arming_time)
        self._state = AlarmControlPanelState.ARMING
        self.async_write_ha_state()
        self._timer_handle = async_call_later(self.hass, self._arming_time, self._finish_arming)

    @callback
    def _finish_arming(self, now: datetime):
        _LOGGER.info("Alarm armed to %s", self._last_armed_state)
        self._state = self._last_armed_state
        self.async_write_ha_state()

    async def async_alarm_arm_home(self, code: str | None = None) -> None:
        """Send arm home command."""
        await self._arm(AlarmControlPanelState.ARMED_HOME, code)

    async def async_alarm_arm_away(self, code: str | None = None) -> None:
        """Send arm away command."""
        await self._arm(AlarmControlPanelState.ARMED_AWAY, code)

    async def async_alarm_arm_vacation(self, code: str | None = None) -> None:
        """Send arm vacation command."""
        await self._arm(AlarmControlPanelState.ARMED_VACATION, code)
