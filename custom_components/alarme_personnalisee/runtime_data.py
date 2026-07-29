"""Runtime data for Alarme Personnalisée."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from homeassistant.config_entries import ConfigEntry

if TYPE_CHECKING:
    from .alarm_control_panel import AlarmePersonnaliseeEntity


@dataclass
class AlarmRuntimeData:
    """Data shared by the entities of one config entry."""

    alarm: AlarmePersonnaliseeEntity | None = None


type AlarmConfigEntry = ConfigEntry[AlarmRuntimeData]
