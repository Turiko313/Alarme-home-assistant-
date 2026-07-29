"""Functional tests for Alarme Personnalisée."""

from datetime import datetime
from unittest.mock import patch

import pytest
from homeassistant.components.alarm_control_panel.const import AlarmControlPanelState
from homeassistant.const import ATTR_ENTITY_ID, STATE_OFF, STATE_ON, STATE_UNKNOWN
from homeassistant.core import HomeAssistant, State
from homeassistant.exceptions import HomeAssistantError, ServiceValidationError
from homeassistant.helpers import entity_registry as er
from homeassistant.helpers import issue_registry as ir
from homeassistant.util import dt as dt_util
from pytest_homeassistant_custom_component.common import (
    MockConfigEntry,
    async_capture_events,
    mock_restore_cache,
)

from custom_components.alarme_personnalisee.const import (
    ATTR_BYPASSED_SENSORS,
    ATTR_TRIGGERED_BY_NAME,
    CONF_ARMING_TIME,
    CONF_AWAY_SENSORS,
    CONF_BADGE_ENTITY,
    CONF_BADGE_NAME,
    CONF_BADGE_VALUE,
    CONF_BADGES,
    CONF_CODE,
    CONF_DELAY_TIME,
    CONF_HOME_SENSORS,
    CONF_REARM_AFTER_TRIGGER,
    CONF_REQUIRE_DISARM_CODE,
    CONF_TRIGGER_TIME,
    CONF_VACATION_SENSORS,
    DOMAIN,
    EVENT_ALARM_TRIGGERED,
    EVENT_BYPASSED_SENSORS_CHANGED,
    EVENT_SENSOR_AVAILABILITY_CHANGED,
    ISSUE_BYPASSED_SENSORS,
    ISSUE_UNAVAILABLE_SENSORS,
    SERVICE_RESET_TRIGGER_COUNT,
)
from custom_components.alarme_personnalisee.runtime_data import AlarmConfigEntry

FRONT_DOOR = "binary_sensor.front_door"
BADGE_READER = "sensor.badge_reader"


