"""Tests for the Alarme Personnalisée config and options flows."""

from homeassistant import config_entries
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType
from homeassistant.helpers import entity_registry as er
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.alarme_personnalisee.const import (
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
    DOMAIN,
)

FRONT_DOOR = "binary_sensor.front_door"
BACK_DOOR = "binary_sensor.back_door"
BADGE_READER = "sensor.badge_reader"
SECOND_BADGE_READER = "sensor.second_badge_reader"
TAG_FRANCK_HOME = "11111111-1111-1111-1111-111111111111"
TAG_FRANCK_CAR = "22222222-2222-2222-2222-222222222222"
TAG_FRANCK_KEYS = "33333333-3333-3333-3333-333333333333"
TAG_FRANCK_UPDATED = "44444444-4444-4444-4444-444444444444"


def _register_tag(hass: HomeAssistant, tag_id: str, name: str) -> None:
    """Register one native Home Assistant tag for selector tests."""
    er.async_get(hass).async_get_or_create(
        "tag",
        "tag",
        tag_id,
        original_name=name,
    )


def _entry(hass: HomeAssistant, options: dict | None = None) -> MockConfigEntry:
    """Create an unloaded config entry for options-flow tests."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        title="Maison",
        data={},
        options=options or {},
    )
    entry.add_to_hass(hass)
    return entry


async def _open_options_step(
    hass: HomeAssistant,
    entry: MockConfigEntry,
    step_id: str,
) -> dict:
    """Open one step from the options menu."""
    result = await hass.config_entries.options.async_init(entry.entry_id)
    assert result["type"] is FlowResultType.MENU
    assert result["menu_options"] == ["general", "sensors", "badges"]
    return await hass.config_entries.options.async_configure(
        result["flow_id"], {"next_step_id": step_id}
    )


async def test_config_flow_creates_alarm(hass: HomeAssistant) -> None:
    """The user flow shows its form and creates an entry."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": config_entries.SOURCE_USER},
    )
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "user"

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {CONF_NAME: "Alarme maison"}
    )
    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["title"] == "Alarme maison"
    assert result["data"] == {}


async def test_general_options_flow(hass: HomeAssistant) -> None:
    """General options preserve existing values and validate all fields."""
    entry = _entry(hass, {CONF_AWAY_SENSORS: [FRONT_DOOR]})
    result = await _open_options_step(hass, entry, "general")
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "general"

    general_options = {
        CONF_CODE: "2468",
        CONF_REQUIRE_ARM_CODE: True,
        CONF_REQUIRE_DISARM_CODE: True,
        CONF_EMERGENCY_CODE: "9999",
        CONF_ARMING_TIME: 15,
        CONF_DELAY_TIME: 20,
        CONF_TRIGGER_TIME: 120,
        CONF_REARM_AFTER_TRIGGER: True,
        CONF_STARTUP_DELAY: 45,
        CONF_ARM_HOME_ON_START: True,
    }
    result = await hass.config_entries.options.async_configure(
        result["flow_id"], general_options
    )
    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["data"] == {
        CONF_AWAY_SENSORS: [FRONT_DOOR],
        **general_options,
    }


async def test_sensor_options_flow(hass: HomeAssistant) -> None:
    """Sensor options can be displayed and saved for every armed mode."""
    entry = _entry(hass, {CONF_CODE: "1234"})
    result = await _open_options_step(hass, entry, "sensors")
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "sensors"

    sensor_options = {
        CONF_AWAY_SENSORS: [FRONT_DOOR, BACK_DOOR],
        CONF_HOME_SENSORS: [BACK_DOOR],
        CONF_VACATION_SENSORS: [FRONT_DOOR],
    }
    result = await hass.config_entries.options.async_configure(
        result["flow_id"], sensor_options
    )
    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["data"] == {CONF_CODE: "1234", **sensor_options}


