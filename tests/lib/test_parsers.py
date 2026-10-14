"""Tests for XML parsing and data extraction."""

import pytest

from custom_components.helios_kwl_ec300._core.constants import (
    FLAG_ACTIVE,
    FLAG_INACTIVE,
    MODE_AUTOMATIC,
    FanID,
    ModeID,
    PartyModeID,
)
from custom_components.helios_kwl_ec300._core.exceptions import ParseError
from custom_components.helios_kwl_ec300._core.models import (
    FanSpeed,
    OperationMode,
    Temperature,
    Temperatures,
)
from custom_components.helios_kwl_ec300._core.parsers import (
    _try_float,
    _try_int,
    extract_device_identity,
    extract_fan_speed,
    extract_operation_mode,
    extract_party_state,
    extract_temperature,
    extract_temperatures,
    parse_values_xml,
    parse_werte8_xml,
)


class TestParseWerte8XML:
    """Tests for parse_werte8_xml function."""

    def test_parse_real_werte8_xml(self, sample_werte8_xml):
        """Test parsing real werte8.xml from device."""
        data = parse_werte8_xml(sample_werte8_xml)

        assert isinstance(data, dict)
        assert len(data) > 0

        # Check expected IDs are present
        assert "v00104" in data  # Outdoor air
        assert "v00105" in data  # Supply air
        assert "v00102" in data  # Fan stage

    def test_parse_simple_xml(self):
        """Test parsing simple XML structure."""
        xml = b"""<?xml version="1.0" encoding="UTF-8"?>
<PARAMETER>
<ID>v00104</ID>
<VA>8.6</VA>
<ID>v00105</ID>
<VA>22.3</VA>
</PARAMETER>"""

        data = parse_werte8_xml(xml)

        assert data == {"v00104": "8.6", "v00105": "22.3"}

    def test_parse_values_xml_alias(self):
        """Test the generic XML parser handles the same response format."""
        xml = b"""<?xml version=\"1.0\" encoding=\"UTF-8\"?>
<PARAMETER>
<ID>v00000</ID>
<VA>KWL EC 300W R</VA>
</PARAMETER>"""

        assert parse_values_xml(xml) == {"v00000": "KWL EC 300W R"}

    def test_parse_malformed_xml(self):
        """Test parsing fails gracefully on malformed XML."""
        xml = b"<PARAMETER>INVALID<XML"

        with pytest.raises(ParseError, match="Failed to parse XML"):
            parse_werte8_xml(xml)

    def test_parse_mismatched_id_va_count(self):
        """Test parsing fails when ID/VA counts don't match."""
        xml = b"""<?xml version="1.0" encoding="UTF-8"?>
<PARAMETER>
<ID>v00104</ID>
<VA>8.6</VA>
<ID>v00105</ID>
</PARAMETER>"""

        with pytest.raises(ParseError, match="Mismatched ID/VA count"):
            parse_werte8_xml(xml)


class TestTryFloat:
    """Tests for _try_float helper."""

    def test_try_float_valid(self):
        """Test parsing valid float."""
        assert _try_float("8.6") == 8.6
        assert _try_float("22.3") == 22.3

    def test_try_float_with_comma(self):
        """Test parsing float with comma as decimal separator."""
        assert _try_float("8,6") == 8.6
        assert _try_float("22,3") == 22.3

    def test_try_float_dash(self):
        """Test parsing dash (not connected) returns None."""
        assert _try_float("-") is None

    def test_try_float_empty(self):
        """Test parsing empty string returns None."""
        assert _try_float("") is None
        assert _try_float(None) is None

    def test_try_float_invalid(self):
        """Test parsing invalid string returns None."""
        assert _try_float("invalid") is None
        assert _try_float("abc") is None


