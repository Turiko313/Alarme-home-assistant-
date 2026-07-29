"""Tests for the Alarme Personnalisée config and options flows."""

from homeassistant import config_entries
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.alarme_personnalisee.const import (
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
    DOMAIN,
)

FRONT_DOOR = "binary_sensor.front_door"
BACK_DOOR = "binary_sensor.back_door"
BADGE_READER = "sensor.badge_reader"


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


async def test_badge_options_add_duplicate_remove_and_save(
    hass: HomeAssistant,
) -> None:
    """Badges can be added, duplicate-checked, removed, and saved."""
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
        CONF_BADGE_NAME: "Alice",
        CONF_BADGE_ENTITY: BADGE_READER,
        CONF_BADGE_VALUE: "04-A1-B2",
    }
    result = await hass.config_entries.options.async_configure(result["flow_id"], badge)
    assert result["step_id"] == "badges"
    assert "Alice" in result["description_placeholders"]["badges_list"]

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
            CONF_BADGE_NAME: "Bob",
            CONF_BADGE_ENTITY: BADGE_READER,
            CONF_BADGE_VALUE: "04-C3-D4",
        },
    )
    assert result["step_id"] == "badges"

    result = await hass.config_entries.options.async_configure(
        result["flow_id"], {"action": "remove"}
    )
    assert result["step_id"] == "remove_badge"
    result = await hass.config_entries.options.async_configure(
        result["flow_id"], {"badge_to_remove": "0"}
    )
    assert result["step_id"] == "badges"
    assert "Alice" not in result["description_placeholders"]["badges_list"]
    assert "Bob" in result["description_placeholders"]["badges_list"]

    result = await hass.config_entries.options.async_configure(
        result["flow_id"], {"action": "done"}
    )
    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["data"][CONF_BADGES] == [
        {
            CONF_BADGE_NAME: "Bob",
            CONF_BADGE_ENTITY: BADGE_READER,
            CONF_BADGE_VALUE: "04-C3-D4",
        }
    ]


async def test_remove_badge_with_empty_list_returns_to_badges(
    hass: HomeAssistant,
) -> None:
    """Removing from an empty badge list safely returns to the badge menu."""
    entry = _entry(hass)
    result = await _open_options_step(hass, entry, "badges")
    result = await hass.config_entries.options.async_configure(
        result["flow_id"], {"action": "remove"}
    )
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "badges"
