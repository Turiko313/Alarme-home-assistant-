"""Constants for the Alarme Personnalisée integration."""

DOMAIN = "alarme_personnalisee"

# Events
EVENT_EMERGENCY_DISARM = f"{DOMAIN}.urgence"
EVENT_ALARM_TRIGGERED = f"{DOMAIN}.triggered"
EVENT_ALARM_ARMED = f"{DOMAIN}.armed"
EVENT_ALARM_DISARMED = f"{DOMAIN}.disarmed"
EVENT_BADGE_DISARM = f"{DOMAIN}.badge_disarm"
EVENT_SENSOR_AVAILABILITY_CHANGED = f"{DOMAIN}.sensor_availability_changed"
EVENT_BYPASSED_SENSORS_CHANGED = f"{DOMAIN}.bypassed_sensors_changed"

# Default values
DEFAULT_ARMING_TIME = 30
DEFAULT_DELAY_TIME = 30
DEFAULT_TRIGGER_TIME = 180
DEFAULT_CODE = ""

# Attribute keys
ATTR_TRIGGERED_BY = "triggered_by"
ATTR_TRIGGERED_BY_NAME = "triggered_by_name"
ATTR_TRIGGERED_COUNT = "triggered_count"
ATTR_LAST_CHANGED_AT = "last_changed_at"
ATTR_LAST_ARMED_STATE = "last_armed_state"
ATTR_MONITORED_SENSORS = "monitored_sensors"
ATTR_BADGE_NAME = "badge_name"
ATTR_BADGE_ENTITY = "badge_entity"
ATTR_BADGE_VALUE = "badge_value"
ATTR_BYPASSED_SENSORS = "bypassed_sensors"

# Configuration keys
CONF_NAME = "name"
CONF_CODE = "code"
CONF_REQUIRE_ARM_CODE = "require_arm_code"
CONF_REQUIRE_DISARM_CODE = "require_disarm_code"
CONF_EMERGENCY_CODE = "emergency_code"
CONF_ARMING_TIME = "arming_time"
CONF_DELAY_TIME = "delay_time"
CONF_TRIGGER_TIME = "trigger_time"
CONF_REARM_AFTER_TRIGGER = "rearm_after_trigger"
CONF_AWAY_SENSORS = "away_sensors"
CONF_HOME_SENSORS = "home_sensors"
CONF_VACATION_SENSORS = "vacation_sensors"
CONF_BADGES = "badges"
CONF_BADGE_NAME = "badge_name"
CONF_BADGE_ENTITY = "badge_entity"
CONF_BADGE_VALUE = "badge_value"

# Services and dispatcher
SERVICE_RESET_TRIGGER_COUNT = "reset_trigger_count"
SIGNAL_STATE_UPDATED = f"{DOMAIN}_state_updated"
ISSUE_UNAVAILABLE_SENSORS = "unavailable_sensors"
ISSUE_BYPASSED_SENSORS = "bypassed_sensors"