class TestTryInt:
    """Tests for _try_int helper."""

    def test_try_int_valid(self):
        """Test parsing valid integer."""
        assert _try_int("2") == 2
        assert _try_int("1234") == 1234

    def test_try_int_dash(self):
        """Test parsing dash returns None."""
        assert _try_int("-") is None

    def test_try_int_empty(self):
        """Test parsing empty string returns None."""
        assert _try_int("") is None
        assert _try_int(None) is None

    def test_try_int_invalid(self):
        """Test parsing invalid string returns None."""
        assert _try_int("invalid") is None
        assert _try_int("12.5") is None


class TestExtractTemperature:
    """Tests for extract_temperature function."""

    def test_extract_valid_temperature(self):
        """Test extracting valid temperature."""
        data = {"v00104": "8.6"}
        temp = extract_temperature(data, "v00104", "Outdoor air")

        assert isinstance(temp, Temperature)
        assert temp.variable_id == "v00104"
        assert temp.label == "Outdoor air"
        assert temp.value_celsius == 8.6
        assert temp.raw_value == "8.6"

    def test_extract_missing_temperature(self):
        """Test extracting temperature for sensor not connected."""
        data = {"v00108": "-"}
        temp = extract_temperature(data, "v00108", "Duct outdoor")

        assert temp.value_celsius is None
        assert temp.raw_value == "-"

    def test_extract_temperature_not_in_data(self):
        """Test extracting temperature not present in data."""
        data = {}
        temp = extract_temperature(data, "v00999", "Unknown")

        assert temp.value_celsius is None
        assert temp.raw_value == "-"


class TestExtractTemperatures:
    """Tests for extract_temperatures function."""

    def test_extract_all_core_temperatures(self, parsed_werte8_data):
        """Test extracting all core temperature sensors."""
        temps = extract_temperatures(parsed_werte8_data)

        assert isinstance(temps, Temperatures)
        assert temps.outdoor.value_celsius == 8.6
        assert temps.supply.value_celsius == 22.3
        assert temps.exhaust.value_celsius == 18.5
        assert temps.extract.value_celsius == 20.1

    def test_extract_temperatures_skips_disconnected_optional(self, parsed_werte8_data):
        """Test optional sensors that are not connected (show '-') are None."""
        temps = extract_temperatures(parsed_werte8_data)

        # These sensors show "-" in test data
        assert temps.duct_outdoor is None
        assert temps.duct_supply is None
        assert temps.return_hw is None

    def test_extract_temperatures_with_connected_optional(self):
        """Test optional sensors that are connected."""
        data = {
            "v00104": "8.6",
            "v00105": "22.3",
            "v00106": "18.5",
            "v00107": "20.1",
            "v00108": "5.2",  # Duct outdoor connected
            "v00146": "-",
            "v00110": "-",
        }

        temps = extract_temperatures(data)

        assert temps.duct_outdoor is not None
        assert temps.duct_outdoor.value_celsius == 5.2
        assert temps.duct_supply is None
        assert temps.return_hw is None

    def test_extract_temperatures_labels(self, parsed_werte8_data):
        """Test temperature labels are correct."""
        temps = extract_temperatures(parsed_werte8_data)

        assert "Außenluft" in temps.outdoor.label
        assert "Zuluft" in temps.supply.label
        assert "Fortluft" in temps.exhaust.label
        assert "Abluft" in temps.extract.label


