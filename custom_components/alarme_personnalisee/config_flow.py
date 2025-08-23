"""Config flow for Alarme Personnalisée."""
from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol
from homeassistant.config_entries import ConfigFlow
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers import selector

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)


class AlarmePersonnaliseeConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Alarme Personnalisée."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the initial step."""
        errors: dict[str, str] = {}
        if user_input is not None:
            # Here you can add validation if needed before creating the entry.
            # For now, we just create it.
            return self.async_create_entry(title="Alarme Personnalisée", data=user_input)

        # This is the form the user will see.
        data_schema = vol.Schema(
            {
                vol.Optional("away_sensors"): selector.EntitySelector(
                    selector.EntitySelectorConfig(
                        domain="binary_sensor", multiple=True
                    ),
                ),
                vol.Optional("home_sensors"): selector.EntitySelector(
                    selector.EntitySelectorConfig(
                        domain="binary_sensor", multiple=True
                    ),
                ),
                vol.Optional("vacation_sensors"): selector.EntitySelector(
                    selector.EntitySelectorConfig(
                        domain="binary_sensor", multiple=True
                    ),
                ),
            }
        )

        return self.async_show_form(
            step_id="user", data_schema=data_schema, errors=errors
        )
