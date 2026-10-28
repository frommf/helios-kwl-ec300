"""Switch entity for the Helios base automatic mode."""

from __future__ import annotations

from typing import Any

from homeassistant.components.switch import SwitchEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN
from .coordinator import HeliosRuntimeData
from .entity import HeliosEntity


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the base automatic-mode switch."""
    runtime_data = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([HeliosAutomaticModeSwitch(runtime_data)])


class HeliosAutomaticModeSwitch(HeliosEntity, SwitchEntity):
    """Control the base automatic mode independently of effective-mode overrides."""

    _attr_name = "Automatic mode"
    _attr_icon = "mdi:auto-mode"

    def __init__(self, runtime_data: HeliosRuntimeData) -> None:
        super().__init__(runtime_data, "automatic_mode")

    @property
    def is_on(self) -> bool:
        """Return the v00101 base state, including during party/quiet/holiday modes."""
        return not self.snapshot.status.operation_mode.manual

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Request automatic mode and let the coordinator refresh actual state."""
        await self.coordinator.async_set_automatic_mode(True)

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Request manual mode and let the coordinator refresh actual state."""
        await self.coordinator.async_set_automatic_mode(False)