async def _setup_alarm(
    hass: HomeAssistant, options: dict | None = None
) -> tuple[AlarmConfigEntry, str]:
    """Set up one alarm and return its config entry and entity ID."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        title="Maison",
        data={},
        options=options or {},
    )
    entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    entity_id = er.async_get(hass).async_get_entity_id(
        "alarm_control_panel", DOMAIN, entry.entry_id
    )
    assert entity_id is not None
    return entry, entity_id


def _finish_arming(entry: AlarmConfigEntry) -> None:
    """Complete the arming timer."""
    alarm = entry.runtime_data.alarm
    assert alarm is not None
    alarm._finish_arming(dt_util.utcnow())


async def _arm_away(hass: HomeAssistant, entity_id: str) -> None:
    """Request away arming through the Home Assistant service."""
    await hass.services.async_call(
        "alarm_control_panel",
        "alarm_arm_away",
        {ATTR_ENTITY_ID: entity_id},
        blocking=True,
    )


async def test_full_alarm_cycle(hass: HomeAssistant) -> None:
    """Arm, enter pending, trigger, count, and disarm after timeout."""
    events = async_capture_events(hass, EVENT_ALARM_TRIGGERED)
    hass.states.async_set(FRONT_DOOR, STATE_OFF, {"friendly_name": "Porte d'entrée"})
    entry, entity_id = await _setup_alarm(
        hass,
        {
            CONF_AWAY_SENSORS: [FRONT_DOOR],
            CONF_ARMING_TIME: 10,
            CONF_DELAY_TIME: 10,
            CONF_TRIGGER_TIME: 10,
        },
    )
    alarm = entry.runtime_data.alarm
    assert alarm is not None

    await _arm_away(hass, entity_id)
    assert hass.states.get(entity_id).state == AlarmControlPanelState.ARMING

    _finish_arming(entry)
    assert hass.states.get(entity_id).state == AlarmControlPanelState.ARMED_AWAY

    hass.states.async_set(FRONT_DOOR, STATE_ON)
    await hass.async_block_till_done()
    assert hass.states.get(entity_id).state == AlarmControlPanelState.PENDING

    with patch(
        "custom_components.alarme_personnalisee.alarm_control_panel."
        "async_create_persistent_notification"
    ) as create_notification:
        alarm._trigger_alarm(dt_util.utcnow())

    assert hass.states.get(entity_id).state == AlarmControlPanelState.TRIGGERED
    assert (
        hass.states.get(entity_id).attributes[ATTR_TRIGGERED_BY_NAME]
        == "Porte d'entrée"
    )
    assert events[-1].data["triggered_by"] == FRONT_DOOR
    assert events[-1].data[ATTR_TRIGGERED_BY_NAME] == "Porte d'entrée"
    notification_id = f"{DOMAIN}_{entry.entry_id}_triggered"
    create_notification.assert_called_once()
    notification_args, notification_kwargs = create_notification.call_args
    assert notification_args[0] is hass
    assert "Porte d'entrée" in notification_args[1]
    assert FRONT_DOOR in notification_args[1]
    assert notification_kwargs["notification_id"] == notification_id
    assert alarm.triggered_count == 1

    alarm._post_trigger_action(dt_util.utcnow())
    assert hass.states.get(entity_id).state == AlarmControlPanelState.DISARMED


async def test_open_sensor_is_bypassed_then_reactivated(
    hass: HomeAssistant,
) -> None:
    """An open zone is bypassed, then protects again after closing."""
    events = async_capture_events(hass, EVENT_BYPASSED_SENSORS_CHANGED)
    hass.states.async_set(FRONT_DOOR, STATE_ON)
    entry, entity_id = await _setup_alarm(hass, {CONF_AWAY_SENSORS: [FRONT_DOOR]})

    await _arm_away(hass, entity_id)

    assert hass.states.get(entity_id).state == AlarmControlPanelState.ARMING
    assert hass.states.get(entity_id).attributes[ATTR_BYPASSED_SENSORS] == [FRONT_DOOR]
    issue_id = f"{ISSUE_BYPASSED_SENSORS}_{entry.entry_id}"
    issue = ir.async_get(hass).async_get_issue(DOMAIN, issue_id)
    assert issue is not None
    assert issue.severity is ir.IssueSeverity.WARNING

    _finish_arming(entry)
    assert hass.states.get(entity_id).state == AlarmControlPanelState.ARMED_AWAY

    hass.states.async_set(FRONT_DOOR, STATE_OFF)
    await hass.async_block_till_done()

    assert hass.states.get(entity_id).state == AlarmControlPanelState.ARMED_AWAY
    assert hass.states.get(entity_id).attributes[ATTR_BYPASSED_SENSORS] == []
    assert ir.async_get(hass).async_get_issue(DOMAIN, issue_id) is None
    assert events[-1].data[ATTR_BYPASSED_SENSORS] == []

    hass.states.async_set(FRONT_DOOR, STATE_ON)
    await hass.async_block_till_done()

    assert hass.states.get(entity_id).state == AlarmControlPanelState.PENDING


async def test_sensor_opened_during_arming_is_bypassed(
    hass: HomeAssistant,
) -> None:
    """A zone opened during the exit delay does not cancel arming."""
    hass.states.async_set(FRONT_DOOR, STATE_OFF)
    entry, entity_id = await _setup_alarm(hass, {CONF_AWAY_SENSORS: [FRONT_DOOR]})

    await _arm_away(hass, entity_id)
    hass.states.async_set(FRONT_DOOR, STATE_ON)
    await hass.async_block_till_done()

    assert hass.states.get(entity_id).state == AlarmControlPanelState.ARMING
    assert hass.states.get(entity_id).attributes[ATTR_BYPASSED_SENSORS] == [FRONT_DOOR]


async def test_unknown_sensor_is_reported_when_arming(hass: HomeAssistant) -> None:
    """An unknown zone is identified in the bypass notification event."""
    events = async_capture_events(hass, EVENT_BYPASSED_SENSORS_CHANGED)
    hass.states.async_set(FRONT_DOOR, STATE_UNKNOWN)
    _, entity_id = await _setup_alarm(hass, {CONF_AWAY_SENSORS: [FRONT_DOOR]})

    await _arm_away(hass, entity_id)

    assert hass.states.get(entity_id).state == AlarmControlPanelState.ARMING
    assert events[-1].data[ATTR_BYPASSED_SENSORS] == [FRONT_DOOR]
    assert events[-1].data["sensor_states"] == {FRONT_DOOR: STATE_UNKNOWN}


async def test_badge_requires_exact_reader_value(hass: HomeAssistant) -> None:
    """Only the configured badge value can disarm the alarm."""
    hass.states.async_set(BADGE_READER, "idle")
    entry, entity_id = await _setup_alarm(
        hass,
        {
            CONF_BADGES: [
                {
                    CONF_BADGE_NAME: "Alice",
                    CONF_BADGE_ENTITY: BADGE_READER,
                    CONF_BADGE_VALUE: "04-A1-B2",
                }
            ]
        },
    )
    await _arm_away(hass, entity_id)
    _finish_arming(entry)

    hass.states.async_set(BADGE_READER, "unknown-badge")
    await hass.async_block_till_done()
    assert hass.states.get(entity_id).state == AlarmControlPanelState.ARMED_AWAY

    hass.states.async_set(BADGE_READER, "04-A1-B2")
    await hass.async_block_till_done()
    assert hass.states.get(entity_id).state == AlarmControlPanelState.DISARMED


async def test_disarm_code_and_reset_service(hass: HomeAssistant) -> None:
    """The disarm code is enforced and the reset action targets one alarm."""
    entry, entity_id = await _setup_alarm(
        hass,
        {
            CONF_CODE: "1234",
            CONF_REQUIRE_DISARM_CODE: True,
            CONF_REARM_AFTER_TRIGGER: True,
        },
    )
    alarm = entry.runtime_data.alarm
    assert alarm is not None
    await _arm_away(hass, entity_id)
    _finish_arming(entry)

    await hass.services.async_call(
        "alarm_control_panel",
        "alarm_disarm",
        {ATTR_ENTITY_ID: entity_id, "code": "9999"},
        blocking=True,
    )
    assert hass.states.get(entity_id).state == AlarmControlPanelState.ARMED_AWAY

    await hass.services.async_call(
        "alarm_control_panel",
        "alarm_disarm",
        {ATTR_ENTITY_ID: entity_id, "code": "1234"},
        blocking=True,
    )
    assert hass.states.get(entity_id).state == AlarmControlPanelState.DISARMED

    alarm._triggered_count = 2
    alarm._write_state()
    await hass.services.async_call(
        DOMAIN,
        SERVICE_RESET_TRIGGER_COUNT,
        {ATTR_ENTITY_ID: entity_id},
        blocking=True,
    )
    assert alarm.triggered_count == 0


async def test_timestamp_sensor_exposes_datetime(hass: HomeAssistant) -> None:
    """The timestamp diagnostic sensor uses a timezone-aware datetime."""
    entry, entity_id = await _setup_alarm(hass)
    await _arm_away(hass, entity_id)
    await hass.async_block_till_done()

    sensor_id = er.async_get(hass).async_get_entity_id(
        "sensor", DOMAIN, f"{entry.entry_id}_last_changed_at"
    )
    assert sensor_id is not None
    state = hass.states.get(sensor_id)
    assert state is not None
    assert state.state != "unknown"
    parsed = datetime.fromisoformat(state.state)
    assert parsed.tzinfo is not None


async def test_option_update_keeps_active_timer(hass: HomeAssistant) -> None:
    """Changing an option must not leave an alarm stuck while arming."""
    entry, entity_id = await _setup_alarm(hass, {CONF_ARMING_TIME: 30})
    await _arm_away(hass, entity_id)
    alarm = entry.runtime_data.alarm
    assert alarm is not None
    timer_handle = alarm._timer_handle
    assert timer_handle is not None

    hass.config_entries.async_update_entry(
        entry,
        options={**entry.options, CONF_REARM_AFTER_TRIGGER: True},
    )
    await hass.async_block_till_done()

    assert alarm._timer_handle is timer_handle
    assert hass.states.get(entity_id).state == AlarmControlPanelState.ARMING


async def test_reset_service_isolated_between_instances(hass: HomeAssistant) -> None:
    """Resetting one alarm does not modify another configured instance."""
    first_entry, first_entity_id = await _setup_alarm(hass)
    second_entry, _ = await _setup_alarm(hass)
    first_alarm = first_entry.runtime_data.alarm
    second_alarm = second_entry.runtime_data.alarm
    assert first_alarm is not None
    assert second_alarm is not None
    first_alarm._triggered_count = 2
    second_alarm._triggered_count = 3

    await hass.services.async_call(
        DOMAIN,
        SERVICE_RESET_TRIGGER_COUNT,
        {ATTR_ENTITY_ID: first_entity_id},
        blocking=True,
    )

    assert first_alarm.triggered_count == 0
    assert second_alarm.triggered_count == 3


async def test_restores_armed_mode_and_trigger_count(hass: HomeAssistant) -> None:
    """The protected mode and trigger count survive a restart."""
    mock_restore_cache(
        hass,
        [
            State(
                "alarm_control_panel.maison",
                AlarmControlPanelState.ARMED_AWAY,
                {
                    "triggered_count": 4,
                    "last_armed_state": AlarmControlPanelState.ARMED_AWAY,
                    "last_changed_at": dt_util.utcnow().isoformat(),
                },
            )
        ],
    )

    entry, entity_id = await _setup_alarm(hass)
    alarm = entry.runtime_data.alarm
    assert alarm is not None
    assert hass.states.get(entity_id).state == AlarmControlPanelState.ARMED_AWAY
    assert alarm.triggered_count == 4


async def test_repairs_tracks_unavailable_sensor(hass: HomeAssistant) -> None:
    """A Repairs issue and event follow sensor availability."""
    events = async_capture_events(hass, EVENT_SENSOR_AVAILABILITY_CHANGED)
    hass.states.async_set(FRONT_DOOR, "unavailable")
    entry, _ = await _setup_alarm(hass, {CONF_AWAY_SENSORS: [FRONT_DOOR]})
    issue_id = f"{ISSUE_UNAVAILABLE_SENSORS}_{entry.entry_id}"

    issue = ir.async_get(hass).async_get_issue(DOMAIN, issue_id)
    assert issue is not None
    assert issue.severity is ir.IssueSeverity.ERROR

    hass.states.async_set(FRONT_DOOR, STATE_OFF)
    await hass.async_block_till_done()

    assert ir.async_get(hass).async_get_issue(DOMAIN, issue_id) is None
    assert events[-1].data["available"] is True
    assert events[-1].data["unavailable_sensors"] == []


async def test_restored_alarm_bypasses_active_zone(hass: HomeAssistant) -> None:
    """A restored armed alarm bypasses a zone that is already active."""
    hass.states.async_set(FRONT_DOOR, STATE_ON)
    mock_restore_cache(
        hass,
        [
            State(
                "alarm_control_panel.maison",
                AlarmControlPanelState.ARMED_AWAY,
                {
                    "triggered_count": 1,
                    "last_armed_state": AlarmControlPanelState.ARMED_AWAY,
                },
            )
        ],
    )

    _, entity_id = await _setup_alarm(
        hass,
        {
            CONF_AWAY_SENSORS: [FRONT_DOOR],
            CONF_DELAY_TIME: 30,
        },
    )

    state = hass.states.get(entity_id)
    assert state.state == AlarmControlPanelState.ARMED_AWAY
    assert state.attributes[ATTR_BYPASSED_SENSORS] == [FRONT_DOOR]


async def test_restores_transient_and_invalid_states(hass: HomeAssistant) -> None:
    """Transient states recover safely and malformed metadata uses defaults."""
    mock_restore_cache(
        hass,
        [
            State(
                "alarm_control_panel.maison",
                AlarmControlPanelState.PENDING,
                {
                    "triggered_count": "invalid",
                    "last_armed_state": AlarmControlPanelState.ARMED_HOME,
                },
            )
        ],
    )
    entry, entity_id = await _setup_alarm(hass)
    alarm = entry.runtime_data.alarm
    assert alarm is not None
    assert hass.states.get(entity_id).state == AlarmControlPanelState.ARMED_HOME
    assert alarm.triggered_count == 0

    assert await hass.config_entries.async_unload(entry.entry_id)
    mock_restore_cache(
        hass,
        [
            State(
                "alarm_control_panel.maison",
                "invalid-state",
                {
                    "triggered_count": None,
                    "last_armed_state": "invalid-mode",
                },
            )
        ],
    )
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    assert hass.states.get(entity_id).state == AlarmControlPanelState.DISARMED


async def test_home_and_vacation_modes_use_their_own_sensors(
    hass: HomeAssistant,
) -> None:
    """Home and vacation commands select the corresponding sensor lists."""
    hass.states.async_set(FRONT_DOOR, STATE_OFF)
    entry, entity_id = await _setup_alarm(
        hass,
        {
            CONF_HOME_SENSORS: [FRONT_DOOR],
            CONF_VACATION_SENSORS: [FRONT_DOOR],
        },
    )

    await hass.services.async_call(
        "alarm_control_panel",
        "alarm_arm_home",
        {ATTR_ENTITY_ID: entity_id},
        blocking=True,
    )
    _finish_arming(entry)
    assert hass.states.get(entity_id).state == AlarmControlPanelState.ARMED_HOME

    await hass.services.async_call(
        "alarm_control_panel",
        "alarm_disarm",
        {ATTR_ENTITY_ID: entity_id},
        blocking=True,
    )
    await hass.services.async_call(
        "alarm_control_panel",
        "alarm_arm_vacation",
        {ATTR_ENTITY_ID: entity_id},
        blocking=True,
    )
    _finish_arming(entry)
    assert hass.states.get(entity_id).state == AlarmControlPanelState.ARMED_VACATION


async def test_configuration_entities_update_options_and_report_unavailable_alarm(
    hass: HomeAssistant,
) -> None:
    """Number/switch entities update options and the button handles no alarm."""
    entry, _ = await _setup_alarm(hass)
    registry = er.async_get(hass)
    number_id = registry.async_get_entity_id(
        "number", DOMAIN, f"{entry.entry_id}_arming_time"
    )
    switch_id = registry.async_get_entity_id(
        "switch", DOMAIN, f"{entry.entry_id}_rearm_after_trigger"
    )
    button_id = registry.async_get_entity_id(
        "button", DOMAIN, f"{entry.entry_id}_reset_trigger_count"
    )
    assert number_id and switch_id and button_id

    await hass.services.async_call(
        "number",
        "set_value",
        {ATTR_ENTITY_ID: number_id, "value": 45},
        blocking=True,
    )
    assert entry.options[CONF_ARMING_TIME] == 45

    await hass.services.async_call(
        "switch", "turn_on", {ATTR_ENTITY_ID: switch_id}, blocking=True
    )
    assert entry.options[CONF_REARM_AFTER_TRIGGER] is True
    await hass.services.async_call(
        "switch", "turn_off", {ATTR_ENTITY_ID: switch_id}, blocking=True
    )
    assert entry.options[CONF_REARM_AFTER_TRIGGER] is False

    entry.runtime_data.alarm = None
    with pytest.raises(HomeAssistantError):
        await hass.services.async_call(
            "button", "press", {ATTR_ENTITY_ID: button_id}, blocking=True
        )


async def test_reset_service_rejects_invalid_targets(hass: HomeAssistant) -> None:
    """The reset action rejects unknown, detached, and unavailable alarms."""
    entry, entity_id = await _setup_alarm(hass)

    with pytest.raises(ServiceValidationError):
        await hass.services.async_call(
            DOMAIN,
            SERVICE_RESET_TRIGGER_COUNT,
            {ATTR_ENTITY_ID: "alarm_control_panel.unknown"},
            blocking=True,
        )

    with (
        patch.object(hass.config_entries, "async_get_entry", return_value=None),
        pytest.raises(ServiceValidationError),
    ):
        await hass.services.async_call(
            DOMAIN,
            SERVICE_RESET_TRIGGER_COUNT,
            {ATTR_ENTITY_ID: entity_id},
            blocking=True,
        )

    entry.runtime_data.alarm = None
    with pytest.raises(ServiceValidationError):
        await hass.services.async_call(
            DOMAIN,
            SERVICE_RESET_TRIGGER_COUNT,
            {ATTR_ENTITY_ID: entity_id},
            blocking=True,
        )
