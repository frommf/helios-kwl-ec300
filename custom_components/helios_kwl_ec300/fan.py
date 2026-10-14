"""Fan entity for Helios — displays current speed and controls party mode."""

from __future__ import annotations

from typing import Any

from homeassistant.components.fan import FanEntity, FanEntityFeature
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import (
    ATTR_EFFECTIVE_MODE,
    ATTR_RPM_EXTRACT,
    ATTR_RPM_SUPPLY,
    ATTR_STAGE,
    ATTR_STAGE_LABEL,
    DOMAIN,
)
from .coordinator import HeliosRuntimeData
from .entity import HeliosEntity


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the read-only fan entity."""
    runtime_data = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([HeliosVentilationFan(runtime_data)])


class HeliosVentilationFan(HeliosEntity, FanEntity):
    """Fan entity: shows current speed and toggles party mode on/off."""

    _attr_name = "Ventilation"
    _attr_supported_features = FanEntityFeature.TURN_ON | FanEntityFeature.TURN_OFF
    _attr_icon = "mdi:fan"

    def __init__(self, runtime_data: HeliosRuntimeData) -> None:
        super().__init__(runtime_data, "ventilation")

    @property
    def is_on(self) -> bool:
        """Return True when party mode is active."""
        return self.snapshot.party_state.active

    async def async_turn_on(
        self,
        percentage: int | None = None,
        preset_mode: str | None = None,
        **kwargs: Any,
    ) -> None:
        """Start party mode using the configured duration and fan stage."""
        await self.coordinator.async_start_party_mode()

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Stop party mode."""
        await self.coordinator.async_stop_party_mode()

    @property
    def percentage(self) -> int | None:
        """Return the current fan percentage for dashboard display."""
        percentage = self.snapshot.status.fan_speed.stage_percent
        if percentage is None:
            return None
        return int(round(percentage))

    @property
    def speed_count(self) -> int:
        """Return the supported speed count for percentage display."""
        return 100

    @property
    def extra_state_attributes(self) -> dict[str, object]:
        """Expose the richer fan state for dashboards and templates."""
        fan_speed = self.snapshot.status.fan_speed
        return {
            ATTR_STAGE: fan_speed.stage,
            ATTR_STAGE_LABEL: fan_speed.stage_label,
            ATTR_RPM_SUPPLY: fan_speed.rpm_supply,
            ATTR_RPM_EXTRACT: fan_speed.rpm_extract,
            ATTR_EFFECTIVE_MODE: self.snapshot.status.operation_mode.effective,
        }
