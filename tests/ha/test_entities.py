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
    DOMAIN,
)
from custom_components.helios_kwl_ec300.entity import HeliosEntity
from custom_components.helios_kwl_ec300.fan import HeliosVentilationFan
from custom_components.helios_kwl_ec300.number import HeliosPartyDurationNumber
from custom_components.helios_kwl_ec300.select import (
    HeliosFanStageSelect,
    HeliosPartyFanStageSelect,
)
from custom_components.helios_kwl_ec300.select import (
    async_setup_entry as async_setup_select,
)
from custom_components.helios_kwl_ec300.sensor import SENSOR_DESCRIPTIONS, HeliosStateSensor
from custom_components.helios_kwl_ec300.switch import (
    HeliosAutomaticModeSwitch,
)
from custom_components.helios_kwl_ec300.switch import (
    async_setup_entry as async_setup_switch,
)


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


def test_operating_entities_use_base_state_and_are_not_config(runtime_data) -> None:
    """The new operating entities expose base state rather than local configuration."""
    stage = HeliosFanStageSelect(runtime_data)
    automatic = HeliosAutomaticModeSwitch(runtime_data)

    assert stage.current_option == "2"
    assert stage._attr_options == ["1", "2", "3", "4"]
    assert automatic.is_on is True
    assert getattr(stage, "_attr_entity_category", None) is None
    assert getattr(automatic, "_attr_entity_category", None) is None


def test_operating_entities_ignore_party_display_override(runtime_data) -> None:
    """Party target/effective state does not replace base stage and automatic mode."""
    snapshot = runtime_data.coordinator.data
    status = snapshot.status.model_copy(
        update={
            "fan_speed": snapshot.status.fan_speed.model_copy(update={"stage": 4, "base_stage": 1}),
            "operation_mode": snapshot.status.operation_mode.model_copy(
                update={
                    "effective": "Partybetrieb (Party mode)",
                    "party": True,
                    "manual": False,
                    "automatic": False,
                }
            ),
        }
    )
    runtime_data.coordinator.data = snapshot.model_copy(update={"status": status})

    assert HeliosFanStageSelect(runtime_data).current_option == "1"
    assert HeliosAutomaticModeSwitch(runtime_data).is_on is True


@pytest.mark.asyncio
async def test_fan_stage_select_delegates_and_rejects_other_options(runtime_data) -> None:
    """Only stages 1–4 can reach the coordinator fan-stage operation."""
    stage = HeliosFanStageSelect(runtime_data)
    runtime_data.coordinator.async_set_fan_stage = AsyncMock()

    await stage.async_select_option("3")

    runtime_data.coordinator.async_set_fan_stage.assert_awaited_once_with(3)

    with pytest.raises(ValueError, match="1, 2, 3, or 4"):
        await stage.async_select_option("5")

    runtime_data.coordinator.async_set_fan_stage.assert_awaited_once_with(3)


@pytest.mark.asyncio
async def test_automatic_switch_delegates_on_and_off(runtime_data) -> None:
    """The switch controls base automatic mode without optimistic state writes."""
    automatic = HeliosAutomaticModeSwitch(runtime_data)
    runtime_data.coordinator.async_set_automatic_mode = AsyncMock()

    await automatic.async_turn_off()
    await automatic.async_turn_on()

    assert runtime_data.coordinator.async_set_automatic_mode.await_args_list == [
        ((False,), {}),
        ((True,), {}),
    ]


@pytest.mark.asyncio
async def test_operating_platform_setup_adds_new_entities(hass, runtime_data) -> None:
    """Select and switch setup register the normal operating controls."""
    hass.data[DOMAIN] = {runtime_data.config_entry.entry_id: runtime_data}
    select_entities = []
    switch_entities = []

    await async_setup_select(hass, runtime_data.config_entry, select_entities.extend)
    await async_setup_switch(hass, runtime_data.config_entry, switch_entities.extend)

    assert [type(entity) for entity in select_entities] == [
        HeliosFanStageSelect,
        HeliosPartyFanStageSelect,
    ]
    assert [type(entity) for entity in switch_entities] == [HeliosAutomaticModeSwitch]


def test_sensor_entity_reads_from_snapshot(runtime_data) -> None:
    """Coordinator-backed sensors surface the expected native values."""
    by_key = {description.key: description for description in SENSOR_DESCRIPTIONS}

    supply_temp = HeliosStateSensor(runtime_data, by_key["supply_air_temperature"])
    firmware = HeliosStateSensor(runtime_data, by_key["firmware_version"])

    assert supply_temp.native_value == 22.3
    assert firmware.native_value == "04232003.hGP"
