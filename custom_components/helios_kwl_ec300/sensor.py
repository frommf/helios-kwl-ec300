"""Sensor platform for Helios status values."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import PERCENTAGE, EntityCategory, UnitOfTemperature
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from ._core.models import HeliosSnapshot
from .const import DOMAIN
from .coordinator import HeliosRuntimeData
from .entity import HeliosEntity


@dataclass(frozen=True, kw_only=True)
class HeliosSensorDescription(SensorEntityDescription):
    """Describe a coordinator-backed Helios sensor."""

    value_fn: Callable[[HeliosSnapshot], Any]


SENSOR_DESCRIPTIONS: tuple[HeliosSensorDescription, ...] = (
    HeliosSensorDescription(
        key="outdoor_air_temperature",
        name="Outdoor air",
        device_class=SensorDeviceClass.TEMPERATURE,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda snapshot: snapshot.status.temperatures.outdoor.value_celsius,
    ),
    HeliosSensorDescription(
        key="supply_air_temperature",
        name="Supply air",
        device_class=SensorDeviceClass.TEMPERATURE,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda snapshot: snapshot.status.temperatures.supply.value_celsius,
    ),
    HeliosSensorDescription(
        key="exhaust_air_temperature",
        name="Exhaust air",
        device_class=SensorDeviceClass.TEMPERATURE,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda snapshot: snapshot.status.temperatures.exhaust.value_celsius,
    ),
    HeliosSensorDescription(
        key="extract_air_temperature",
        name="Extract air",
        device_class=SensorDeviceClass.TEMPERATURE,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda snapshot: snapshot.status.temperatures.extract.value_celsius,
    ),
    HeliosSensorDescription(
        key="fan_stage",
        name="Fan stage",
        icon="mdi:stairs",
        value_fn=lambda snapshot: snapshot.status.fan_speed.stage,
    ),
    HeliosSensorDescription(
        key="fan_stage_percent",
        name="Fan stage percent",
        native_unit_of_measurement=PERCENTAGE,
        icon="mdi:fan-chevron-up",
        value_fn=lambda snapshot: (
            int(round(snapshot.status.fan_speed.stage_percent))
            if snapshot.status.fan_speed.stage_percent is not None
            else None
        ),
    ),
    HeliosSensorDescription(
        key="supply_fan_rpm",
        name="Supply fan RPM",
        native_unit_of_measurement="rpm",
        icon="mdi:fan",
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda snapshot: snapshot.status.fan_speed.rpm_supply,
    ),
    HeliosSensorDescription(
        key="extract_fan_rpm",
        name="Extract fan RPM",
        native_unit_of_measurement="rpm",
        icon="mdi:fan",
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda snapshot: snapshot.status.fan_speed.rpm_extract,
    ),
    HeliosSensorDescription(
        key="host",
        name="Host",
        entity_category=EntityCategory.DIAGNOSTIC,
        icon="mdi:ip-network",
        value_fn=lambda snapshot: snapshot.status.host,
    ),
    HeliosSensorDescription(
        key="firmware_version",
        name="Firmware version",
        entity_category=EntityCategory.DIAGNOSTIC,
        icon="mdi:chip",
        value_fn=lambda snapshot: (
            snapshot.identity.firmware_version if snapshot.identity is not None else None
        ),
    ),
    HeliosSensorDescription(
        key="mac_address",
        name="MAC address",
        entity_category=EntityCategory.DIAGNOSTIC,
        icon="mdi:network",
        entity_registry_enabled_default=False,
        value_fn=lambda snapshot: (
            snapshot.identity.mac_address if snapshot.identity is not None else None
        ),
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Helios sensors."""
    runtime_data = hass.data[DOMAIN][entry.entry_id]
    async_add_entities(
        HeliosStateSensor(runtime_data, description) for description in SENSOR_DESCRIPTIONS
    )


class HeliosStateSensor(HeliosEntity, SensorEntity):
    """Coordinator-backed Helios sensor."""

    entity_description: HeliosSensorDescription

    def __init__(
        self, runtime_data: HeliosRuntimeData, description: HeliosSensorDescription
    ) -> None:
        super().__init__(runtime_data, description.key)
        self.entity_description = description
        self._attr_name = description.name

    @property
    def native_value(self) -> Any:
        """Return the current sensor value from the coordinator snapshot."""
        return self.entity_description.value_fn(self.snapshot)
