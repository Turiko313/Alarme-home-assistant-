"""Config flow for Alarme Personnalisée."""

from __future__ import annotations

from typing import Any

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.const import STATE_ON
from homeassistant.core import callback
from homeassistant.helpers import entity_registry as er
from homeassistant.helpers import selector

from .const import (
    CONF_ARM_HOME_ON_START,
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
    CONF_STARTUP_DELAY,
    CONF_TAG_ID,
    CONF_TAG_NAME,
    CONF_TRIGGER_TIME,
    CONF_VACATION_SENSORS,
    DEFAULT_ARM_HOME_ON_START,
    DEFAULT_ARMING_TIME,
    DEFAULT_CODE,
    DEFAULT_DELAY_TIME,
    DEFAULT_STARTUP_DELAY,
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
    _editing_badge_index: int | None = None

    def _options(self) -> dict[str, Any]:
        """Return a mutable copy used by the current flow."""
        if self._pending_options is None:
            self._pending_options = dict(self.config_entry.options)
            self._pending_options[CONF_BADGES] = [
                dict(badge) for badge in self.config_entry.options.get(CONF_BADGES, [])
            ]
        return self._pending_options

    def _badges(self) -> list[dict[str, Any]]:
        """Return the mutable badge list."""
        return self._options().setdefault(CONF_BADGES, [])

    @staticmethod
    def _short_tag_id(tag_id: str) -> str:
        """Return a readable shortened tag identifier."""
        return tag_id if len(tag_id) <= 16 else f"{tag_id[:8]}…{tag_id[-4:]}"

    def _known_tags(self) -> dict[str, str]:
        """Return native Home Assistant tag IDs indexed by readable names."""
        tags = {
            entry.unique_id: (
                entry.name
                or entry.original_name
                or entry.entity_id.removeprefix("tag.")
            )
            for entry in er.async_get(self.hass).entities.values()
            if entry.entity_id.startswith("tag.") and entry.platform == "tag"
        }
        for badge in self._badges():
            if tag_id := badge.get(CONF_TAG_ID):
                tags.setdefault(
                    str(tag_id),
                    str(
                        badge.get(CONF_TAG_NAME)
                        or f"Tag {self._short_tag_id(str(tag_id))}"
                    ),
                )
        return tags

    def _tag_choices(self) -> list[selector.SelectOptionDict]:
        """Return native tags as readable selector options."""
        return [
            {
                "value": tag_id,
                "label": f"{name} — {self._short_tag_id(tag_id)}",
            }
            for tag_id, name in sorted(
                self._known_tags().items(), key=lambda item: item[1].casefold()
            )
        ]

    def _normalize_tag_data(
        self,
        data: dict[str, Any],
        existing: dict[str, Any] | None = None,
    ) -> dict[str, str]:
        """Store a native tag with its current readable Home Assistant name."""
        tag_id = str(data[CONF_TAG_ID]).strip()
        known_name = self._known_tags().get(tag_id)
        existing_name = (
            existing.get(CONF_TAG_NAME)
            if existing is not None and existing.get(CONF_TAG_ID) == tag_id
            else None
        )
        return {
            CONF_BADGE_NAME: str(data[CONF_BADGE_NAME]).strip(),
            CONF_TAG_ID: tag_id,
            CONF_TAG_NAME: str(
                known_name or existing_name or f"Tag {self._short_tag_id(tag_id)}"
            ),
        }

    def _tag_data_schema(
        self,
        defaults: dict[str, Any] | None = None,
    ) -> vol.Schema:
        """Build the schema used to select a native Home Assistant tag."""
        defaults = defaults or {}
        tag_key = (
            vol.Required(CONF_TAG_ID, default=defaults[CONF_TAG_ID])
            if defaults.get(CONF_TAG_ID)
            else vol.Required(CONF_TAG_ID)
        )
        return vol.Schema(
            {
                vol.Required(
                    CONF_BADGE_NAME,
                    default=defaults.get(CONF_BADGE_NAME, ""),
                ): vol.All(str, vol.Length(min=1)),
                tag_key: selector.SelectSelector(
                    selector.SelectSelectorConfig(
                        options=self._tag_choices(),
                        custom_value=True,
                        mode=selector.SelectSelectorMode.DROPDOWN,
                        sort=True,
                    )
                ),
            }
        )

    def _badge_label(self, badge: dict[str, Any]) -> str:
        """Return a readable label for one badge credential."""
        if tag_id := badge.get(CONF_TAG_ID):
            tag_name = (
                self._known_tags().get(str(tag_id)) or badge.get(CONF_TAG_NAME) or "Tag"
            )
            return (
                f"{badge[CONF_BADGE_NAME]} — {tag_name} "
                f"({self._short_tag_id(str(tag_id))})"
            )
        return (
            f"{badge[CONF_BADGE_NAME]} — ancien lecteur "
            f"{badge.get(CONF_BADGE_ENTITY, '?')} = "
            f"{badge.get(CONF_BADGE_VALUE, STATE_ON)}"
        )

    def _badge_choices(self) -> dict[str, str]:
        """Return index-based badge choices for edit and removal forms."""
        return {
            str(index): self._badge_label(badge)
            for index, badge in enumerate(self._badges())
        }

    def _badges_description(self) -> str:
        """Return badges grouped by their friendly owner name."""
        grouped: dict[str, list[dict[str, Any]]] = {}
        for badge in self._badges():
            grouped.setdefault(badge[CONF_BADGE_NAME], []).append(badge)

        sections = []
        for name, badges in grouped.items():
            credentials = "\n".join(
                self._badge_description_line(badge) for badge in badges
            )
            label = "tag" if len(badges) == 1 else "tags"
            sections.append(f"**{name}** ({len(badges)} {label})\n{credentials}")
        return "\n\n".join(sections) or "-"

    def _badge_description_line(self, badge: dict[str, Any]) -> str:
        """Return one readable native-tag or legacy-reader description."""
        if tag_id := badge.get(CONF_TAG_ID):
            tag_name = (
                self._known_tags().get(str(tag_id)) or badge.get(CONF_TAG_NAME) or "Tag"
            )
            return f"- **{tag_name}** — `{self._short_tag_id(str(tag_id))}`"
        return (
            f"- Ancien lecteur `{badge.get(CONF_BADGE_ENTITY, '?')}` = "
            f"`{badge.get(CONF_BADGE_VALUE, STATE_ON)}`"
        )

    @staticmethod
    def _badge_identity(badge: dict[str, Any]) -> tuple[str, ...]:
        """Return the stable identity used for duplicate detection."""
        if tag_id := badge.get(CONF_TAG_ID):
            return ("tag", str(tag_id))
        return (
            "entity",
            str(badge.get(CONF_BADGE_ENTITY, "")),
            str(badge.get(CONF_BADGE_VALUE, STATE_ON)),
        )

    def _badge_is_duplicate(
        self,
        badge_data: dict[str, Any],
        *,
        ignored_index: int | None = None,
    ) -> bool:
        """Return whether a reader/value pair is already configured."""
        identity = self._badge_identity(badge_data)
        return any(
            index != ignored_index and self._badge_identity(badge) == identity
            for index, badge in enumerate(self._badges())
        )

    @staticmethod
    def _legacy_badge_data_schema(
        defaults: dict[str, Any] | None = None,
    ) -> vol.Schema:
        """Build the common badge credential schema."""
        defaults = defaults or {}
        return vol.Schema(
            {
                vol.Required(
                    CONF_BADGE_NAME,
                    default=defaults.get(CONF_BADGE_NAME, ""),
                ): str,
                vol.Required(
                    CONF_BADGE_ENTITY,
                    default=defaults.get(CONF_BADGE_ENTITY),
                ): selector.EntitySelector(
                    selector.EntitySelectorConfig(domain=["sensor", "binary_sensor"])
                ),
                vol.Required(
                    CONF_BADGE_VALUE,
                    default=defaults.get(CONF_BADGE_VALUE, STATE_ON),
                ): str,
            }
        )

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
                    vol.Optional(
                        CONF_STARTUP_DELAY,
                        default=options.get(CONF_STARTUP_DELAY, DEFAULT_STARTUP_DELAY),
                    ): vol.All(vol.Coerce(int), vol.Range(min=0, max=300)),
                    vol.Optional(
                        CONF_ARM_HOME_ON_START,
                        default=options.get(
                            CONF_ARM_HOME_ON_START,
                            DEFAULT_ARM_HOME_ON_START,
                        ),
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
            if action == "add_to_name":
                return await self.async_step_add_badge_to_name()
            if action == "edit":
                return await self.async_step_edit_badge()
            if action == "remove":
                return await self.async_step_remove_badge()
            return self.async_create_entry(title="", data=self._options())

        actions = {
            "add": "Ajouter un tag RFID / Add RFID tag",
            "done": "Terminer / Done",
        }
        if self._badges():
            actions = {
                "add": "Ajouter un tag RFID / Add RFID tag",
                "add_to_name": "Ajouter un tag à une personne / Add to name",
                "edit": "Modifier un tag / Edit",
                "remove": "Supprimer un tag / Remove",
                "done": "Terminer / Done",
            }
        return self.async_show_form(
            step_id="badges",
            data_schema=vol.Schema({vol.Required("action"): vol.In(actions)}),
            description_placeholders={
                "badges_list": self._badges_description(),
            },
        )

    async def async_step_add_badge(
        self, user_input: dict[str, Any] | None = None
    ) -> config_entries.ConfigFlowResult:
        """Add an authorized badge."""
        errors: dict[str, str] = {}
        if user_input is not None:
            tag_data = self._normalize_tag_data(user_input)
            if self._badge_is_duplicate(tag_data):
                errors["base"] = "badge_already_configured"
            else:
                self._badges().append(tag_data)
                return await self.async_step_badges()

        return self.async_show_form(
            step_id="add_badge",
            data_schema=self._tag_data_schema(user_input),
            errors=errors,
        )

    async def async_step_add_badge_to_name(
        self, user_input: dict[str, Any] | None = None
    ) -> config_entries.ConfigFlowResult:
        """Add another badge credential under an existing friendly name."""
        if not self._badges():
            return await self.async_step_add_badge()

        errors: dict[str, str] = {}
        if user_input is not None:
            tag_data = self._normalize_tag_data(
                {
                    CONF_BADGE_NAME: user_input["badge_owner"],
                    CONF_TAG_ID: user_input[CONF_TAG_ID],
                }
            )
            if self._badge_is_duplicate(tag_data):
                errors["base"] = "badge_already_configured"
            else:
                self._badges().append(tag_data)
                return await self.async_step_badges()

        names = list(dict.fromkeys(badge[CONF_BADGE_NAME] for badge in self._badges()))
        return self.async_show_form(
            step_id="add_badge_to_name",
            data_schema=vol.Schema(
                {
                    vol.Required("badge_owner"): vol.In({name: name for name in names}),
                    vol.Required(CONF_TAG_ID): selector.SelectSelector(
                        selector.SelectSelectorConfig(
                            options=self._tag_choices(),
                            custom_value=True,
                            mode=selector.SelectSelectorMode.DROPDOWN,
                            sort=True,
                        )
                    ),
                }
            ),
            errors=errors,
        )

    async def async_step_edit_badge(
        self, user_input: dict[str, Any] | None = None
    ) -> config_entries.ConfigFlowResult:
        """Select and edit an existing tag or legacy badge credential."""
        badges = self._badges()
        if not badges:
            return await self.async_step_badges()

        if self._editing_badge_index is None:
            if user_input is not None:
                self._editing_badge_index = int(user_input["badge_to_edit"])
                return await self.async_step_edit_badge()
            return self.async_show_form(
                step_id="edit_badge",
                data_schema=vol.Schema(
                    {vol.Required("badge_to_edit"): vol.In(self._badge_choices())}
                ),
            )

        existing = badges[self._editing_badge_index]
        errors: dict[str, str] = {}
        if user_input is not None:
            badge_data = (
                self._normalize_tag_data(user_input, existing)
                if CONF_TAG_ID in existing
                else {
                    CONF_BADGE_NAME: user_input[CONF_BADGE_NAME],
                    CONF_BADGE_ENTITY: user_input[CONF_BADGE_ENTITY],
                    CONF_BADGE_VALUE: user_input[CONF_BADGE_VALUE],
                }
            )
            if self._badge_is_duplicate(
                badge_data,
                ignored_index=self._editing_badge_index,
            ):
                errors["base"] = "badge_already_configured"
            else:
                badges[self._editing_badge_index] = badge_data
                self._editing_badge_index = None
                return await self.async_step_badges()

        defaults = user_input or existing
        data_schema = (
            self._tag_data_schema(defaults)
            if CONF_TAG_ID in existing
            else self._legacy_badge_data_schema(defaults)
        )
        return self.async_show_form(
            step_id="edit_badge",
            data_schema=data_schema,
            errors=errors,
        )

    async def async_step_remove_badge(
        self, user_input: dict[str, Any] | None = None
    ) -> config_entries.ConfigFlowResult:
        """Remove an authorized badge."""
        badges = self._options().get(CONF_BADGES, [])
        if not badges:
            return await self.async_step_badges()

        if user_input is not None:
            del badges[int(user_input["badge_to_remove"])]
            return await self.async_step_badges()

        return self.async_show_form(
            step_id="remove_badge",
            data_schema=vol.Schema(
                {vol.Required("badge_to_remove"): vol.In(self._badge_choices())}
            ),
        )
