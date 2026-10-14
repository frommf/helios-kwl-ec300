"""Tests for Pydantic data models."""

import json
from datetime import datetime

import pytest
from pydantic import ValidationError

from custom_components.helios_kwl_ec300._core.constants import (
    MODE_AUTOMATIC,
    MODE_PARTY,
)
from custom_components.helios_kwl_ec300._core.models import (
    DeviceIdentity,
    FanSpeed,
    HeliosSnapshot,
    HeliosStatus,
    OperationMode,
    PartyModeConfig,
    PartyState,
    Temperature,
    Temperatures,
)


class TestTemperature:
    """Tests for Temperature model."""

    def test_valid_temperature(self):
        """Test creating a valid temperature reading."""
        temp = Temperature(
            variable_id="v00104",
            label="Outdoor air",
            value_celsius=20.5,
            raw_value="20.5",
        )
        assert temp.value_celsius == 20.5
        assert temp.variable_id == "v00104"
        assert temp.label == "Outdoor air"
        assert temp.raw_value == "20.5"

    def test_temperature_none_value(self):
        """Test temperature with None value (sensor not connected)."""
        temp = Temperature(
            variable_id="v00108",
            label="Duct outdoor",
            value_celsius=None,
            raw_value="-",
        )
        assert temp.value_celsius is None
        assert temp.raw_value == "-"

    def test_temperature_out_of_range_high(self):
        """Test temperature validation rejects values above 80°C."""
        with pytest.raises(ValidationError, match="out of plausible range"):
            Temperature(
                variable_id="v00104",
                label="Test",
                value_celsius=150.0,
                raw_value="150.0",
            )

    def test_temperature_out_of_range_low(self):
        """Test temperature validation rejects values below -40°C."""
        with pytest.raises(ValidationError, match="out of plausible range"):
            Temperature(
                variable_id="v00104",
                label="Test",
                value_celsius=-50.0,
                raw_value="-50.0",
            )

    def test_temperature_edge_cases(self):
        """Test temperature at edge of valid range."""
        # Exactly -40°C (minimum)
        temp_min = Temperature(
            variable_id="v00104",
            label="Test",
            value_celsius=-40.0,
            raw_value="-40.0",
        )
        assert temp_min.value_celsius == -40.0

        # Exactly 80°C (maximum)
        temp_max = Temperature(
            variable_id="v00104",
            label="Test",
            value_celsius=80.0,
            raw_value="80.0",
        )
        assert temp_max.value_celsius == 80.0

    def test_temperature_is_frozen(self):
        """Test that Temperature model is immutable."""
        temp = Temperature(
            variable_id="v00104",
            label="Outdoor air",
            value_celsius=20.5,
            raw_value="20.5",
        )
        with pytest.raises(ValidationError):
            temp.value_celsius = 25.0  # type: ignore


class TestTemperatures:
    """Tests for Temperatures model."""

    def test_all_core_temperatures(self):
        """Test creating Temperatures with all core sensors."""
        temps = Temperatures(
            outdoor=Temperature(
                variable_id="v00104", label="Outdoor", value_celsius=8.6, raw_value="8.6"
            ),
            supply=Temperature(
                variable_id="v00105", label="Supply", value_celsius=22.3, raw_value="22.3"
            ),
            exhaust=Temperature(
                variable_id="v00106", label="Exhaust", value_celsius=18.5, raw_value="18.5"
            ),
            extract=Temperature(
                variable_id="v00107", label="Extract", value_celsius=20.1, raw_value="20.1"
            ),
        )
        assert temps.outdoor.value_celsius == 8.6
        assert temps.supply.value_celsius == 22.3
        assert temps.exhaust.value_celsius == 18.5
        assert temps.extract.value_celsius == 20.1

    def test_with_optional_sensors(self):
        """Test Temperatures with optional sensors connected."""
        temps = Temperatures(
            outdoor=Temperature(
                variable_id="v00104", label="Outdoor", value_celsius=8.6, raw_value="8.6"
            ),
            supply=Temperature(
                variable_id="v00105", label="Supply", value_celsius=22.3, raw_value="22.3"
            ),
            exhaust=Temperature(
                variable_id="v00106", label="Exhaust", value_celsius=18.5, raw_value="18.5"
            ),
            extract=Temperature(
                variable_id="v00107", label="Extract", value_celsius=20.1, raw_value="20.1"
            ),
            duct_outdoor=Temperature(
                variable_id="v00108", label="Duct outdoor", value_celsius=None, raw_value="-"
            ),
        )
        assert temps.duct_outdoor is not None
        assert temps.duct_outdoor.value_celsius is None


