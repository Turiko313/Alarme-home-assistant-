"""Config flow for Alarme Personnalisée."""
from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.core import callback
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers import selector

from .const import DOMAIN

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
        if self._async_current_entries():
            return self.async_abort(reason="already_configured")

        if user_input is not None:
            return self.async_create_entry(title="Alarme Personnalisée", data=user_input)

        data_schema = vol.Schema(
            {
                vol.Optional("away_sensors"): selector.EntitySelector(
                    selector.EntitySelectorConfig(domain="binary_sensor", multiple=True),
                ),
                vol.Optional("home_sensors"): selector.EntitySelector(
                    selector.EntitySelectorConfig(domain="binary_sensor", multiple=True),
                ),
                vol.Optional("vacation_sensors"): selector.EntitySelector(
                    selector.EntitySelectorConfig(domain="binary_sensor", multiple=True),
                ),
            }
        )

        return self.async_show_form(step_id="user", data_schema=data_schema)


class AlarmePersonnaliseeOptionsFlow(config_entries.OptionsFlow):
    """Handle an options flow for Alarme Personnalisée."""

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Manage the options."""
        if user_input is not None:
            # user_input contains the new options. We update the config entry.
            return self.async_create_entry(title="", data=user_input)

        # The form is pre-filled with values from the config entry options or data.
        # .options is for values set in the options flow, .data is for initial values.
        options = self.config_entry.options
        data = self.config_entry.data

        schema = vol.Schema(
            {
                vol.Optional(
                    "code",
                    description={"suggested_value": options.get("code")},
                ): str,
                vol.Optional(
                    "require_arm_code",
                    description={"suggested_value": options.get("require_arm_code", False)},
                ): bool,
                vol.Optional(
                    "require_disarm_code",
                    description={"suggested_value": options.get("require_disarm_code", True)},
                ): bool,
                vol.Optional(
                    "emergency_code",
                    description={"suggested_value": options.get("emergency_code")},
                ): str,
                vol.Optional(
                    "arming_time",
                    description={"suggested_value": options.get("arming_time", 30)},
                ): int,
                vol.Optional(
                    "delay_time",
                    description={"suggested_value": options.get("delay_time", 30)},
                ): int,
                vol.Optional(
                    "trigger_time",
                    description={"suggested_value": options.get("trigger_time", 180)},
                ): int,
                vol.Optional(
                    "rearm_after_trigger",
                    description={"suggested_value": options.get("rearm_after_trigger", False)},
                ): bool,
                vol.Optional(
                    "trigger_actions",
                    description={"suggested_value": options.get("trigger_actions", [])},
                ): selector.EntitySelector(
                    selector.EntitySelectorConfig(domain=["light", "switch", "siren"], multiple=True)
                ),
                vol.Optional(
                    "away_sensors",
                    description={"suggested_value": options.get("away_sensors", data.get("away_sensors", []))},
                ): selector.EntitySelector(
                    selector.EntitySelectorConfig(domain="binary_sensor", multiple=True),
                ),
                vol.Optional(
                    "home_sensors",
                    description={"suggested_value": options.get("home_sensors", data.get("home_sensors", []))},
                ): selector.EntitySelector(
                    selector.EntitySelectorConfig(domain="binary_sensor", multiple=True),
                ),
                vol.Optional(
                    "vacation_sensors",
                    description={"suggested_value": options.get("vacation_sensors", data.get("vacation_sensors", []))},
                ): selector.EntitySelector(
                    selector.EntitySelectorConfig(domain="binary_sensor", multiple=True),
                ),
            }
        )
        return self.async_show_form(step_id="init", data_schema=schema)
