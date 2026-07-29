"""Alarm control panel platform for Alarme Personnalisée."""

from __future__ import annotations

import logging
from datetime import datetime
from typing import Any

from homeassistant.components.alarm_control_panel import (
    AlarmControlPanelEntity,
    AlarmControlPanelEntityFeature,
    CodeFormat,
)
from homeassistant.components.alarm_control_panel.const import AlarmControlPanelState
from homeassistant.components.persistent_notification import (
    async_create as async_create_persistent_notification,
)
from homeassistant.components.tag.const import (
    DEVICE_ID as TAG_DEVICE_ID,
)
from homeassistant.components.tag.const import (
    EVENT_TAG_SCANNED,
    TAG_ID,
)
from homeassistant.const import (
    ATTR_FRIENDLY_NAME,
    STATE_OFF,
    STATE_ON,
    STATE_UNAVAILABLE,
    STATE_UNKNOWN,
)
from homeassistant.core import CALLBACK_TYPE, Event, HomeAssistant, State, callback
from homeassistant.helpers import issue_registry as ir
from homeassistant.helpers.dispatcher import async_dispatcher_send
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.event import async_call_later, async_track_state_change_event
from homeassistant.helpers.restore_state import RestoreEntity
from homeassistant.helpers.start import async_at_start
from homeassistant.util import dt as dt_util

from .const import (
    ATTR_BADGE_ENTITY,
    ATTR_BADGE_NAME,
    ATTR_BADGE_VALUE,
    ATTR_BYPASSED_SENSORS,
    ATTR_LAST_ARMED_STATE,
    ATTR_LAST_CHANGED_AT,
    ATTR_MONITORED_SENSORS,
    ATTR_TAG_DEVICE_ID,
    ATTR_TAG_ID,
    ATTR_TAG_NAME,
    ATTR_TRIGGERED_BY,
    ATTR_TRIGGERED_BY_NAME,
    ATTR_TRIGGERED_COUNT,
    CONF_ARM_HOME_ON_START,
    CONF_ARMING_TIME,
    CONF_AWAY_SENSORS,
    CONF_BADGE_ENTITY,
    CONF_BADGE_NAME,
    CONF_BADGE_VALUE,
    CONF_BADGES,
    CONF_CODE,
    CONF_DELAY_TIME,
    CONF_EMERGENCY_CODE,
    CONF_HOME_SENSORS,
    CONF_REARM_AFTER_TRIGGER,
    CONF_REQUIRE_ARM_CODE,
    CONF_REQUIRE_DISARM_CODE,
    CONF_STARTUP_DELAY,
    CONF_TAG_ID,
    CONF_TAG_NAME,
    CONF_TRIGGER_TIME,
    CONF_VACATION_SENSORS,
    DEFAULT_ARM_HOME_ON_START,
    DEFAULT_ARMING_TIME,
    DEFAULT_CODE,
    DEFAULT_DELAY_TIME,
    DEFAULT_STARTUP_DELAY,
    DEFAULT_TRIGGER_TIME,
    DOMAIN,
    EVENT_ALARM_ARMED,
    EVENT_ALARM_DISARMED,
    EVENT_ALARM_TRIGGERED,
    EVENT_BADGE_DISARM,
    EVENT_BYPASSED_SENSORS_CHANGED,
    EVENT_EMERGENCY_DISARM,
    EVENT_SENSOR_AVAILABILITY_CHANGED,
    ISSUE_BYPASSED_SENSORS,
    ISSUE_UNAVAILABLE_SENSORS,
    SIGNAL_STATE_UPDATED,
)
from .entity import alarm_device_info
from .runtime_data import AlarmConfigEntry

_LOGGER = logging.getLogger(__name__)

ARMED_STATES = {
    AlarmControlPanelState.ARMED_AWAY,
    AlarmControlPanelState.ARMED_HOME,
    AlarmControlPanelState.ARMED_VACATION,
}


