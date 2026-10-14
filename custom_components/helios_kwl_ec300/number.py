"""Local configuration numbers for party mode defaults."""

from __future__ import annotations

from homeassistant.components.number import NumberEntity, NumberMode
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import EntityCategory, UnitOfTime
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN
from .coordinator import HeliosRuntimeData, persist_settings
from .entity import HeliosEntity


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up local Helios configuration numbers."""
    runtime_data = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([HeliosPartyDurationNumber(runtime_data)])


class HeliosPartyDurationNumber(HeliosEntity, NumberEntity):
    """Persist the default party duration used by safe control entities."""

    _attr_name = "Default party duration"
    _attr_entity_category = EntityCategory.CONFIG
    _attr_icon = "mdi:timer-cog"
    _attr_native_min_value = 5
    _attr_native_max_value = 180
    _attr_native_step = 5
    _attr_native_unit_of_measurement = UnitOfTime.MINUTES
    _attr_mode = NumberMode.BOX

    def __init__(self, runtime_data: HeliosRuntimeData) -> None:
        super().__init__(runtime_data, "default_party_duration")

    @property
    def native_value(self) -> float:
        """Return the stored default party duration."""
        return float(self.runtime_data.settings.party_duration_minutes)

    async def async_set_native_value(self, value: float) -> None:
        """Persist a new default party duration."""
        self.runtime_data.settings.party_duration_minutes = int(value)
        persist_settings(self.hass, self.runtime_data)
        self.async_write_ha_state()