class TestFanSpeed:
    """Tests for FanSpeed model."""

    def test_valid_fan_speed(self):
        """Test creating valid fan speed reading."""
        fan = FanSpeed(
            stage=2,
            stage_percent=24.0,
            stage_label="S2 — Reduced ventilation",
            rpm_supply=1234,
            rpm_extract=1256,
        )
        assert fan.stage == 2
        assert fan.stage_percent == 24.0
        assert fan.rpm_supply == 1234
        assert fan.rpm_extract == 1256

    def test_fan_stage_validation_min(self):
        """Test fan stage must be >= 1."""
        with pytest.raises(ValidationError):
            FanSpeed(
                stage=0,  # Invalid: below minimum
                stage_percent=0.0,
                stage_label="Invalid",
                rpm_supply=0,
                rpm_extract=0,
            )

    def test_fan_stage_validation_max(self):
        """Test fan stage must be <= 6."""
        with pytest.raises(ValidationError):
            FanSpeed(
                stage=7,  # Invalid: above maximum
                stage_percent=100.0,
                stage_label="Invalid",
                rpm_supply=2000,
                rpm_extract=2000,
            )

    def test_fan_stage_external(self):
        """Test external fan stages (5-6)."""
        fan = FanSpeed(
            stage=5,
            stage_percent=100.0,
            stage_label="External — Supply air only",
            rpm_supply=2500,
            rpm_extract=0,
        )
        assert fan.stage == 5

    def test_fan_speed_none_values(self):
        """Test fan speed with None values."""
        fan = FanSpeed(
            stage=None,
            stage_percent=None,
            stage_label="Unknown",
            rpm_supply=None,
            rpm_extract=None,
        )
        assert fan.stage is None
        assert fan.rpm_supply is None


class TestOperationMode:
    """Tests for OperationMode model."""

    def test_automatic_mode(self):
        """Test automatic operation mode."""
        mode = OperationMode(
            effective=MODE_AUTOMATIC,
            party=False,
            quiet=False,
            holiday=False,
            manual=False,
            automatic=True,
            humidity_control="Continuous (Stufenlos)",
            co2_control="Continuous (Stufenlos)",
            voc_control="Continuous (Stufenlos)",
        )
        assert mode.effective == MODE_AUTOMATIC
        assert mode.automatic is True
        assert mode.party is False

    def test_party_mode(self):
        """Test party operation mode (highest priority)."""
        mode = OperationMode(
            effective=MODE_PARTY,
            party=True,
            quiet=False,
            holiday=False,
            manual=False,
            automatic=False,
            humidity_control="OFF (AUS)",
            co2_control="OFF (AUS)",
            voc_control="OFF (AUS)",
        )
        assert mode.effective == MODE_PARTY
        assert mode.party is True


