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
from homeassistant.util import dt as dt_util

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the alarm control panel platform."""
    entity = AlarmePersonnaliseeEntity(hass, entry)
    async_add_entities([entity])
    
    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = entity

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
        self._last_triggered_by = None
        self._last_changed_at = None
        self._triggered_count = 0

        self._update_options()
        self._unsub_listener = None
        self._unsub_options_update_listener = entry.add_update_listener(
            self._options_update_listener
        )

    @callback
    def _update_options(self):
        """Update options from the config entry."""
        options = self._entry.options
        self._code = options.get("code", "")
        self._require_arm_code = options.get("require_arm_code", False)
        self._require_disarm_code = options.get("require_disarm_code", False)
        self._emergency_code = options.get("emergency_code", "")
        self._arming_time = max(0, options.get("arming_time", 30))
        self._delay_time = max(0, options.get("delay_time", 30))
        self._trigger_time = max(0, options.get("trigger_time", 180))
        self._rearm_after_trigger = options.get("rearm_after_trigger", False)

        self._away_sensors = options.get("away_sensors", [])
        self._home_sensors = options.get("home_sensors", [])
        self._vacation_sensors = options.get("vacation_sensors", [])

        self._all_sensors = list(set(self._away_sensors + self._home_sensors + self._vacation_sensors))

    async def _options_update_listener(self, hass: HomeAssistant, entry: ConfigEntry):
        """Handle options update."""
        self._cancel_timer()
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

    @property
    def extra_state_attributes(self) -> dict:
        """Return additional state attributes."""
        features = self.supported_features
        attrs = {
            "supported_features_list": [
                feature.name
                for feature in AlarmControlPanelEntityFeature
                # Skip the zero-value placeholder feature.
                if feature.value != 0 and features & feature
            ],
            "triggered_count": self._triggered_count,
        }
        
        if self._last_triggered_by:
            attrs["last_triggered_by"] = self._last_triggered_by
        
        if self._last_changed_at:
            attrs["last_changed_at"] = self._last_changed_at.isoformat()
            
        if self._last_armed_state:
            attrs["last_armed_state"] = self._last_armed_state
            
        attrs["monitored_sensors"] = {
            "away": self._away_sensors,
            "home": self._home_sensors,
            "vacation": self._vacation_sensors,
        }
        
        return attrs

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
        """Cancel the timer."""
        if self._timer_handle:
            self._timer_handle()  # This is a callable, not an object with a cancel method.
            self._timer_handle = None

    @callback
    def _sensor_state_changed(self, event: Event) -> None:
        """Handle sensor state changes."""
        new_state = event.data.get("new_state")
        if new_state is None or new_state.state != "on":
            return

        entity_id = event.data.get("entity_id")
        if not entity_id:
            _LOGGER.warning("Sensor state change event without entity_id")
            return

        # Surveiller les capteurs pendant l'armement ET quand armé
        if self._state not in [
            AlarmControlPanelState.ARMING,
            AlarmControlPanelState.ARMED_AWAY,
            AlarmControlPanelState.ARMED_HOME,
            AlarmControlPanelState.ARMED_VACATION,
        ]:
            return

        # Déterminer quels capteurs surveiller selon le mode cible
        if self._state == AlarmControlPanelState.ARMING:
            # En cours d'armement, vérifier selon le mode cible
            if self._last_armed_state == AlarmControlPanelState.ARMED_AWAY:
                is_relevant_sensor = entity_id in self._away_sensors
            elif self._last_armed_state == AlarmControlPanelState.ARMED_HOME:
                is_relevant_sensor = entity_id in self._home_sensors
            elif self._last_armed_state == AlarmControlPanelState.ARMED_VACATION:
                is_relevant_sensor = entity_id in self._vacation_sensors
            else:
                return
        else:
            # Déjà armé, vérifier selon l'état actuel
            is_relevant_sensor = (
                (self._state == AlarmControlPanelState.ARMED_AWAY and entity_id in self._away_sensors)
                or (self._state == AlarmControlPanelState.ARMED_HOME and entity_id in self._home_sensors)
                or (self._state == AlarmControlPanelState.ARMED_VACATION and entity_id in self._vacation_sensors)
            )

        if not is_relevant_sensor:
            return

        # Si on est en cours d'armement et qu'un capteur se déclenche, annuler l'armement
        if self._state == AlarmControlPanelState.ARMING:
            _LOGGER.warning("Arming cancelled: sensor %s triggered during arming delay", entity_id)
            self._cancel_timer()
            self._state = AlarmControlPanelState.DISARMED
            self._last_armed_state = None
            self.async_write_ha_state()
            
            # Émettre un événement personnalisé
            self.hass.bus.async_fire(
                f"{DOMAIN}.arming_cancelled",
                {
                    "entity_id": self.entity_id,
                    "cancelled_by": entity_id,
                    "timestamp": dt_util.utcnow().isoformat(),
                },
            )
            return

        # Sinon, comportement normal (passage en PENDING)
        _LOGGER.info("Alarm pending due to sensor %s", entity_id)
        self._last_triggered_by = entity_id
        self._state = AlarmControlPanelState.PENDING
        self._last_changed_at = dt_util.utcnow()
        self.async_write_ha_state()
        self._timer_handle = async_call_later(self.hass, self._delay_time, self._trigger_alarm)

    @callback
    def _trigger_alarm(self, now: datetime):
        """Trigger the alarm."""
        _LOGGER.warning("Alarm triggered!")
        self._state = AlarmControlPanelState.TRIGGERED
        self._triggered_count += 1
        self._last_changed_at = dt_util.utcnow()
        self.async_write_ha_state()
        
        self.hass.bus.async_fire(
            f"{DOMAIN}.triggered",
            {
                "entity_id": self.entity_id,
                "triggered_by": self._last_triggered_by,
                "timestamp": self._last_changed_at.isoformat(),
            },
        )
        
        self._timer_handle = async_call_later(self.hass, self._trigger_time, self._post_trigger_action)

    @callback
    def _post_trigger_action(self, now: datetime):
        """Action after trigger duration."""
        if self._rearm_after_trigger and self._last_armed_state:
            _LOGGER.info("Rearming alarm to %s", self._last_armed_state)
            self._state = self._last_armed_state
        else:
            _LOGGER.info("Disarming alarm after trigger.")
            self._state = AlarmControlPanelState.DISARMED
        self._last_changed_at = dt_util.utcnow()
        self.async_write_ha_state()

    async def async_alarm_disarm(self, code: str | None = None) -> None:
        """Send disarm command."""
        await self._perform_disarm(code)

    def _validate_disarm_code(self, code: str | None) -> tuple[bool, bool]:
        """Validate disarm code.

        Returns:
            tuple[bool, bool]: (is_valid, is_emergency) where is_emergency
            is True only when the emergency code matches.
        """
        if self._emergency_code and code == self._emergency_code:
            return True, True

        if self._require_disarm_code:
            if not self._code:
                _LOGGER.warning("Disarm requires a code, but none is set.")
                return False, False
            if code != self._code:
                _LOGGER.warning("Invalid code provided for disarming.")
                return False, False

        return True, False

    async def _perform_disarm(
        self, code: str | None = None, validation: tuple[bool, bool] | None = None
    ) -> None:
        """Handle disarm logic with validation.

        Args:
            code: The provided code to validate.
            validation: Optional pre-validated (is_valid, is_emergency) tuple
                to avoid re-validation when already performed by caller.
        """
        if self._state == AlarmControlPanelState.DISARMED:
            _LOGGER.info("Alarm is already disarmed. Ignoring disarm request.")
            return

        validation_result = (
            validation if validation is not None else self._validate_disarm_code(code)
        )
        is_valid, is_emergency = validation_result
        if not is_valid:
            return

        if is_emergency:
            _LOGGER.warning("Emergency code used to disarm alarm!")
            self.hass.bus.async_fire(f"{DOMAIN}.urgence", {"entity_id": self.entity_id})

        _LOGGER.info("Alarm disarmed from state: %s", self._state)
        self._state = AlarmControlPanelState.DISARMED
        self._last_armed_state = None
        self._last_triggered_by = None
        self._last_changed_at = dt_util.utcnow()
        self._cancel_timer()
        self.async_write_ha_state()

    async def _arm(self, state: AlarmControlPanelState, code: str | None = None):
        """Arm the alarm to the specified state.
        
        Args:
            state: The target armed state (ARMED_HOME, ARMED_AWAY, or ARMED_VACATION)
            code: Optional code for arming (if required)
            
        Returns:
            None. State changes are reflected in self._state and logged.
            
        State validations:
            - Prevents arming if already in the requested state
            - Prevents arming while in ARMING, PENDING, or TRIGGERED states
            - Validates code if required
        """
        # Check if already armed in the requested state
        if self._state == state:
            _LOGGER.info("Alarm is already armed in %s mode. Toggling to disarm.", state)
            is_valid, is_emergency = self._validate_disarm_code(code)
            if not is_valid:
                return
            await self._perform_disarm(code, (is_valid, is_emergency))
            return

        # Prevent arming while in ARMING state
        if self._state == AlarmControlPanelState.ARMING:
            _LOGGER.warning("Alarm is currently arming. Please wait for arming to complete.")
            return

        # Prevent arming while in PENDING state
        if self._state == AlarmControlPanelState.PENDING:
            _LOGGER.warning("Alarm is in PENDING state. Cannot arm now.")
            return

        # Prevent arming while in TRIGGERED state
        if self._state == AlarmControlPanelState.TRIGGERED:
            _LOGGER.warning("Alarm is TRIGGERED. Disarm the alarm first before arming again.")
            return

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
        self._last_changed_at = dt_util.utcnow()
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
