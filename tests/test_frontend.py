"""Tests for the bundled Lovelace card."""

from homeassistant.core import HomeAssistant
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.alarme_personnalisee import CARD_URL
from custom_components.alarme_personnalisee.const import DOMAIN


async def test_lovelace_card_is_served(hass: HomeAssistant, hass_client) -> None:
    """The integration exposes its JavaScript card as a module resource."""
    entry = MockConfigEntry(domain=DOMAIN, title="Maison", data={})
    entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    client = await hass_client()
    response = await client.get(CARD_URL)

    assert response.status == 200
    assert "alarme-personnalisee-card" in await response.text()
    assert response.content_type in {"application/javascript", "text/javascript"}
