"""Select entities for normal fan control and local party defaults."""

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
    """Set up normal fan control and local party configuration selects."""
    runtime_data = hass.data[DOMAIN][entry.entry_id]
    async_add_entities(
        [
            HeliosFanStageSelect(runtime_data),
            HeliosPartyFanStageSelect(runtime_data),
        ]
    )


class HeliosFanStageSelect(HeliosEntity, SelectEntity):
    """Control the raw base fan stage without changing party display semantics."""

    _attr_name = "Fan stage control"
    _attr_icon = "mdi:fan"
    _attr_options = ["1", "2", "3", "4"]

    def __init__(self, runtime_data: HeliosRuntimeData) -> None:
        super().__init__(runtime_data, "fan_stage_control")

    @property
    def current_option(self) -> str | None:
        """Return the raw v00102 stage, never the party target stage."""
        stage = self.snapshot.status.fan_speed.base_stage
        return str(stage) if stage in (1, 2, 3, 4) else None

    async def async_select_option(self, option: str) -> None:
        """Request a normal stage, which also requests manual mode."""
        if option not in self._attr_options:
            raise ValueError("Fan stage must be one of 1, 2, 3, or 4")
        await self.coordinator.async_set_fan_stage(int(option))


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
