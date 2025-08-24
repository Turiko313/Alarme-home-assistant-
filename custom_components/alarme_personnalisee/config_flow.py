"""Config flow for Alarme Personnalisée."""
from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.core import callback
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers import selector
from homeassistant.helpers.selector import (
    ColorRgbSelector,
    EntitySelector,
    EntitySelectorConfig,
    ListSelector,
    ObjectSelector,
    SelectSelector,
    SelectSelectorConfig,
    SelectSelectorMode,
)

from .const import (
    CONF_LIGHT_ACTIONS,
    CONF_SIREN_ACTIONS,
    CONF_SWITCH_ACTIONS,
    DOMAIN,
)

_LOGGER = logging.getLogger(__name__)


class AlarmePersonnaliseeConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Alarme Personnalisée."""

    VERSION = 1

    @staticmethod
    @callback
    def async_get_options_flow(
        config_entry: config_entries.ConfigEntry,
    ) -> AlarmePersonnaliseeOptionsFlow:
        """Get the options flow for this handler."""
        return AlarmePersonnaliseeOptionsFlow(config_entry)

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the initial step."""
        # Allow only one instance of the integration.
        if self._async_current_entries():
            return self.async_abort(reason="already_configured")

        # No user input needed for initial setup, create the entry immediately.
        # All configuration will be done in the options flow.
        return self.async_create_entry(title="Alarme Personnalisée", data={})


class AlarmePersonnaliseeOptionsFlow(config_entries.OptionsFlow):
    """Handle an options flow for Alarme Personnalisée."""

    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        """Initialize options flow."""
        self.config_entry = config_entry

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Manage the options."""
        if user_input is not None:
            # user_input contains the new options. We update the config entry.
            return self.async_create_entry(title="", data=user_input)

        # The form is pre-filled with values from the config entry options.
        options = self.config_entry.options

        schema = vol.Schema(
            {
                vol.Optional(
                    "code", default=options.get("code", "")
                ): str,
                vol.Optional(
                    "require_arm_code",
                    default=options.get("require_arm_code", False),
                ): bool,
                vol.Optional(
                    "require_disarm_code",
                    default=options.get("require_disarm_code", True),
                ): bool,
                vol.Optional(
                    "emergency_code", default=options.get("emergency_code", "")
                ): str,
                vol.Optional(
                    "arming_time", default=options.get("arming_time", 30)
                ): int,
                vol.Optional(
                    "delay_time", default=options.get("delay_time", 30)
                ): int,
                vol.Optional(
                    "trigger_time", default=options.get("trigger_time", 180)
                ): int,
                vol.Optional(
                    "rearm_after_trigger",
                    default=options.get("rearm_after_trigger", False),
                ): bool,
                vol.Optional(
                    CONF_LIGHT_ACTIONS,
                    default=options.get(CONF_LIGHT_ACTIONS, []),
                ): ListSelector(
                    ObjectSelector(
                        vol.Schema(
                            {
                                vol.Required("entity_id"): EntitySelector(
                                    EntitySelectorConfig(domain="light")
                                ),
                                vol.Optional("brightness"): vol.All(
                                    vol.Coerce(int), vol.Range(min=0, max=255)
                                ),
                                vol.Optional("color"): ColorRgbSelector(),
                                vol.Optional("flash"): SelectSelector(
                                    SelectSelectorConfig(
                                        options=["short", "long"],
                                        mode=SelectSelectorMode.DROPDOWN,
                                    )
                                ),
                            }
                        )
                    )
                ),
                vol.Optional(
                    CONF_SIREN_ACTIONS,
                    default=options.get(CONF_SIREN_ACTIONS, []),
                ): ListSelector(
                    ObjectSelector(
                        vol.Schema(
                            {
                                vol.Required("entity_id"): EntitySelector(
                                    EntitySelectorConfig(domain="siren")
                                ),
                                vol.Optional("volume"): vol.All(
                                    vol.Coerce(float), vol.Range(min=0.0, max=1.0)
                                ),
                            }
                        )
                    )
                ),
                vol.Optional(
                    CONF_SWITCH_ACTIONS,
                    default=options.get(CONF_SWITCH_ACTIONS, []),
                ): EntitySelector(EntitySelectorConfig(domain="switch", multiple=True)),
                vol.Optional(
                    "away_sensors",
                    default=options.get("away_sensors", []),
                ): EntitySelector(
                    EntitySelectorConfig(domain="binary_sensor", multiple=True),
                ),
                vol.Optional(
                    "home_sensors",
                    default=options.get("home_sensors", []),
                ): EntitySelector(
                    EntitySelectorConfig(domain="binary_sensor", multiple=True),
                ),
                vol.Optional(
                    "vacation_sensors",
                    default=options.get("vacation_sensors", []),
                ): EntitySelector(
                    EntitySelectorConfig(domain="binary_sensor", multiple=True),
                ),
            }
        )
        return self.async_show_form(step_id="init", data_schema=schema)
