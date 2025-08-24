"""Constants for the Alarme Personnalisée integration."""

DOMAIN = "alarme_personnalisee"

# Events
EVENT_TRIGGERED = f"{DOMAIN}_triggered"
EVENT_STOPPED = f"{DOMAIN}_stopped"
EVENT_DISARMED = f"{DOMAIN}_disarmed"
EVENT_EMERGENCY_DISARM = f"{DOMAIN}_emergency_disarmed" # Renaming for consistency
