"""Config flow for Alarme Personnalisée."""

from __future__ import annotations

from typing import Any

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.const import STATE_ON
from homeassistant.core import callback
from homeassistant.helpers import selector

from .const import (
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
    CONF_NAME,
    CONF_REARM_AFTER_TRIGGER,
    CONF_REQUIRE_ARM_CODE,
    CONF_REQUIRE_DISARM_CODE,
    CONF_TRIGGER_TIME,
    CONF_VACATION_SENSORS,
    DEFAULT_ARMING_TIME,
    DEFAULT_CODE,
    DEFAULT_DELAY_TIME,
    DEFAULT_TRIGGER_TIME,
    DOMAIN,
)


class AlarmePersonnaliseeConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Alarme Personnalisée."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> config_entries.ConfigFlowResult:
        """Handle the initial step."""
        if user_input is not None:
            return self.async_create_entry(title=user_input[CONF_NAME], data={})

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema({vol.Required(CONF_NAME, default="Alarme"): str}),
        )

    @staticmethod
    @callback
    def async_get_options_flow(
        config_entry: config_entries.ConfigEntry,
    ) -> AlarmePersonnaliseeOptionsFlow:
        """Create the options flow."""
        return AlarmePersonnaliseeOptionsFlow()


class AlarmePersonnaliseeOptionsFlow(config_entries.OptionsFlow):
    """Handle options for Alarme Personnalisée."""

    _pending_options: dict[str, Any] | None = None

    def _options(self) -> dict[str, Any]:
        """Return a mutable copy used by the current flow."""
        if self._pending_options is None:
            self._pending_options = dict(self.config_entry.options)
            self._pending_options[CONF_BADGES] = [
                dict(badge) for badge in self.config_entry.options.get(CONF_BADGES, [])
            ]
        return self._pending_options

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> config_entries.ConfigFlowResult:
        """Show the options menu."""
        return self.async_show_menu(
            step_id="init",
            menu_options=["general", "sensors", "badges"],
        )

    async def async_step_general(
        self, user_input: dict[str, Any] | None = None
    ) -> config_entries.ConfigFlowResult:
        """Manage general options."""
        if user_input is not None:
            return self.async_create_entry(
                title="", data={**self.config_entry.options, **user_input}
            )

        options = self.config_entry.options
        return self.async_show_form(
            step_id="general",
            data_schema=vol.Schema(
                {
                    vol.Optional(
                        CONF_CODE, default=options.get(CONF_CODE, DEFAULT_CODE)
                    ): str,
                    vol.Optional(
                        CONF_REQUIRE_ARM_CODE,
                        default=options.get(CONF_REQUIRE_ARM_CODE, False),
                    ): bool,
                    vol.Optional(
                        CONF_REQUIRE_DISARM_CODE,
                        default=options.get(CONF_REQUIRE_DISARM_CODE, False),
                    ): bool,
                    vol.Optional(
                        CONF_EMERGENCY_CODE,
                        default=options.get(CONF_EMERGENCY_CODE, DEFAULT_CODE),
                    ): str,
                    vol.Optional(
                        CONF_ARMING_TIME,
                        default=options.get(CONF_ARMING_TIME, DEFAULT_ARMING_TIME),
                    ): vol.All(vol.Coerce(int), vol.Range(min=0, max=600)),
                    vol.Optional(
                        CONF_DELAY_TIME,
                        default=options.get(CONF_DELAY_TIME, DEFAULT_DELAY_TIME),
                    ): vol.All(vol.Coerce(int), vol.Range(min=0, max=600)),
                    vol.Optional(
                        CONF_TRIGGER_TIME,
                        default=options.get(CONF_TRIGGER_TIME, DEFAULT_TRIGGER_TIME),
                    ): vol.All(vol.Coerce(int), vol.Range(min=0, max=1800)),
                    vol.Optional(
                        CONF_REARM_AFTER_TRIGGER,
                        default=options.get(CONF_REARM_AFTER_TRIGGER, False),
                    ): bool,
                }
            ),
        )

    async def async_step_sensors(
        self, user_input: dict[str, Any] | None = None
    ) -> config_entries.ConfigFlowResult:
        """Manage monitored sensors."""
        if user_input is not None:
            return self.async_create_entry(
                title="", data={**self.config_entry.options, **user_input}
            )

        options = self.config_entry.options
        binary_sensor_selector = selector.EntitySelector(
            selector.EntitySelectorConfig(
                domain="binary_sensor",
                multiple=True,
            )
        )
        return self.async_show_form(
            step_id="sensors",
            data_schema=vol.Schema(
                {
                    vol.Optional(
                        CONF_AWAY_SENSORS,
                        default=options.get(CONF_AWAY_SENSORS, []),
                    ): binary_sensor_selector,
                    vol.Optional(
                        CONF_HOME_SENSORS,
                        default=options.get(CONF_HOME_SENSORS, []),
                    ): binary_sensor_selector,
                    vol.Optional(
                        CONF_VACATION_SENSORS,
                        default=options.get(CONF_VACATION_SENSORS, []),
                    ): binary_sensor_selector,
                }
            ),
        )

    async def async_step_badges(
        self, user_input: dict[str, Any] | None = None
    ) -> config_entries.ConfigFlowResult:
        """Manage authorized badges."""
        if user_input is not None:
            action = user_input["action"]
            if action == "add":
                return await self.async_step_add_badge()
            if action == "remove":
                return await self.async_step_remove_badge()
            return self.async_create_entry(title="", data=self._options())

        badges = self._options().get(CONF_BADGES, [])
        description = "\n".join(
            (
                f"- {badge[CONF_BADGE_NAME]} "
                f"({badge[CONF_BADGE_ENTITY]} = "
                f"{badge.get(CONF_BADGE_VALUE, 'on')})"
            )
            for badge in badges
        )
        return self.async_show_form(
            step_id="badges",
            data_schema=vol.Schema(
                {
                    vol.Required("action"): vol.In(
                        {
                            "add": "Ajouter / Add",
                            "remove": "Supprimer / Remove",
                            "done": "Terminer / Done",
                        }
                    )
                }
            ),
            description_placeholders={"badges_list": description or "-"},
        )

    async def async_step_add_badge(
        self, user_input: dict[str, Any] | None = None
    ) -> config_entries.ConfigFlowResult:
        """Add an authorized badge."""
        errors: dict[str, str] = {}
        if user_input is not None:
            badges = self._options().setdefault(CONF_BADGES, [])
            duplicate = any(
                badge[CONF_BADGE_ENTITY] == user_input[CONF_BADGE_ENTITY]
                and str(badge.get(CONF_BADGE_VALUE, STATE_ON))
                == user_input[CONF_BADGE_VALUE]
                for badge in badges
            )
            if duplicate:
                errors["base"] = "badge_already_configured"
            else:
                badges.append(dict(user_input))
                return await self.async_step_badges()

        return self.async_show_form(
            step_id="add_badge",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_BADGE_NAME): str,
                    vol.Required(CONF_BADGE_ENTITY): selector.EntitySelector(
                        selector.EntitySelectorConfig(
                            domain=["sensor", "binary_sensor"]
                        )
                    ),
                    vol.Required(CONF_BADGE_VALUE, default="on"): str,
                }
            ),
            errors=errors,
        )

    async def async_step_remove_badge(
        self, user_input: dict[str, Any] | None = None
    ) -> config_entries.ConfigFlowResult:
        """Remove an authorized badge."""
        badges = self._options().get(CONF_BADGES, [])
        if not badges:
            return await self.async_step_badges()

        badge_options = {
            str(index): (
                f"{badge[CONF_BADGE_NAME]} "
                f"({badge[CONF_BADGE_ENTITY]} = "
                f"{badge.get(CONF_BADGE_VALUE, 'on')})"
            )
            for index, badge in enumerate(badges)
        }
        if user_input is not None:
            del badges[int(user_input["badge_to_remove"])]
            return await self.async_step_badges()

        return self.async_show_form(
            step_id="remove_badge",
            data_schema=vol.Schema(
                {vol.Required("badge_to_remove"): vol.In(badge_options)}
            ),
        )