async def async_setup_entry(
    hass: HomeAssistant,
    entry: AlarmConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the alarm control panel platform."""
    entity = AlarmePersonnaliseeEntity(hass, entry)
    entry.runtime_data.alarm = entity
    async_add_entities([entity])


class AlarmePersonnaliseeEntity(AlarmControlPanelEntity, RestoreEntity):
    """Representation of an Alarme Personnalisée alarm."""

    _attr_has_entity_name = True
    _attr_name = None
    _attr_supported_features = (
        AlarmControlPanelEntityFeature.ARM_HOME
        | AlarmControlPanelEntityFeature.ARM_AWAY
        | AlarmControlPanelEntityFeature.ARM_VACATION
    )

    def __init__(self, hass: HomeAssistant, entry: AlarmConfigEntry) -> None:
        """Initialize the alarm control panel."""
        self.hass = hass
        self._entry = entry
        self._attr_unique_id = entry.entry_id
        self._attr_alarm_state = AlarmControlPanelState.DISARMED
        self._last_armed_state: AlarmControlPanelState | None = None
        self._timer_handle: CALLBACK_TYPE | None = None
        self._last_triggered_by: str | None = None
        self._last_triggered_by_name: str | None = None
        self._last_changed_at: datetime | None = None
        self._triggered_count = 0
        self._unsub_sensor_listener: CALLBACK_TYPE | None = None
        self._unsub_badge_listener: CALLBACK_TYPE | None = None
        self._unsub_tag_listener: CALLBACK_TYPE | None = None
        self._unsub_start_listener: CALLBACK_TYPE | None = None
        self._startup_timer_handle: CALLBACK_TYPE | None = None
        self._startup_ready = False
        self._startup_state_touched = False
        self._unavailable_sensors: set[str] = set()
        self._bypassed_sensors: set[str] = set()
        self._update_options()
        self._unsub_options_update_listener = entry.add_update_listener(
            self._options_update_listener
        )

    @property
    def device_info(self) -> DeviceInfo:
        """Return the device information."""
        return alarm_device_info(self._entry)

    @property
    def alarm_state(self) -> AlarmControlPanelState:
        """Return the current alarm state."""
        return self._attr_alarm_state

    @property
    def code_format(self) -> CodeFormat | None:
        """Return the code format required by the configured codes."""
        codes = [code for code in (self._code, self._emergency_code) if code]
        if not codes:
            return None
        return (
            CodeFormat.NUMBER
            if all(code.isdigit() for code in codes)
            else CodeFormat.TEXT
        )

    @property
    def code_arm_required(self) -> bool:
        """Return whether a code is required for arming."""
        return self._require_arm_code

    @property
    def triggered_count(self) -> int:
        """Return the number of alarm triggers."""
        return self._triggered_count

    @property
    def last_triggered_by(self) -> str | None:
        """Return the entity that most recently triggered the alarm."""
        return self._last_triggered_by

    @property
    def last_triggered_by_name(self) -> str | None:
        """Return the friendly name of the entity that triggered the alarm."""
        if self._last_triggered_by_name is not None:
            return self._last_triggered_by_name
        if self._last_triggered_by is None:
            return None
        if state := self.hass.states.get(self._last_triggered_by):
            return state.name
        return self._last_triggered_by

    @property
    def last_changed_at(self) -> datetime | None:
        """Return the time of the latest alarm transition."""
        return self._last_changed_at

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return additional state attributes."""
        attributes: dict[str, Any] = {
            ATTR_TRIGGERED_COUNT: self._triggered_count,
            ATTR_MONITORED_SENSORS: {
                "away": self._away_sensors,
                "home": self._home_sensors,
                "vacation": self._vacation_sensors,
            },
            ATTR_BYPASSED_SENSORS: sorted(self._bypassed_sensors),
            "configured_badges": len(self._badges),
        }
        if self._last_triggered_by:
            attributes[ATTR_TRIGGERED_BY] = self._last_triggered_by
            attributes[ATTR_TRIGGERED_BY_NAME] = self.last_triggered_by_name
        if self._last_changed_at:
            attributes[ATTR_LAST_CHANGED_AT] = self._last_changed_at.isoformat()
        if self._last_armed_state:
            attributes[ATTR_LAST_ARMED_STATE] = self._last_armed_state
        return attributes

    @callback
    def _update_options(self) -> None:
        """Update cached options from the config entry."""
        options = self._entry.options
        self._code = str(options.get(CONF_CODE, DEFAULT_CODE))
        self._require_arm_code = bool(options.get(CONF_REQUIRE_ARM_CODE, False))
        self._require_disarm_code = bool(options.get(CONF_REQUIRE_DISARM_CODE, False))
        self._emergency_code = str(options.get(CONF_EMERGENCY_CODE, DEFAULT_CODE))
        self._arming_time = max(
            0, int(options.get(CONF_ARMING_TIME, DEFAULT_ARMING_TIME))
        )
        self._delay_time = max(0, int(options.get(CONF_DELAY_TIME, DEFAULT_DELAY_TIME)))
        self._trigger_time = max(
            0, int(options.get(CONF_TRIGGER_TIME, DEFAULT_TRIGGER_TIME))
        )
        self._rearm_after_trigger = bool(options.get(CONF_REARM_AFTER_TRIGGER, False))
        self._startup_delay = max(
            0, int(options.get(CONF_STARTUP_DELAY, DEFAULT_STARTUP_DELAY))
        )
        self._arm_home_on_start = bool(
            options.get(CONF_ARM_HOME_ON_START, DEFAULT_ARM_HOME_ON_START)
        )

        self._badges = [
            badge
            for badge in options.get(CONF_BADGES, [])
            if CONF_BADGE_NAME in badge
            and (CONF_TAG_ID in badge or CONF_BADGE_ENTITY in badge)
        ]
        self._tag_badges = [badge for badge in self._badges if CONF_TAG_ID in badge]
        self._entity_badges = [
            badge for badge in self._badges if CONF_BADGE_ENTITY in badge
        ]
        self._badge_entities = list(
            dict.fromkeys(badge[CONF_BADGE_ENTITY] for badge in self._entity_badges)
        )
        self._away_sensors = list(options.get(CONF_AWAY_SENSORS, []))
        self._home_sensors = list(options.get(CONF_HOME_SENSORS, []))
        self._vacation_sensors = list(options.get(CONF_VACATION_SENSORS, []))
        self._all_sensors = list(
            dict.fromkeys(
                self._away_sensors + self._home_sensors + self._vacation_sensors
            )
        )

    async def _options_update_listener(
        self, hass: HomeAssistant, entry: AlarmConfigEntry
    ) -> None:
        """Handle an options update without interrupting an active timer."""
        self._update_options()
        if not self._startup_ready:
            target_state = None
        elif self.alarm_state == AlarmControlPanelState.ARMING:
            target_state = self._last_armed_state
        elif self.alarm_state in ARMED_STATES:
            target_state = self.alarm_state
        else:
            target_state = None

        bypassed_sensors = self._bypassed_sensors.intersection(self._all_sensors)
        if target_state is not None:
            bypassed_sensors |= self._problematic_sensors_for_mode(target_state)
        self._set_bypassed_sensors(bypassed_sensors)
        self._subscribe_to_state_changes()
        self._update_sensor_repairs()
        self._write_state()

    async def async_added_to_hass(self) -> None:
        """Subscribe when the entity is added to Home Assistant."""
        await super().async_added_to_hass()
        await self._async_restore_state()
        self._subscribe_to_state_changes()
        self._unsub_start_listener = async_at_start(
            self.hass, self._schedule_startup_check
        )
        async_dispatcher_send(
            self.hass, f"{SIGNAL_STATE_UPDATED}_{self._entry.entry_id}"
        )

    async def async_will_remove_from_hass(self) -> None:
        """Clean up subscriptions and timers."""
        await super().async_will_remove_from_hass()
        self._unsub_options_update_listener()
        self._unsubscribe_state_changes()
        if self._unsub_start_listener:
            self._unsub_start_listener()
            self._unsub_start_listener = None
        if self._startup_timer_handle:
            self._startup_timer_handle()
            self._startup_timer_handle = None
        self._cancel_timer()
        ir.async_delete_issue(self.hass, DOMAIN, self._unavailable_sensors_issue_id)
        ir.async_delete_issue(self.hass, DOMAIN, self._bypassed_sensors_issue_id)
        if self._entry.runtime_data.alarm is self:
            self._entry.runtime_data.alarm = None

    @callback
    def _subscribe_to_state_changes(self) -> None:
        """Refresh state-change subscriptions."""
        self._unsubscribe_state_changes()
        if self._all_sensors:
            self._unsub_sensor_listener = async_track_state_change_event(
                self.hass, self._all_sensors, self._sensor_state_changed
            )
        if self._badge_entities:
            self._unsub_badge_listener = async_track_state_change_event(
                self.hass, self._badge_entities, self._badge_state_changed
            )
        if self._tag_badges:
            self._unsub_tag_listener = self.hass.bus.async_listen(
                EVENT_TAG_SCANNED, self._tag_scanned
            )

    @property
    def _unavailable_sensors_issue_id(self) -> str:
        """Return the Repairs issue ID for this alarm."""
        return f"{ISSUE_UNAVAILABLE_SENSORS}_{self._entry.entry_id}"

    @property
    def _bypassed_sensors_issue_id(self) -> str:
        """Return the Repairs issue ID for bypassed alarm zones."""
        return f"{ISSUE_BYPASSED_SENSORS}_{self._entry.entry_id}"

    async def _async_restore_state(self) -> None:
        """Restore the armed mode and trigger metadata after restart."""
        last_state = await self.async_get_last_state()
        if last_state is None:
            return

        restored_count = last_state.attributes.get(ATTR_TRIGGERED_COUNT, 0)
        try:
            self._triggered_count = max(0, int(restored_count))
        except (TypeError, ValueError):
            self._triggered_count = 0

        restored_last_mode = last_state.attributes.get(ATTR_LAST_ARMED_STATE)
        try:
            last_mode = AlarmControlPanelState(restored_last_mode)
        except (TypeError, ValueError):
            last_mode = None
        if last_mode in ARMED_STATES:
            self._last_armed_state = last_mode

        try:
            restored_state = AlarmControlPanelState(last_state.state)
        except ValueError:
            restored_state = AlarmControlPanelState.DISARMED

        if restored_state in ARMED_STATES:
            self._attr_alarm_state = restored_state
            self._last_armed_state = restored_state
        elif (
            restored_state
            in {
                AlarmControlPanelState.ARMING,
                AlarmControlPanelState.PENDING,
                AlarmControlPanelState.TRIGGERED,
            }
            and self._last_armed_state in ARMED_STATES
        ):
            # Timers cannot be safely resumed after a restart. Restore the
            # protected armed mode instead of a transient state.
            self._attr_alarm_state = self._last_armed_state
        else:
            self._attr_alarm_state = AlarmControlPanelState.DISARMED

        self._last_triggered_by = last_state.attributes.get(ATTR_TRIGGERED_BY)
        self._last_triggered_by_name = last_state.attributes.get(ATTR_TRIGGERED_BY_NAME)
        restored_changed_at = last_state.attributes.get(ATTR_LAST_CHANGED_AT)
        if isinstance(restored_changed_at, str):
            self._last_changed_at = dt_util.parse_datetime(restored_changed_at)

    @callback
    def _schedule_startup_check(self, hass: HomeAssistant) -> None:
        """Wait for integrations and devices to restore their states."""
        self._unsub_start_listener = None
        self._startup_timer_handle = async_call_later(
            self.hass,
            self._startup_delay,
            self._finish_startup,
        )

    @callback
    def _finish_startup(self, now: datetime) -> None:
        """Enable monitoring and apply the configured startup alarm mode."""
        if self._startup_ready:
            return
        if self._startup_timer_handle:
            self._startup_timer_handle()
            self._startup_timer_handle = None

        self._startup_ready = True
        self._update_sensor_repairs()
        if self.alarm_state in ARMED_STATES:
            self._set_bypassed_sensors(
                self._problematic_sensors_for_mode(self.alarm_state)
            )
            self._write_state()
        elif (
            self.alarm_state == AlarmControlPanelState.DISARMED
            and self._arm_home_on_start
            and not self._startup_state_touched
        ):
            self.hass.async_create_task(
                self._arm(AlarmControlPanelState.ARMED_HOME, skip_code=True)
            )

    @callback
    def _update_sensor_repairs(self) -> None:
        """Create or clear a Repairs issue for unavailable security sensors."""
        if not self._startup_ready:
            return
        configured_entities = set(self._all_sensors) | set(self._badge_entities)
        unavailable = {
            entity_id
            for entity_id in configured_entities
            if (state := self.hass.states.get(entity_id)) is None
            or state.state in {STATE_UNAVAILABLE, STATE_UNKNOWN}
        }
        if unavailable == self._unavailable_sensors:
            return

        self._unavailable_sensors = unavailable
        if unavailable:
            sensor_list = "\n".join(
                f"- `{entity_id}`" for entity_id in sorted(unavailable)
            )
            ir.async_create_issue(
                self.hass,
                DOMAIN,
                self._unavailable_sensors_issue_id,
                is_fixable=False,
                is_persistent=False,
                severity=ir.IssueSeverity.ERROR,
                translation_key=ISSUE_UNAVAILABLE_SENSORS,
                translation_placeholders={
                    "alarm_name": self._entry.title,
                    "sensors": sensor_list,
                },
            )
        else:
            ir.async_delete_issue(self.hass, DOMAIN, self._unavailable_sensors_issue_id)

        self.hass.bus.async_fire(
            EVENT_SENSOR_AVAILABILITY_CHANGED,
            {
                "entity_id": self.entity_id,
                "alarm_name": self._entry.title,
                "available": not unavailable,
                "unavailable_sensors": sorted(unavailable),
                "timestamp": dt_util.utcnow().isoformat(),
            },
        )

    def _problematic_sensors_for_mode(self, state: AlarmControlPanelState) -> set[str]:
        """Return zones that are not closed and cannot initially protect the mode."""
        return {
            entity_id
            for entity_id in self._sensors_for_mode(state)
            if (sensor_state := self.hass.states.get(entity_id)) is None
            or sensor_state.state != STATE_OFF
        }

    @callback
    def _set_bypassed_sensors(self, sensors: set[str]) -> None:
        """Update temporary zone bypasses, the Repairs issue, and the event."""
        if sensors == self._bypassed_sensors:
            return

        self._bypassed_sensors = set(sensors)
        sensor_states = {
            entity_id: (
                state.state
                if (state := self.hass.states.get(entity_id)) is not None
                else "missing"
            )
            for entity_id in sorted(sensors)
        }
        if sensors:
            sensor_list = "\n".join(
                f"- `{entity_id}` ({sensor_states[entity_id]})"
                for entity_id in sorted(sensors)
            )
            ir.async_create_issue(
                self.hass,
                DOMAIN,
                self._bypassed_sensors_issue_id,
                is_fixable=False,
                is_persistent=False,
                severity=ir.IssueSeverity.WARNING,
                translation_key=ISSUE_BYPASSED_SENSORS,
                translation_placeholders={
                    "alarm_name": self._entry.title,
                    "sensors": sensor_list,
                },
            )
        else:
            ir.async_delete_issue(self.hass, DOMAIN, self._bypassed_sensors_issue_id)

        self.hass.bus.async_fire(
            EVENT_BYPASSED_SENSORS_CHANGED,
            {
                "entity_id": self.entity_id,
                "alarm_name": self._entry.title,
                ATTR_BYPASSED_SENSORS: sorted(sensors),
                "sensor_states": sensor_states,
                "timestamp": dt_util.utcnow().isoformat(),
            },
        )

    @callback
    def _unsubscribe_state_changes(self) -> None:
        """Remove state-change subscriptions."""
        if self._unsub_sensor_listener:
            self._unsub_sensor_listener()
            self._unsub_sensor_listener = None
        if self._unsub_badge_listener:
            self._unsub_badge_listener()
            self._unsub_badge_listener = None
        if self._unsub_tag_listener:
            self._unsub_tag_listener()
            self._unsub_tag_listener = None

    @callback
    def _write_state(self) -> None:
        """Write the entity and notify its diagnostic sensors."""
        self.async_write_ha_state()
        async_dispatcher_send(
            self.hass, f"{SIGNAL_STATE_UPDATED}_{self._entry.entry_id}"
        )

    @callback
    def reset_trigger_count(self) -> None:
        """Reset the trigger counter."""
        self._triggered_count = 0
        self._write_state()

    @callback
    def _cancel_timer(self) -> None:
        """Cancel the active transition timer."""
        if self._timer_handle:
            self._timer_handle()
            self._timer_handle = None

    def _sensors_for_mode(self, state: AlarmControlPanelState) -> list[str]:
        """Return sensors monitored in an armed mode."""
        if state == AlarmControlPanelState.ARMED_AWAY:
            return self._away_sensors
        if state == AlarmControlPanelState.ARMED_HOME:
            return self._home_sensors
        if state == AlarmControlPanelState.ARMED_VACATION:
            return self._vacation_sensors
        return []

    @staticmethod
    def _is_badge_match(badge: dict[str, Any], new_state: State) -> bool:
        """Return whether a reader state matches one configured badge."""
        expected_value = badge.get(CONF_BADGE_VALUE)
        if expected_value is not None and str(expected_value):
            return new_state.state == str(expected_value)

        # Compatibility for old configurations: a dedicated binary sensor can
        # safely represent one badge, but arbitrary sensor value changes cannot.
        return (
            new_state.entity_id.startswith("binary_sensor.")
            and new_state.state == STATE_ON
        )

    @callback
    def _badge_state_changed(self, event: Event) -> None:
        """Disarm when a configured reader reports an authorized badge."""
        if not self._startup_ready:
            return
        self._update_sensor_repairs()
        new_state: State | None = event.data.get("new_state")
        old_state: State | None = event.data.get("old_state")
        entity_id: str | None = event.data.get("entity_id")
        if (
            new_state is None
            or entity_id is None
            or (old_state is not None and new_state.state == old_state.state)
            or self.alarm_state
            not in {
                *ARMED_STATES,
                AlarmControlPanelState.ARMING,
                AlarmControlPanelState.PENDING,
                AlarmControlPanelState.TRIGGERED,
            }
        ):
            return

        badge = next(
            (
                badge
                for badge in self._entity_badges
                if badge[CONF_BADGE_ENTITY] == entity_id
                and self._is_badge_match(badge, new_state)
            ),
            None,
        )
        if badge is None:
            return

        timestamp = dt_util.utcnow()
        self.hass.bus.async_fire(
            EVENT_BADGE_DISARM,
            {
                "entity_id": self.entity_id,
                ATTR_BADGE_NAME: badge[CONF_BADGE_NAME],
                ATTR_BADGE_ENTITY: entity_id,
                ATTR_BADGE_VALUE: new_state.state,
                "timestamp": timestamp.isoformat(),
            },
        )
        self.hass.async_create_task(self._perform_disarm(validation=(True, False)))

    @callback
    def _tag_scanned(self, event: Event) -> None:
        """Disarm when Home Assistant reports an authorized native tag."""
        if not self._startup_ready or self.alarm_state not in {
            *ARMED_STATES,
            AlarmControlPanelState.ARMING,
            AlarmControlPanelState.PENDING,
            AlarmControlPanelState.TRIGGERED,
        }:
            return

        tag_id = event.data.get(TAG_ID)
        if not isinstance(tag_id, str):
            return
        badge = next(
            (badge for badge in self._tag_badges if badge[CONF_TAG_ID] == tag_id),
            None,
        )
        if badge is None:
            return

        timestamp = dt_util.utcnow()
        tag_name = event.data.get("name") or badge.get(CONF_TAG_NAME) or f"Tag {tag_id}"
        self.hass.bus.async_fire(
            EVENT_BADGE_DISARM,
            {
                "entity_id": self.entity_id,
                ATTR_BADGE_NAME: badge[CONF_BADGE_NAME],
                ATTR_TAG_ID: tag_id,
                ATTR_TAG_NAME: tag_name,
                ATTR_TAG_DEVICE_ID: event.data.get(TAG_DEVICE_ID),
                "timestamp": timestamp.isoformat(),
            },
        )
        self.hass.async_create_task(self._perform_disarm(validation=(True, False)))

    @callback
    def _sensor_state_changed(self, event: Event) -> None:
        """Handle bypass recovery and monitored sensor activation."""
        if not self._startup_ready:
            return
        self._update_sensor_repairs()
        new_state: State | None = event.data.get("new_state")
        old_state: State | None = event.data.get("old_state")
        entity_id: str | None = event.data.get("entity_id")
        if entity_id is None:
            return

        current_state = self.alarm_state
        if current_state == AlarmControlPanelState.ARMING:
            target_state = self._last_armed_state
        elif current_state in ARMED_STATES:
            target_state = current_state
        else:
            return

        if target_state is None or entity_id not in self._sensors_for_mode(
            target_state
        ):
            return

        if entity_id in self._bypassed_sensors:
            if new_state is not None and new_state.state == STATE_OFF:
                self._set_bypassed_sensors(self._bypassed_sensors - {entity_id})
                self._write_state()
            return

        if new_state is None or new_state.state in {STATE_UNKNOWN, STATE_UNAVAILABLE}:
            self._set_bypassed_sensors(self._bypassed_sensors | {entity_id})
            self._write_state()
            return

        if new_state.state != STATE_ON:
            return

        if current_state == AlarmControlPanelState.ARMING:
            self._set_bypassed_sensors(self._bypassed_sensors | {entity_id})
            self._write_state()
            return

        self._last_triggered_by = entity_id
        self._last_triggered_by_name = (
            new_state.attributes.get(ATTR_FRIENDLY_NAME)
            or (old_state.name if old_state is not None else None)
            or new_state.name
        )
        self._attr_alarm_state = AlarmControlPanelState.PENDING
        self._last_changed_at = dt_util.utcnow()
        self._write_state()
        self._timer_handle = async_call_later(
            self.hass, self._delay_time, self._trigger_alarm
        )

    @callback
    def _trigger_alarm(self, now: datetime) -> None:
        """Trigger the alarm after the entry delay."""
        self._timer_handle = None
        if self.alarm_state != AlarmControlPanelState.PENDING:
            return
        self._attr_alarm_state = AlarmControlPanelState.TRIGGERED
        self._triggered_count += 1
        self._last_changed_at = dt_util.utcnow()
        self._write_state()
        self._create_trigger_notification()
        self.hass.bus.async_fire(
            EVENT_ALARM_TRIGGERED,
            {
                "entity_id": self.entity_id,
                "alarm_name": self._entry.title,
                ATTR_TRIGGERED_BY: self._last_triggered_by,
                ATTR_TRIGGERED_BY_NAME: self.last_triggered_by_name,
                "timestamp": self._last_changed_at.isoformat(),
            },
        )
        self._timer_handle = async_call_later(
            self.hass, self._trigger_time, self._post_trigger_action
        )

    @callback
    def _create_trigger_notification(self) -> None:
        """Create or update the Home Assistant notification for this alarm."""
        sensor_id = self._last_triggered_by or "unknown"
        sensor_name = self.last_triggered_by_name or sensor_id
        triggered_at = self._last_changed_at or dt_util.utcnow()
        if str(self.hass.config.language).lower().startswith("fr"):
            title = f"Alarme déclenchée : {self._entry.title}"
            message = (
                f"Capteur responsable : **{sensor_name}** (`{sensor_id}`).\n\n"
                f"Déclenchement à {triggered_at.isoformat()}."
            )
        else:
            title = f"Alarm triggered: {self._entry.title}"
            message = (
                f"Triggering sensor: **{sensor_name}** (`{sensor_id}`).\n\n"
                f"Triggered at {triggered_at.isoformat()}."
            )

        async_create_persistent_notification(
            self.hass,
            message,
            title=title,
            notification_id=f"{DOMAIN}_{self._entry.entry_id}_triggered",
        )

    @callback
    def _post_trigger_action(self, now: datetime) -> None:
        """Rearm or disarm after the configured trigger duration."""
        self._timer_handle = None
        if self.alarm_state != AlarmControlPanelState.TRIGGERED:
            return
        if self._rearm_after_trigger and self._last_armed_state:
            self._attr_alarm_state = self._last_armed_state
        else:
            self._attr_alarm_state = AlarmControlPanelState.DISARMED
            self._set_bypassed_sensors(set())
            self.hass.bus.async_fire(
                EVENT_ALARM_DISARMED,
                {"entity_id": self.entity_id, "reason": "trigger_timeout"},
            )
        self._last_changed_at = dt_util.utcnow()
        self._write_state()

    async def async_alarm_disarm(self, code: str | None = None) -> None:
        """Disarm the alarm."""
        self._startup_state_touched = True
        await self._perform_disarm(code)

    def _validate_disarm_code(self, code: str | None) -> tuple[bool, bool]:
        """Return whether a code is valid and whether it is the emergency code."""
        if self._emergency_code and code == self._emergency_code:
            return True, True
        if self._require_disarm_code and (not self._code or code != self._code):
            _LOGGER.warning("Invalid or missing code for disarming")
            return False, False
        return True, False

    async def _perform_disarm(
        self,
        code: str | None = None,
        validation: tuple[bool, bool] | None = None,
    ) -> None:
        """Perform a validated disarm."""
        if self.alarm_state == AlarmControlPanelState.DISARMED:
            return
        is_valid, is_emergency = (
            validation if validation is not None else self._validate_disarm_code(code)
        )
        if not is_valid:
            return

        previous_state = self.alarm_state
        self._cancel_timer()
        self._attr_alarm_state = AlarmControlPanelState.DISARMED
        self._last_triggered_by = None
        self._last_triggered_by_name = None
        self._last_changed_at = dt_util.utcnow()
        self._set_bypassed_sensors(set())
        self._write_state()

        event_data = {
            "entity_id": self.entity_id,
            "previous_state": previous_state,
            "timestamp": self._last_changed_at.isoformat(),
        }
        self.hass.bus.async_fire(EVENT_ALARM_DISARMED, event_data)
        if is_emergency:
            self.hass.bus.async_fire(EVENT_EMERGENCY_DISARM, event_data)

    async def _arm(
        self,
        state: AlarmControlPanelState,
        code: str | None = None,
        *,
        skip_code: bool = False,
    ) -> None:
        """Arm the alarm in the requested mode."""
        if self.alarm_state == state:
            return
        if self.alarm_state != AlarmControlPanelState.DISARMED:
            _LOGGER.warning("Cannot arm from state %s", self.alarm_state)
            return
        if (
            not skip_code
            and self._require_arm_code
            and (not self._code or code != self._code)
        ):
            _LOGGER.warning("Invalid or missing code for arming")
            return

        self._cancel_timer()
        self._last_armed_state = state
        self._attr_alarm_state = AlarmControlPanelState.ARMING
        self._last_changed_at = dt_util.utcnow()
        self._set_bypassed_sensors(self._problematic_sensors_for_mode(state))
        self._write_state()
        self._timer_handle = async_call_later(
            self.hass, self._arming_time, self._finish_arming
        )

    @callback
    def _finish_arming(self, now: datetime) -> None:
        """Finish the arming delay."""
        self._timer_handle = None
        if (
            self.alarm_state != AlarmControlPanelState.ARMING
            or self._last_armed_state is None
        ):
            return
        self._attr_alarm_state = self._last_armed_state
        self._last_changed_at = dt_util.utcnow()
        self._write_state()
        self.hass.bus.async_fire(
            EVENT_ALARM_ARMED,
            {
                "entity_id": self.entity_id,
                "state": self.alarm_state,
                "timestamp": self._last_changed_at.isoformat(),
            },
        )

    async def async_alarm_arm_home(self, code: str | None = None) -> None:
        """Arm in home mode."""
        self._startup_state_touched = True
        await self._arm(AlarmControlPanelState.ARMED_HOME, code)

    async def async_alarm_arm_away(self, code: str | None = None) -> None:
        """Arm in away mode."""
        self._startup_state_touched = True
        await self._arm(AlarmControlPanelState.ARMED_AWAY, code)

    async def async_alarm_arm_vacation(self, code: str | None = None) -> None:
        """Arm in vacation mode."""
        self._startup_state_touched = True
        await self._arm(AlarmControlPanelState.ARMED_VACATION, code)
