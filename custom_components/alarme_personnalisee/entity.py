"""Shared entity helpers for Alarme Personnalisée."""

from homeassistant.helpers.entity import DeviceInfo

from .const import DOMAIN
from .runtime_data import AlarmConfigEntry


def alarm_device_info(entry: AlarmConfigEntry) -> DeviceInfo:
    """Return stable device information for one alarm."""
    return DeviceInfo(
        identifiers={(DOMAIN, entry.entry_id)},
        name=entry.title,
        manufacturer="Alarme Personnalisée",
        model="Alarme virtuelle",
    )
