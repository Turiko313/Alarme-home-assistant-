"""Config flow for Alarme Personnalisée integration."""
from __future__ import annotations

from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.core import callback
from homeassistant.helpers import selector

from .const import DOMAIN, CONF_BADGES, CONF_BADGE_NAME, CONF_BADGE_ENTITY


class AlarmePersonnaliseeConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Alarme Personnalisée."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> config_entries.FlowResult:
        """Handle the initial step."""
        if user_input is not None:
            return self.async_create_entry(title="Alarme Personnalisée", data={})

        return self.async_show_form(step_id="user")

    @staticmethod
    @callback
    def async_get_options_flow(
        config_entry: config_entries.ConfigEntry,
    ) -> AlarmePersonnaliseeOptionsFlow:
        """Get the options flow for this handler."""
        return AlarmePersonnaliseeOptionsFlow(config_entry)


class AlarmePersonnaliseeOptionsFlow(config_entries.OptionsFlow):
    """Handle options flow for Alarme Personnalisée."""

    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        """Initialize options flow."""
        self._config_entry = config_entry

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> config_entries.FlowResult:
        """Manage the options."""
        return self.async_show_menu(
            step_id="init",
            menu_options=["general", "sensors", "badges"],
        )

    async def async_step_general(
        self, user_input: dict[str, Any] | None = None
    ) -> config_entries.FlowResult:
        """Manage general options."""
        if user_input is not None:
            # Merge with existing options
            new_options = {**self._config_entry.options, **user_input}
            return self.async_create_entry(title="", data=new_options)

        options = self._config_entry.options
        data_schema = vol.Schema(
            {
                vol.Optional("code", default=options.get("code", "")): str,
                vol.Optional(
                    "require_arm_code", default=options.get("require_arm_code", False)
                ): bool,
                vol.Optional(
                    "require_disarm_code",
                    default=options.get("require_disarm_code", False),
                ): bool,
                vol.Optional(
                    "emergency_code", default=options.get("emergency_code", "")
                ): str,
                vol.Optional(
                    "arming_time", default=options.get("arming_time", 30)
                ): vol.All(vol.Coerce(int), vol.Range(min=0)),
                vol.Optional(
                    "delay_time", default=options.get("delay_time", 30)
                ): vol.All(vol.Coerce(int), vol.Range(min=0)),
                vol.Optional(
                    "trigger_time", default=options.get("trigger_time", 180)
                ): vol.All(vol.Coerce(int), vol.Range(min=0)),
                vol.Optional(
                    "rearm_after_trigger",
                    default=options.get("rearm_after_trigger", False),
                ): bool,
            }
        )

        return self.async_show_form(step_id="general", data_schema=data_schema)

    async def async_step_sensors(
        self, user_input: dict[str, Any] | None = None
    ) -> config_entries.FlowResult:
        """Manage sensor options."""
        if user_input is not None:
            # Merge with existing options
            new_options = {**self._config_entry.options, **user_input}
            return self.async_create_entry(title="", data=new_options)

        options = self._config_entry.options
        data_schema = vol.Schema(
            {
                vol.Optional(
                    "away_sensors", default=options.get("away_sensors", [])
                ): selector.EntitySelector(
                    selector.EntitySelectorConfig(domain="binary_sensor", multiple=True)
                ),
                vol.Optional(
                    "home_sensors", default=options.get("home_sensors", [])
                ): selector.EntitySelector(
                    selector.EntitySelectorConfig(domain="binary_sensor", multiple=True)
                ),
                vol.Optional(
                    "vacation_sensors", default=options.get("vacation_sensors", [])
                ): selector.EntitySelector(
                    selector.EntitySelectorConfig(domain="binary_sensor", multiple=True)
                ),
            }
        )

        return self.async_show_form(step_id="sensors", data_schema=data_schema)

    async def async_step_badges(
        self, user_input: dict[str, Any] | None = None
    ) -> config_entries.FlowResult:
        """Manage badge options."""
        if user_input is not None:
            if user_input.get("action") == "add":
                return await self.async_step_add_badge()
            elif user_input.get("action") == "remove":
                return await self.async_step_remove_badge()
            else:
                return self.async_create_entry(title="", data=self._config_entry.options)

        badges = self._config_entry.options.get(CONF_BADGES, [])
        
        description = "Badges configures :\n"
        if badges:
            for badge in badges:
                description += f"- {badge[CONF_BADGE_NAME]} ({badge[CONF_BADGE_ENTITY]})\n"
        else:
            description += "Aucun badge configure\n"

        return self.async_show_form(
            step_id="badges",
            data_schema=vol.Schema(
                {
                    vol.Required("action"): vol.In(
                        {
                            "add": "Ajouter un badge",
                            "remove": "Supprimer un badge",
                            "done": "Terminer",
                        }
                    ),
                }
            ),
            description_placeholders={"badges_list": description},
        )

    async def async_step_add_badge(
        self, user_input: dict[str, Any] | None = None
    ) -> config_entries.FlowResult:
        """Add a new badge."""
        if user_input is not None:
            badges = self._config_entry.options.get(CONF_BADGES, [])
            badges.append(
                {
                    CONF_BADGE_NAME: user_input[CONF_BADGE_NAME],
                    CONF_BADGE_ENTITY: user_input[CONF_BADGE_ENTITY],
                }
            )
            new_options = {**self._config_entry.options, CONF_BADGES: badges}
            self.hass.config_entries.async_update_entry(
                self._config_entry, options=new_options
            )
            return await self.async_step_badges()

        return self.async_show_form(
            step_id="add_badge",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_BADGE_NAME): str,
                    vol.Required(CONF_BADGE_ENTITY): selector.EntitySelector(
                        selector.EntitySelectorConfig(domain=["sensor", "binary_sensor"])
                    ),
                }
            ),
        )

    async def async_step_remove_badge(
        self, user_input: dict[str, Any] | None = None
    ) -> config_entries.FlowResult:
        """Remove a badge."""
        badges = self._config_entry.options.get(CONF_BADGES, [])
        
        if not badges:
            return await self.async_step_badges()

        if user_input is not None:
            badge_to_remove = user_input["badge_to_remove"]
            badges = [b for b in badges if f"{b[CONF_BADGE_NAME]} ({b[CONF_BADGE_ENTITY]})" != badge_to_remove]
            new_options = {**self._config_entry.options, CONF_BADGES: badges}
            self.hass.config_entries.async_update_entry(
                self._config_entry, options=new_options
            )
            return await self.async_step_badges()

        badge_options = {
            f"{badge[CONF_BADGE_NAME]} ({badge[CONF_BADGE_ENTITY]})": f"{badge[CONF_BADGE_NAME]} ({badge[CONF_BADGE_ENTITY]})"
            for badge in badges
        }

        return self.async_show_form(
            step_id="remove_badge",
            data_schema=vol.Schema(
                {
                    vol.Required("badge_to_remove"): vol.In(badge_options),
                }
            ),
        )
