"""Constants for the Alarme Personnalisée integration."""

DOMAIN = "alarme_personnalisee"

# Events
EVENT_EMERGENCY_DISARM = f"{DOMAIN}.urgence"
EVENT_ALARM_TRIGGERED = f"{DOMAIN}.triggered"
EVENT_ALARM_ARMED = f"{DOMAIN}.armed"
EVENT_ALARM_DISARMED = f"{DOMAIN}.disarmed"
EVENT_ARMING_CANCELLED = f"{DOMAIN}.arming_cancelled"
EVENT_BADGE_DISARM = f"{DOMAIN}.badge_disarm"

# Default values
DEFAULT_ARMING_TIME = 30
DEFAULT_DELAY_TIME = 30
DEFAULT_TRIGGER_TIME = 180
DEFAULT_CODE = ""

# Attribute keys
ATTR_TRIGGERED_BY = "triggered_by"
ATTR_CANCELLED_BY = "cancelled_by"
ATTR_TRIGGERED_COUNT = "triggered_count"
ATTR_LAST_CHANGED_AT = "last_changed_at"
ATTR_LAST_ARMED_STATE = "last_armed_state"
ATTR_MONITORED_SENSORS = "monitored_sensors"
ATTR_BADGE_NAME = "badge_name"
ATTR_BADGE_ENTITY = "badge_entity"

# Configuration keys
CONF_BADGES = "badges"
CONF_BADGE_NAME = "badge_name"
CONF_BADGE_ENTITY = "badge_entity"
