"""The Alarme Personnalisée integration."""

from __future__ import annotations

from pathlib import Path

import voluptuous as vol
from homeassistant.components.http import StaticPathConfig
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.exceptions import ServiceValidationError
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers import entity_registry as er

from .const import DOMAIN, SERVICE_RESET_TRIGGER_COUNT
from .runtime_data import AlarmConfigEntry, AlarmRuntimeData

PLATFORMS: list[Platform] = [
    Platform.ALARM_CONTROL_PANEL,
    Platform.BUTTON,
    Platform.SENSOR,
    Platform.SWITCH,
    Platform.NUMBER,
]

CARD_URL = f"/{DOMAIN}/alarme-personnalisee-card.js"
CARD_PATH = Path(__file__).parent / "frontend" / "alarme-personnalisee-card.js"

SERVICE_RESET_TRIGGER_COUNT_SCHEMA = vol.Schema(
    {vol.Required("entity_id"): cv.entity_id}
)


async def async_setup(hass: HomeAssistant, config: dict) -> bool:
    """Set up integration-wide service actions."""
    await hass.http.async_register_static_paths(
        [StaticPathConfig(CARD_URL, str(CARD_PATH), cache_headers=True)]
    )

    async def async_reset_trigger_count(call: ServiceCall) -> None:
        """Reset the trigger count of the requested alarm."""
        entity_id = call.data["entity_id"]
        registry_entry = er.async_get(hass).async_get(entity_id)
        if (
            registry_entry is None
            or registry_entry.platform != DOMAIN
            or registry_entry.config_entry_id is None
        ):
            raise ServiceValidationError(
                translation_domain=DOMAIN,
                translation_key="invalid_alarm_entity",
                translation_placeholders={"entity_id": entity_id},
            )

        config_entry = hass.config_entries.async_get_entry(
            registry_entry.config_entry_id
        )
        if config_entry is None:
            raise ServiceValidationError(
                translation_domain=DOMAIN,
                translation_key="invalid_alarm_entity",
                translation_placeholders={"entity_id": entity_id},
            )

        runtime_data: AlarmRuntimeData = config_entry.runtime_data
        if runtime_data.alarm is None or runtime_data.alarm.entity_id != entity_id:
            raise ServiceValidationError(
                translation_domain=DOMAIN,
                translation_key="invalid_alarm_entity",
                translation_placeholders={"entity_id": entity_id},
            )

        runtime_data.alarm.reset_trigger_count()

    hass.services.async_register(
        DOMAIN,
        SERVICE_RESET_TRIGGER_COUNT,
        async_reset_trigger_count,
        schema=SERVICE_RESET_TRIGGER_COUNT_SCHEMA,
    )
    return True


async def async_setup_entry(hass: HomeAssistant, entry: AlarmConfigEntry) -> bool:
    """Set up Alarme Personnalisée from a config entry."""
    entry.runtime_data = AlarmRuntimeData()
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
