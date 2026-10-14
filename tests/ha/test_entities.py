"""Tests for Helios Home Assistant entities."""

from __future__ import annotations

from unittest.mock import AsyncMock, Mock

import pytest

from custom_components.helios_kwl_ec300.const import (
    ATTR_EFFECTIVE_MODE,
    ATTR_RPM_EXTRACT,
    ATTR_RPM_SUPPLY,
    ATTR_STAGE,
    ATTR_STAGE_LABEL,
)
from custom_components.helios_kwl_ec300.entity import HeliosEntity
from custom_components.helios_kwl_ec300.fan import HeliosVentilationFan
from custom_components.helios_kwl_ec300.number import HeliosPartyDurationNumber
from custom_components.helios_kwl_ec300.select import HeliosPartyFanStageSelect
from custom_components.helios_kwl_ec300.sensor import SENSOR_DESCRIPTIONS, HeliosStateSensor


def test_base_entity_device_info(runtime_data) -> None:
    """Base entity exposes device registry information from the snapshot."""
    entity = HeliosEntity(runtime_data, "base")
    device_info = entity.device_info

    assert entity.snapshot == runtime_data.coordinator.data
    assert device_info.get("manufacturer") == "Helios"
    assert device_info.get("model") == "KWL EC 300W R"
    assert device_info.get("connections") == {("mac", "80:4B:20:01:99:2A")}


def test_fan_reflects_party_state(runtime_data) -> None:
    """Fan is_on reflects party_state.active; percentage shows current fan speed."""
    fan = HeliosVentilationFan(runtime_data)

    assert fan.is_on is False  # party_state.active is False in fixture
    assert fan.percentage == 24
    assert fan.speed_count == 100
    assert fan.extra_state_attributes == {
        ATTR_STAGE: 2,
        ATTR_STAGE_LABEL: "S2 - Reduced ventilation",
        ATTR_RPM_SUPPLY: 1234,
        ATTR_RPM_EXTRACT: 1256,
        ATTR_EFFECTIVE_MODE: "Automatisch (Automatic)",
    }


@pytest.mark.asyncio
async def test_fan_turn_on_starts_party_mode(runtime_data) -> None:
    """Turning the fan on delegates to async_start_party_mode."""
    fan = HeliosVentilationFan(runtime_data)
    runtime_data.coordinator.async_start_party_mode = AsyncMock()

    await fan.async_turn_on()

    runtime_data.coordinator.async_start_party_mode.assert_awaited_once_with()


@pytest.mark.asyncio
async def test_fan_turn_off_stops_party_mode(runtime_data) -> None:
    """Turning the fan off delegates to async_stop_party_mode."""
    fan = HeliosVentilationFan(runtime_data)
    runtime_data.coordinator.async_stop_party_mode = AsyncMock()

    await fan.async_turn_off()

    runtime_data.coordinator.async_stop_party_mode.assert_awaited_once_with()


@pytest.mark.asyncio
async def test_party_duration_number_persists_default(hass, runtime_data) -> None:
    """Duration number updates local settings and config entry options."""
    duration = HeliosPartyDurationNumber(runtime_data)
    duration.async_write_ha_state = Mock()

    await duration.async_set_native_value(120)

    assert runtime_data.settings.party_duration_minutes == 120
    assert runtime_data.config_entry.options["party_duration_minutes"] == 120
    duration.async_write_ha_state.assert_called_once_with()


@pytest.mark.asyncio
async def test_party_fan_stage_select_persists_default(hass, runtime_data) -> None:
    """Fan stage select shows current setting and persists new selection."""
    stage = HeliosPartyFanStageSelect(runtime_data)
    stage.async_write_ha_state = Mock()

    assert stage.current_option == "3"

    await stage.async_select_option("4")

    assert runtime_data.settings.party_fan_stage == 4
    assert runtime_data.config_entry.options["party_fan_stage"] == 4
    stage.async_write_ha_state.assert_called_once_with()


def test_sensor_entity_reads_from_snapshot(runtime_data) -> None:
    """Coordinator-backed sensors surface the expected native values."""
    by_key = {description.key: description for description in SENSOR_DESCRIPTIONS}

    supply_temp = HeliosStateSensor(runtime_data, by_key["supply_air_temperature"])
    firmware = HeliosStateSensor(runtime_data, by_key["firmware_version"])

    assert supply_temp.native_value == 22.3
    assert firmware.native_value == "04232003.hGP"