class TestExtractFanSpeed:
    """Tests for extract_fan_speed function."""

    def test_extract_valid_fan_speed(self, parsed_werte8_data):
        """Test extracting valid fan speed data."""
        fan = extract_fan_speed(parsed_werte8_data)

        assert isinstance(fan, FanSpeed)
        assert fan.stage == 2
        assert fan.stage_percent == 24.0
        assert fan.rpm_supply == 1234
        assert fan.rpm_extract == 1256

    def test_extract_fan_stage_label(self, parsed_werte8_data):
        """Test fan stage label is correct."""
        fan = extract_fan_speed(parsed_werte8_data)

        assert "S2" in fan.stage_label
        assert "Reduz. Lüftung" in fan.stage_label

    def test_extract_fan_speed_missing_data(self):
        """Test fan speed with missing/invalid data."""
        data = {
            "v00102": "-",
            "v00103": "-",
            "v00348": "-",
            "v00349": "-",
        }

        fan = extract_fan_speed(data)

        assert fan.stage is None
        assert fan.stage_percent is None
        assert fan.rpm_supply is None
        assert fan.rpm_extract is None
        assert "Unknown" in fan.stage_label

    def test_extract_fan_speed_external_stage(self):
        """Test extracting external fan stage (5 or 6)."""
        data = {
            "v00102": "5",
            "v00103": "100",
            "v00348": "2500",
            "v00349": "0",
        }

        fan = extract_fan_speed(data)

        assert fan.stage == 5
        assert "External" in fan.stage_label or "EXT" in fan.stage_label

    def test_extract_fan_speed_during_party_mode(self):
        """Test fan speed displays party target stage when party mode active."""
        data = {
            FanID.STAGE: "2",  # Current actual stage (ramping up)
            PartyModeID.FAN_STAGE: "3",  # Party mode target stage
            ModeID.PARTY_ACTIVE: FLAG_ACTIVE,  # Party mode active
            FanID.STAGE_PCT: "80",
            FanID.RPM_SUPPLY: "2000",
            FanID.RPM_EXTRACT: "2020",
        }

        fan = extract_fan_speed(data)

        # Should display party target stage (3), not current actual stage (2)
        assert fan.stage == 3
        assert "S3" in fan.stage_label
        assert "Nennlüftung" in fan.stage_label

    def test_extract_fan_speed_without_party_mode(self):
        """Test fan speed displays actual stage when party mode not active."""
        data = {
            FanID.STAGE: "2",  # Current actual stage
            PartyModeID.FAN_STAGE: "3",  # Party target (ignored when party inactive)
            ModeID.PARTY_ACTIVE: FLAG_INACTIVE,  # Party mode NOT active
            FanID.STAGE_PCT: "80",
            FanID.RPM_SUPPLY: "2000",
            FanID.RPM_EXTRACT: "2020",
        }

        fan = extract_fan_speed(data)

        # Should display current actual stage (2), not party target
        assert fan.stage == 2
        assert "S2" in fan.stage_label


