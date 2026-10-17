"""Pytest fixtures and fake Home Assistant modules for integration tests."""

from __future__ import annotations

import sys
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from types import ModuleType
from typing import TYPE_CHECKING, Any

import pytest

if TYPE_CHECKING:
    from custom_components.helios_kwl_ec300._core.models import HeliosSnapshot


def _install_fake_voluptuous() -> None:
    module = ModuleType("voluptuous")

    class Schema:
        def __init__(self, schema: Any):
            self.schema = schema

        def __call__(self, value: Any) -> Any:
            return value

    def required(key: Any, default: Any = None) -> tuple[Any, Any]:
        return (key, default)

    def all_(*validators: Any) -> tuple[Any, ...]:
        return validators

    def coerce(type_: type[Any]) -> type[Any]:
        return type_

    def range_(*, min: int | None = None, max: int | None = None) -> tuple[int | None, int | None]:
        return (min, max)

    module_any: Any = module
    module_any.Schema = Schema
    module_any.Required = required
    module_any.All = all_
    module_any.Coerce = coerce
    module_any.Range = range_
    sys.modules["voluptuous"] = module


def _install_fake_homeassistant() -> None:
    homeassistant = ModuleType("homeassistant")
    homeassistant.__path__ = []
    sys.modules["homeassistant"] = homeassistant

    const = ModuleType("homeassistant.const")

    class Platform(str, Enum):
        FAN = "fan"
        NUMBER = "number"
        SELECT = "select"
        SENSOR = "sensor"

    class EntityCategory(str, Enum):
        CONFIG = "config"
        DIAGNOSTIC = "diagnostic"

    class UnitOfTemperature(str, Enum):
        CELSIUS = "degC"

    class UnitOfTime(str, Enum):
        MINUTES = "min"

    const_any: Any = const
    const_any.Platform = Platform
    const_any.EntityCategory = EntityCategory
    const_any.UnitOfTemperature = UnitOfTemperature
    const_any.UnitOfTime = UnitOfTime
    const_any.PERCENTAGE = "%"
    const_any.CONF_HOST = "host"
    const_any.CONF_PASSWORD = "password"
    sys.modules["homeassistant.const"] = const

    config_entries = ModuleType("homeassistant.config_entries")

    @dataclass(slots=True)
    class ConfigEntry:
        entry_id: str
        title: str
        unique_id: str | None
        data: dict[str, Any]
        options: dict[str, Any]

    class ConfigFlow:
        def __init_subclass__(cls, *, domain: str | None = None, **kwargs: Any) -> None:
            super().__init_subclass__(**kwargs)
            cls.DOMAIN = domain

        def __init__(self) -> None:
            self.hass: Any = None
            self._unique_id: str | None = None

        async def async_set_unique_id(self, unique_id: str) -> None:
            self._unique_id = unique_id

        def _abort_if_unique_id_configured(self, updates: dict[str, Any] | None = None) -> None:
            self._updates = updates

        def async_create_entry(
            self,
            *,
            title: str,
            data: dict[str, Any],
            options: dict[str, Any],
        ) -> dict[str, Any]:
            return {
                "type": "create_entry",
                "title": title,
                "data": data,
                "options": options,
            }

        def async_show_form(
            self,
            *,
            step_id: str,
            data_schema: Any,
            errors: dict[str, str],
        ) -> dict[str, Any]:
            return {
                "type": "form",
                "step_id": step_id,
                "data_schema": data_schema,
                "errors": errors,
            }

    config_entries_any: Any = config_entries
    config_entries_any.ConfigEntry = ConfigEntry
    config_entries_any.ConfigFlow = ConfigFlow
    sys.modules["homeassistant.config_entries"] = config_entries

    core = ModuleType("homeassistant.core")

    class ConfigEntriesManager:
        def __init__(self) -> None:
            self.forwarded: list[tuple[ConfigEntry, tuple[Any, ...]]] = []
            self.unloaded: list[tuple[ConfigEntry, tuple[Any, ...]]] = []
            self.updated_entries: list[tuple[ConfigEntry, dict[str, Any]]] = []

        async def async_forward_entry_setups(
            self,
            entry: ConfigEntry,
            platforms: tuple[Any, ...],
        ) -> None:
            self.forwarded.append((entry, platforms))

        async def async_unload_platforms(
            self,
            entry: ConfigEntry,
            platforms: tuple[Any, ...],
        ) -> bool:
            self.unloaded.append((entry, platforms))
            return True

        def async_update_entry(self, entry: ConfigEntry, *, options: dict[str, Any]) -> None:
            entry.options = options
            self.updated_entries.append((entry, options))

    class HomeAssistant:
        def __init__(self) -> None:
            self.data: dict[str, Any] = {}
            self.config_entries = ConfigEntriesManager()

    core_any: Any = core
    core_any.HomeAssistant = HomeAssistant
    sys.modules["homeassistant.core"] = core

    exceptions = ModuleType("homeassistant.exceptions")

    class ConfigEntryAuthFailed(Exception):
        pass

    exceptions_any: Any = exceptions
    exceptions_any.ConfigEntryAuthFailed = ConfigEntryAuthFailed
    sys.modules["homeassistant.exceptions"] = exceptions

    helpers_update = ModuleType("homeassistant.helpers.update_coordinator")

    class UpdateFailed(Exception):
        pass

    class DataUpdateCoordinator:
        def __class_getitem__(cls, item: Any) -> type[DataUpdateCoordinator]:
            return cls

        def __init__(
            self,
            hass: HomeAssistant,
            logger: Any,
            *,
            config_entry: ConfigEntry | None = None,
            name: str | None = None,
            update_interval: Any = None,
            always_update: bool = True,
        ) -> None:
            self.hass = hass
            self.logger = logger
            self.config_entry = config_entry
            self.name = name
            self.update_interval = update_interval
            self.always_update = always_update
            self.data: Any = None

        async def async_request_refresh(self) -> Any:
            coordinator_self: Any = self
            self.data = await coordinator_self._async_update_data()
            return self.data

        async def async_config_entry_first_refresh(self) -> Any:
            return await self.async_request_refresh()

    class CoordinatorEntity:
        def __class_getitem__(cls, item: Any) -> type[CoordinatorEntity]:
            return cls

        def __init__(self, coordinator: DataUpdateCoordinator, context: Any = None) -> None:
            self.coordinator = coordinator
            self.hass = coordinator.hass
            self.context = context
            self.state_written = False

        def async_write_ha_state(self) -> None:
            self.state_written = True

    helpers_update_any: Any = helpers_update
    helpers_update_any.DataUpdateCoordinator = DataUpdateCoordinator
    helpers_update_any.CoordinatorEntity = CoordinatorEntity
    helpers_update_any.UpdateFailed = UpdateFailed
    sys.modules["homeassistant.helpers.update_coordinator"] = helpers_update

    helpers_device = ModuleType("homeassistant.helpers.device_registry")
    helpers_device_any: Any = helpers_device
    helpers_device_any.CONNECTION_NETWORK_MAC = "mac"

    class DeviceInfo(dict):
        def __init__(self, **kwargs: Any) -> None:
            super().__init__(**kwargs)

    helpers_device_any.DeviceInfo = DeviceInfo
    sys.modules["homeassistant.helpers.device_registry"] = helpers_device

    helpers_entity_platform = ModuleType("homeassistant.helpers.entity_platform")
    helpers_entity_platform_any: Any = helpers_entity_platform
    helpers_entity_platform_any.AddEntitiesCallback = Any
    sys.modules["homeassistant.helpers.entity_platform"] = helpers_entity_platform

    diagnostics = ModuleType("homeassistant.components.diagnostics")

    def async_redact_data(data: Any, to_redact: set[str]) -> Any:
        if isinstance(data, dict):
            return {
                key: ("REDACTED" if key in to_redact else async_redact_data(value, to_redact))
                for key, value in data.items()
            }
        if isinstance(data, list):
            return [async_redact_data(item, to_redact) for item in data]
        return data

    diagnostics_any: Any = diagnostics
    diagnostics_any.async_redact_data = async_redact_data
    sys.modules["homeassistant.components.diagnostics"] = diagnostics

    components = ModuleType("homeassistant.components")
    components.__path__ = []
    sys.modules["homeassistant.components"] = components

    @dataclass(frozen=True, kw_only=True)
    class EntityDescription:
        key: str
        name: str
        icon: str | None = None
        entity_category: Any = None
        entity_registry_enabled_default: bool = True

    @dataclass(frozen=True, kw_only=True)
    class SensorEntityDescription(EntityDescription):
        device_class: Any = None
        native_unit_of_measurement: Any = None
        state_class: Any = None

    class FanEntity:
        pass

    class FanEntityFeature(int, Enum):
        TURN_ON = 1 << 7
        TURN_OFF = 1 << 8

    class NumberEntity:
        pass

    class SensorEntity:
        pass

    class SensorDeviceClass(str, Enum):
        TEMPERATURE = "temperature"

    class SensorStateClass(str, Enum):
        MEASUREMENT = "measurement"

    class NumberMode(str, Enum):
        BOX = "box"

    fan = ModuleType("homeassistant.components.fan")
    fan_any: Any = fan
    fan_any.FanEntity = FanEntity
    fan_any.FanEntityFeature = FanEntityFeature
    sys.modules["homeassistant.components.fan"] = fan

    number = ModuleType("homeassistant.components.number")
    number_any: Any = number
    number_any.NumberEntity = NumberEntity
    number_any.NumberMode = NumberMode
    sys.modules["homeassistant.components.number"] = number

    class SelectEntity:
        pass

    select = ModuleType("homeassistant.components.select")
    select_any: Any = select
    select_any.SelectEntity = SelectEntity
    sys.modules["homeassistant.components.select"] = select

    sensor = ModuleType("homeassistant.components.sensor")
    sensor_any: Any = sensor
    sensor_any.SensorDeviceClass = SensorDeviceClass
    sensor_any.SensorEntity = SensorEntity
    sensor_any.SensorEntityDescription = SensorEntityDescription
    sensor_any.SensorStateClass = SensorStateClass
    sys.modules["homeassistant.components.sensor"] = sensor