async def test_badge_options_group_add_edit_remove_and_save(
    hass: HomeAssistant,
) -> None:
    """Native tags are readable and can be added, edited, and removed."""
    _register_tag(hass, TAG_FRANCK_HOME, "Franck appartement")
    _register_tag(hass, TAG_FRANCK_CAR, "Franck voiture")
    _register_tag(hass, TAG_FRANCK_KEYS, "Franck clés")
    _register_tag(hass, TAG_FRANCK_UPDATED, "Franck bureau")
    entry = _entry(hass)
    result = await _open_options_step(hass, entry, "badges")
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "badges"
    assert result["description_placeholders"]["badges_list"] == "-"

    result = await hass.config_entries.options.async_configure(
        result["flow_id"], {"action": "add"}
    )
    assert result["step_id"] == "add_badge"

    badge = {
        CONF_BADGE_NAME: "Franck",
        CONF_TAG_ID: TAG_FRANCK_HOME,
    }
    result = await hass.config_entries.options.async_configure(result["flow_id"], badge)
    assert result["step_id"] == "badges"
    badge_list = result["description_placeholders"]["badges_list"]
    assert "**Franck** (1 tag)" in badge_list
    assert "Franck appartement" in badge_list
    assert "11111111…1111" in badge_list

    result = await hass.config_entries.options.async_configure(
        result["flow_id"], {"action": "add"}
    )
    result = await hass.config_entries.options.async_configure(result["flow_id"], badge)
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "add_badge"
    assert result["errors"] == {"base": "badge_already_configured"}

    result = await hass.config_entries.options.async_configure(
        result["flow_id"],
        {
            CONF_BADGE_NAME: "Franck",
            CONF_TAG_ID: TAG_FRANCK_CAR,
        },
    )
    assert result["step_id"] == "badges"
    assert "**Franck** (2 tags)" in result["description_placeholders"]["badges_list"]

    result = await hass.config_entries.options.async_configure(
        result["flow_id"], {"action": "add_to_name"}
    )
    assert result["step_id"] == "add_badge_to_name"
    result = await hass.config_entries.options.async_configure(
        result["flow_id"],
        {
            "badge_owner": "Franck",
            CONF_TAG_ID: TAG_FRANCK_KEYS,
        },
    )
    assert result["step_id"] == "badges"
    assert "**Franck** (3 tags)" in result["description_placeholders"]["badges_list"]

    result = await hass.config_entries.options.async_configure(
        result["flow_id"], {"action": "edit"}
    )
    assert result["step_id"] == "edit_badge"
    result = await hass.config_entries.options.async_configure(
        result["flow_id"], {"badge_to_edit": "1"}
    )
    assert result["step_id"] == "edit_badge"

    result = await hass.config_entries.options.async_configure(
        result["flow_id"],
        {
            CONF_BADGE_NAME: "Franck",
            CONF_TAG_ID: TAG_FRANCK_HOME,
        },
    )
    assert result["errors"] == {"base": "badge_already_configured"}

    result = await hass.config_entries.options.async_configure(
        result["flow_id"],
        {
            CONF_BADGE_NAME: "Franck",
            CONF_TAG_ID: TAG_FRANCK_UPDATED,
        },
    )
    assert result["step_id"] == "badges"
    assert "Franck bureau" in result["description_placeholders"]["badges_list"]

    result = await hass.config_entries.options.async_configure(
        result["flow_id"], {"action": "remove"}
    )
    assert result["step_id"] == "remove_badge"
    result = await hass.config_entries.options.async_configure(
        result["flow_id"], {"badge_to_remove": "0"}
    )
    assert result["step_id"] == "badges"
    assert "**Franck** (2 tags)" in result["description_placeholders"]["badges_list"]
    assert "Franck appartement" not in result["description_placeholders"]["badges_list"]

    result = await hass.config_entries.options.async_configure(
        result["flow_id"], {"action": "done"}
    )
    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["data"][CONF_BADGES] == [
        {
            CONF_BADGE_NAME: "Franck",
            CONF_TAG_ID: TAG_FRANCK_UPDATED,
            CONF_TAG_NAME: "Franck bureau",
        },
        {
            CONF_BADGE_NAME: "Franck",
            CONF_TAG_ID: TAG_FRANCK_KEYS,
            CONF_TAG_NAME: "Franck clés",
        },
    ]


async def test_remove_badge_with_empty_list_returns_to_badges(
    hass: HomeAssistant,
) -> None:
    """An empty badge list only offers add and done actions."""
    entry = _entry(hass)
    result = await _open_options_step(hass, entry, "badges")
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "badges"
    action_schema = next(iter(result["data_schema"].schema.values()))
    assert set(action_schema.container) == {"add", "done"}


async def test_existing_badges_are_grouped_without_migration(
    hass: HomeAssistant,
) -> None:
    """Existing flat badge options appear grouped under their friendly names."""
    entry = _entry(
        hass,
        {
            CONF_BADGES: [
                {
                    CONF_BADGE_NAME: "Alice",
                    CONF_BADGE_ENTITY: BADGE_READER,
                    CONF_BADGE_VALUE: "04-A1-B2",
                },
                {
                    CONF_BADGE_NAME: "Alice",
                    CONF_BADGE_ENTITY: SECOND_BADGE_READER,
                    CONF_BADGE_VALUE: "04-C3-D4",
                },
            ]
        },
    )

    result = await _open_options_step(hass, entry, "badges")

    badge_list = result["description_placeholders"]["badges_list"]
    assert "**Alice** (2 tags)" in badge_list
    assert BADGE_READER in badge_list
    assert SECOND_BADGE_READER in badge_list