class TestExtractOperationMode:
    """Tests for extract_operation_mode function."""

    def test_extract_automatic_mode(self, parsed_werte8_data):
        """Test extracting automatic operation mode."""
        mode = extract_operation_mode(parsed_werte8_data)

        assert isinstance(mode, OperationMode)
        assert mode.effective == MODE_AUTOMATIC
        assert mode.automatic is True
        assert mode.party is False
        assert mode.quiet is False
        assert mode.holiday is False
        assert mode.manual is False

    def test_extract_party_mode(self):
        """Test party mode takes highest priority."""
        data = {
            "v00101": "0",
            "v00094": "1",  # Party active
            "v00099": "0",
            "v00601": "0",
            "v00033": "0",
            "v00037": "0",
            "v00040": "0",
        }

        mode = extract_operation_mode(data)

        assert mode.effective == "Partybetrieb (Party mode)"
        assert mode.party is True
        assert mode.automatic is False

    def test_extract_quiet_mode(self):
        """Test quiet mode (second priority)."""
        data = {
            "v00101": "0",
            "v00094": "0",
            "v00099": "1",  # Quiet active
            "v00601": "0",
            "v00033": "0",
            "v00037": "0",
            "v00040": "0",
        }

        mode = extract_operation_mode(data)

        assert mode.effective == "Ruhebetrieb (Quiet mode)"
        assert mode.quiet is True
        assert mode.automatic is False

    def test_extract_holiday_mode(self):
        """Test holiday mode (third priority)."""
        data = {
            "v00101": "0",
            "v00094": "0",
            "v00099": "0",
            "v00601": "1",  # Holiday active
            "v00033": "0",
            "v00037": "0",
            "v00040": "0",
        }

        mode = extract_operation_mode(data)

        assert mode.effective == "Urlaub (Holiday mode)"
        assert mode.holiday is True
        assert mode.automatic is False

    def test_extract_manual_mode(self):
        """Test manual mode (fourth priority)."""
        data = {
            "v00101": "1",  # Manual mode
            "v00094": "0",
            "v00099": "0",
            "v00601": "0",
            "v00033": "0",
            "v00037": "0",
            "v00040": "0",
        }

        mode = extract_operation_mode(data)

        assert mode.effective == "Manuell (Manual)"
        assert mode.manual is True
        assert mode.automatic is False

    def test_extract_auto_submodes(self, parsed_werte8_data):
        """Test extracting auto control submodes."""
        mode = extract_operation_mode(parsed_werte8_data)

        # Test data has submodes set to "2" (Continuous)
        assert mode.humidity_control == "Continuous (Stufenlos)"
        assert mode.co2_control == "Continuous (Stufenlos)"
        assert mode.voc_control == "Continuous (Stufenlos)"

    def test_extract_auto_submodes_off(self):
        """Test auto submodes set to OFF."""
        data = {
            "v00101": "0",
            "v00094": "0",
            "v00099": "0",
            "v00601": "0",
            "v00033": "0",  # OFF
            "v00037": "0",  # OFF
            "v00040": "0",  # OFF
        }

        mode = extract_operation_mode(data)

        assert mode.humidity_control == "OFF (AUS)"
        assert mode.co2_control == "OFF (AUS)"
        assert mode.voc_control == "OFF (AUS)"

    def test_extract_auto_submodes_stepped(self):
        """Test auto submodes set to Stepped."""
        data = {
            "v00101": "0",
            "v00094": "0",
            "v00099": "0",
            "v00601": "0",
            "v00033": "1",  # Stepped
            "v00037": "1",  # Stepped
            "v00040": "1",  # Stepped
        }

        mode = extract_operation_mode(data)

        assert mode.humidity_control == "Stepped (Stufig)"
        assert mode.co2_control == "Stepped (Stufig)"
        assert mode.voc_control == "Stepped (Stufig)"


class TestExtractPartyState:
    """Tests for extract_party_state function."""

    def test_extract_party_state(self, parsed_werte3_data):
        """Test extracting party duration, stage, remaining time, and active flag."""
        state = extract_party_state(parsed_werte3_data)

        assert state.active is True
        assert state.configured_duration_minutes == 120
        assert state.fan_stage == 3
        assert state.remaining_minutes == 45

    def test_extract_party_state_missing_values(self):
        """Test missing party values resolve to None and inactive."""
        state = extract_party_state({})

        assert state.active is False
        assert state.configured_duration_minutes is None
        assert state.fan_stage is None
        assert state.remaining_minutes is None


class TestExtractDeviceIdentity:
    """Tests for extract_device_identity function."""

    def test_extract_device_identity(self, parsed_werte20_data):
        """Test extracting model, firmware, and MAC address."""
        identity = extract_device_identity(parsed_werte20_data)

        assert identity.model == "KWL EC 300W R"
        assert identity.firmware_version == "04232003.hGP"
        assert identity.mac_address == "80:4B:20:01:99:2A"
        assert identity.state_flags == "10001101000001110000000010000001"

    def test_mode_priority_party_overrides_all(self):
        """Test party mode overrides all other modes."""
        data = {
            "v00101": "1",  # Manual
            "v00094": "1",  # Party
            "v00099": "1",  # Quiet
            "v00601": "1",  # Holiday
            "v00033": "0",
            "v00037": "0",
            "v00040": "0",
        }

        mode = extract_operation_mode(data)

        # Party should win
        assert mode.effective == "Partybetrieb (Party mode)"
        assert mode.party is True