if "voluptuous" not in sys.modules:
    _install_fake_voluptuous()

if "homeassistant" not in sys.modules:
    _install_fake_homeassistant()

HA_COMPONENT_PATH = Path(__file__).resolve().parents[2]
if str(HA_COMPONENT_PATH) not in sys.path:
    sys.path.insert(0, str(HA_COMPONENT_PATH))


@pytest.fixture
def hass() -> Any:
    """Return a fake Home Assistant instance."""
    core_module: Any = sys.modules["homeassistant.core"]
    return core_module.HomeAssistant()


@pytest.fixture
def config_entry() -> Any:
    """Return a fake config entry for the Helios integration."""
    config_entries_module: Any = sys.modules["homeassistant.config_entries"]
    const_module: Any = sys.modules["homeassistant.const"]
    config_entry_cls = config_entries_module.ConfigEntry
    conf_host = const_module.CONF_HOST
    conf_password = const_module.CONF_PASSWORD

    return config_entry_cls(
        entry_id="entry-1",
        title="Helios KWL",
        unique_id="804b2001992a",
        data={conf_host: "helios.fritz.box", conf_password: "!helios!"},
        options={
            "scan_interval": 30,
            "party_duration_minutes": 90,
            "party_fan_stage": 3,
        },
    )


@pytest.fixture
def sample_snapshot() -> HeliosSnapshot:
    """Return a representative Helios snapshot for HA entity tests."""
    from custom_components.helios_kwl_ec300._core.models import (
        DeviceIdentity,
        FanSpeed,
        HeliosSnapshot,
        HeliosStatus,
        OperationMode,
        PartyState,
        Temperature,
        Temperatures,
    )

    return HeliosSnapshot(
        status=HeliosStatus(
            temperatures=Temperatures(
                outdoor=Temperature(
                    variable_id="v00104",
                    label="Outdoor air",
                    value_celsius=8.6,
                    raw_value="8.6",
                ),
                supply=Temperature(
                    variable_id="v00105",
                    label="Supply air",
                    value_celsius=22.3,
                    raw_value="22.3",
                ),
                exhaust=Temperature(
                    variable_id="v00106",
                    label="Exhaust air",
                    value_celsius=18.5,
                    raw_value="18.5",
                ),
                extract=Temperature(
                    variable_id="v00107",
                    label="Extract air",
                    value_celsius=20.1,
                    raw_value="20.1",
                ),
            ),
            fan_speed=FanSpeed(
                stage=2,
                stage_percent=24.0,
                stage_label="S2 - Reduced ventilation",
                rpm_supply=1234,
                rpm_extract=1256,
            ),
            operation_mode=OperationMode(
                effective="Automatisch (Automatic)",
                party=False,
                quiet=False,
                holiday=False,
                manual=False,
                automatic=True,
                humidity_control="Continuous (Stufenlos)",
                co2_control="Continuous (Stufenlos)",
                voc_control="Continuous (Stufenlos)",
            ),
            host="helios.fritz.box",
        ),
        party_state=PartyState(
            active=False,
            configured_duration_minutes=120,
            fan_stage=3,
            remaining_minutes=0,
        ),
        identity=DeviceIdentity(
            model="KWL EC 300W R",
            firmware_version="04232003.hGP",
            mac_address="80:4B:20:01:99:2A",
            state_flags="10001101000001110000000010000001",
        ),
    )


@pytest.fixture
def runtime_data(
    hass: Any,
    config_entry: Any,
    sample_snapshot: HeliosSnapshot,
) -> Any:
    """Return coordinator runtime data shared by entity tests."""
    from custom_components.helios_kwl_ec300.coordinator import (
        HeliosDataUpdateCoordinator,
        HeliosRuntimeData,
        HeliosSettings,
    )

    class FakeApi:
        async def get_snapshot(self) -> HeliosSnapshot:
            return sample_snapshot

        async def set_party_mode(self, duration_minutes: int, fan_stage: int) -> None:
            self.last_set = (duration_minutes, fan_stage)

        async def stop_party_mode(self) -> None:
            self.stopped = True

    api = FakeApi()
    coordinator = HeliosDataUpdateCoordinator(
        hass,
        config_entry,
        api,
        HeliosSettings(scan_interval_seconds=30, party_duration_minutes=90, party_fan_stage=3),
    )
    coordinator.data = sample_snapshot
    return HeliosRuntimeData(
        api=api,
        coordinator=coordinator,
        config_entry=config_entry,
        settings=coordinator.settings,
        device_identifier="804b2001992a",
    )