class TestHeliosStatus:
    """Tests for HeliosStatus model."""

    def test_complete_status(self):
        """Test creating complete status object."""
        status = HeliosStatus(
            temperatures=Temperatures(
                outdoor=Temperature(
                    variable_id="v00104", label="Outdoor", value_celsius=8.6, raw_value="8.6"
                ),
                supply=Temperature(
                    variable_id="v00105", label="Supply", value_celsius=22.3, raw_value="22.3"
                ),
                exhaust=Temperature(
                    variable_id="v00106", label="Exhaust", value_celsius=18.5, raw_value="18.5"
                ),
                extract=Temperature(
                    variable_id="v00107", label="Extract", value_celsius=20.1, raw_value="20.1"
                ),
            ),
            fan_speed=FanSpeed(
                stage=2,
                stage_percent=24.0,
                stage_label="S2 — Reduced ventilation",
                rpm_supply=1234,
                rpm_extract=1256,
            ),
            operation_mode=OperationMode(
                effective=MODE_AUTOMATIC,
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
        )
        assert status.host == "helios.fritz.box"
        assert status.temperatures.outdoor.value_celsius == 8.6
        assert status.fan_speed.stage == 2
        assert status.operation_mode.automatic is True

    def test_status_has_timestamp(self):
        """Test that status automatically gets a timestamp."""
        status = HeliosStatus(
            temperatures=Temperatures(
                outdoor=Temperature(
                    variable_id="v00104", label="Outdoor", value_celsius=8.6, raw_value="8.6"
                ),
                supply=Temperature(
                    variable_id="v00105", label="Supply", value_celsius=22.3, raw_value="22.3"
                ),
                exhaust=Temperature(
                    variable_id="v00106", label="Exhaust", value_celsius=18.5, raw_value="18.5"
                ),
                extract=Temperature(
                    variable_id="v00107", label="Extract", value_celsius=20.1, raw_value="20.1"
                ),
            ),
            fan_speed=FanSpeed(
                stage=2,
                stage_percent=24.0,
                stage_label="S2",
                rpm_supply=1234,
                rpm_extract=1256,
            ),
            operation_mode=OperationMode(
                effective=MODE_AUTOMATIC,
                party=False,
                quiet=False,
                holiday=False,
                manual=False,
                automatic=True,
                humidity_control="OFF (AUS)",
                co2_control="OFF (AUS)",
                voc_control="OFF (AUS)",
            ),
            host="helios.fritz.box",
        )
        assert isinstance(status.timestamp, datetime)

    def test_status_to_json(self):
        """Test JSON serialization."""
        status = HeliosStatus(
            temperatures=Temperatures(
                outdoor=Temperature(
                    variable_id="v00104", label="Outdoor", value_celsius=8.6, raw_value="8.6"
                ),
                supply=Temperature(
                    variable_id="v00105", label="Supply", value_celsius=22.3, raw_value="22.3"
                ),
                exhaust=Temperature(
                    variable_id="v00106", label="Exhaust", value_celsius=18.5, raw_value="18.5"
                ),
                extract=Temperature(
                    variable_id="v00107", label="Extract", value_celsius=20.1, raw_value="20.1"
                ),
            ),
            fan_speed=FanSpeed(
                stage=2,
                stage_percent=24.0,
                stage_label="S2",
                rpm_supply=1234,
                rpm_extract=1256,
            ),
            operation_mode=OperationMode(
                effective=MODE_AUTOMATIC,
                party=False,
                quiet=False,
                holiday=False,
                manual=False,
                automatic=True,
                humidity_control="OFF (AUS)",
                co2_control="OFF (AUS)",
                voc_control="OFF (AUS)",
            ),
            host="helios.fritz.box",
        )

        json_str = status.to_json()
        assert isinstance(json_str, str)

        # Verify it's valid JSON
        parsed = json.loads(json_str)
        assert "temperatures" in parsed
        assert "fan_speed" in parsed
        assert "operation_mode" in parsed
        assert "host" in parsed
        assert parsed["host"] == "helios.fritz.box"


class TestPartyModeConfig:
    """Tests for PartyModeConfig model."""

    def test_valid_config_with_defaults(self):
        """Test creating config with default values."""
        config = PartyModeConfig()
        assert config.duration_minutes == 90
        assert config.fan_stage == 3

    def test_valid_config_custom_values(self):
        """Test creating config with custom values."""
        config = PartyModeConfig(duration_minutes=120, fan_stage=4)
        assert config.duration_minutes == 120
        assert config.fan_stage == 4

    def test_duration_rounding_up(self):
        """Test duration rounding to nearest 5 (round up)."""
        config = PartyModeConfig(duration_minutes=92, fan_stage=2)
        assert config.duration_minutes == 90

    def test_duration_rounding_down(self):
        """Test duration rounding to nearest 5 (round down)."""
        config = PartyModeConfig(duration_minutes=93, fan_stage=2)
        assert config.duration_minutes == 95

    def test_duration_already_multiple_of_five(self):
        """Test duration that's already a multiple of 5."""
        config = PartyModeConfig(duration_minutes=100, fan_stage=2)
        assert config.duration_minutes == 100

    def test_duration_minimum_valid(self):
        """Test minimum valid duration (5 minutes)."""
        config = PartyModeConfig(duration_minutes=5, fan_stage=1)
        assert config.duration_minutes == 5

    def test_duration_maximum_valid(self):
        """Test maximum valid duration (180 minutes)."""
        config = PartyModeConfig(duration_minutes=180, fan_stage=4)
        assert config.duration_minutes == 180

    def test_duration_too_low_raises_error(self):
        """Test duration below minimum raises ValidationError."""
        with pytest.raises(ValidationError, match="greater than or equal to 5"):
            PartyModeConfig(duration_minutes=4, fan_stage=2)

    def test_duration_too_high_raises_error(self):
        """Test duration above maximum raises ValidationError."""
        with pytest.raises(ValidationError, match="less than or equal to 180"):
            PartyModeConfig(duration_minutes=181, fan_stage=2)

    def test_fan_stage_minimum_valid(self):
        """Test minimum valid fan stage (1)."""
        config = PartyModeConfig(duration_minutes=90, fan_stage=1)
        assert config.fan_stage == 1

    def test_fan_stage_maximum_valid(self):
        """Test maximum valid fan stage (4)."""
        config = PartyModeConfig(duration_minutes=90, fan_stage=4)
        assert config.fan_stage == 4

    def test_fan_stage_too_low_raises_error(self):
        """Test fan stage below minimum raises ValidationError."""
        with pytest.raises(ValidationError, match="greater than or equal to 1"):
            PartyModeConfig(duration_minutes=90, fan_stage=0)

    def test_fan_stage_too_high_raises_error(self):
        """Test fan stage above maximum raises ValidationError."""
        with pytest.raises(ValidationError, match="less than or equal to 4"):
            PartyModeConfig(duration_minutes=90, fan_stage=5)

    def test_config_is_frozen(self):
        """Test that config is immutable (frozen)."""
        config = PartyModeConfig(duration_minutes=90, fan_stage=3)
        with pytest.raises(ValidationError):
            config.duration_minutes = 120


class TestPartyState:
    """Tests for PartyState model."""

    def test_valid_party_state(self):
        """Test creating a valid party state."""
        state = PartyState(
            active=True,
            configured_duration_minutes=120,
            fan_stage=3,
            remaining_minutes=45,
        )

        assert state.active is True
        assert state.configured_duration_minutes == 120
        assert state.fan_stage == 3
        assert state.remaining_minutes == 45

    def test_party_state_allows_empty_optional_fields(self):
        """Test party state can omit optional values."""
        state = PartyState(active=False)
        assert state.configured_duration_minutes is None
        assert state.fan_stage is None
        assert state.remaining_minutes is None


class TestDeviceIdentity:
    """Tests for DeviceIdentity model."""

    def test_unique_id_from_mac_address(self):
        """Test device identity derives a normalized unique id from the MAC address."""
        identity = DeviceIdentity(mac_address="80:4B:20:01:99:2A")
        assert identity.unique_id == "804b2001992a"

    def test_unique_id_is_none_without_mac(self):
        """Test device identity unique id is missing without a MAC address."""
        identity = DeviceIdentity(model="KWL EC 300W R")
        assert identity.unique_id is None


class TestHeliosSnapshot:
    """Tests for HeliosSnapshot model."""

    def test_snapshot_to_json(self):
        """Test snapshot serializes nested models."""
        snapshot = HeliosSnapshot(
            status=HeliosStatus(
                temperatures=Temperatures(
                    outdoor=Temperature(
                        variable_id="v00104", label="Outdoor", value_celsius=8.6, raw_value="8.6"
                    ),
                    supply=Temperature(
                        variable_id="v00105", label="Supply", value_celsius=22.3, raw_value="22.3"
                    ),
                    exhaust=Temperature(
                        variable_id="v00106", label="Exhaust", value_celsius=18.5, raw_value="18.5"
                    ),
                    extract=Temperature(
                        variable_id="v00107", label="Extract", value_celsius=20.1, raw_value="20.1"
                    ),
                ),
                fan_speed=FanSpeed(
                    stage=2,
                    stage_percent=24.0,
                    stage_label="S2",
                    rpm_supply=1234,
                    rpm_extract=1256,
                ),
                operation_mode=OperationMode(
                    effective=MODE_AUTOMATIC,
                    party=False,
                    quiet=False,
                    holiday=False,
                    manual=False,
                    automatic=True,
                    humidity_control="OFF (AUS)",
                    co2_control="OFF (AUS)",
                    voc_control="OFF (AUS)",
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
            ),
        )

        parsed = json.loads(snapshot.to_json())

        assert parsed["status"]["host"] == "helios.fritz.box"
        assert parsed["party_state"]["fan_stage"] == 3
        assert parsed["identity"]["model"] == "KWL EC 300W R"
