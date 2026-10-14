"""Local configuration select entities for party mode defaults."""

from __future__ import annotations

from homeassistant.components.select import SelectEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import EntityCategory
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
    """Set up local Helios configuration selects."""
    runtime_data = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([HeliosPartyFanStageSelect(runtime_data)])


class HeliosPartyFanStageSelect(HeliosEntity, SelectEntity):
    """Persist the default party fan stage used by safe control entities."""

    _attr_name = "Default party fan stage"
    _attr_entity_category = EntityCategory.CONFIG
    _attr_icon = "mdi:fan-plus"
    _attr_options = ["1", "2", "3", "4"]

    def __init__(self, runtime_data: HeliosRuntimeData) -> None:
        super().__init__(runtime_data, "default_party_fan_stage")

    @property
    def current_option(self) -> str:
        """Return the current default party fan stage."""
        return str(self.runtime_data.settings.party_fan_stage)

    async def async_select_option(self, option: str) -> None:
        """Persist a new default party fan stage."""
        self.runtime_data.settings.party_fan_stage = int(option)
        persist_settings(self.hass, self.runtime_data)
        self.async_write_ha_state()
