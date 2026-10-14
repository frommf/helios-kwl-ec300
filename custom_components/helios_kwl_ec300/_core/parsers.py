"""XML parsing and data extraction utilities.

This module parses werte8.xml responses from the Helios device and extracts
typed data into Pydantic models.
"""

import xml.etree.ElementTree as ET
from typing import Literal

from .constants import (
    AUTO_SUBMODE_VALUES,
    FAN_STAGE_LABELS,
    FLAG_ACTIVE,
    FLAG_INACTIVE,
    MODE_AUTOMATIC,
    MODE_HOLIDAY,
    MODE_MANUAL,
    MODE_PARTY,
    MODE_QUIET,
    TEMP_LABELS,
    TEMP_LABELS_OPTIONAL,
    DeviceIdentityID,
    FanID,
    ModeID,
    PartyModeID,
    TempSensorID,
)
from .exceptions import ParseError
from .models import (
    DeviceIdentity,
    FanSpeed,
    OperationMode,
    PartyState,
    Temperature,
    Temperatures,
)


def parse_values_xml(xml_bytes: bytes) -> dict[str, str]:
    """Parse a Helios XML response into an ID -> value mapping.

    The XML format is:
        <PARAMETER>
            <ID>v00104</ID>
            <VA>8.6</VA>
            <ID>v00105</ID>
            <VA>22.3</VA>
            ...
        </PARAMETER>

    Args:
        xml_bytes: Raw XML response from device

    Returns:
        Dictionary mapping variable IDs to their string values

    Raises:
        ParseError: XML parsing failure or mismatched ID/VA counts
    """
    try:
        root = ET.fromstring(xml_bytes)
    except ET.ParseError as e:
        raise ParseError(f"Failed to parse XML: {e}") from e

    ids = [el.text for el in root.findall("ID") if el.text]
    values = [el.text for el in root.findall("VA") if el.text is not None]

    if len(ids) != len(values):
        raise ParseError(f"Mismatched ID/VA count: {len(ids)} IDs, {len(values)} values")

    return dict(zip(ids, values, strict=True))


def parse_werte8_xml(xml_bytes: bytes) -> dict[str, str]:
    """Parse werte8.xml response into ID -> value mapping."""
    return parse_values_xml(xml_bytes)


def _try_float(s: str | None) -> float | None:
    """Safely parse float, handling comma as decimal separator.

    Args:
        s: String to parse (e.g., "8.6" or "8,6")

    Returns:
        Parsed float or None if parsing fails
    """
    if not s or s in ("-", ""):
        return None

    try:
        return float(s.replace(",", "."))
    except (ValueError, AttributeError):
        return None


def _try_int(s: str | None) -> int | None:
    """Safely parse integer.

    Args:
        s: String to parse

    Returns:
        Parsed int or None if parsing fails
    """
    if not s or s in ("-", ""):
        return None

    try:
        return int(s)
    except (ValueError, AttributeError):
        return None


def _try_str(s: str | None) -> str | None:
    """Return a non-empty string value or None."""
    if not s or s in ("-", ""):
        return None
    return s


def _is_mode_active(data: dict[str, str], mode_id: str) -> bool:
    """Check if a mode flag is active.

    Args:
        data: Parsed werte8 data (ID -> value mapping)
        mode_id: Mode variable ID (e.g., ModeID.PARTY_ACTIVE)

    Returns:
        True if mode is active (value == "1"), False otherwise
    """
    return data.get(mode_id, FLAG_INACTIVE) == FLAG_ACTIVE


def extract_temperature(data: dict[str, str], variable_id: str, label: str) -> Temperature:
    """Extract single temperature reading from raw data.

    Args:
        data: Parsed werte8 data (ID -> value mapping)
        variable_id: Variable ID to extract (e.g., "v00104")
        label: Human-readable label for this temperature

    Returns:
        Temperature model
    """
    raw = data.get(variable_id, "-")
    value = _try_float(raw)

    return Temperature(variable_id=variable_id, label=label, value_celsius=value, raw_value=raw)


def extract_temperatures(data: dict[str, str]) -> Temperatures:
    """Extract all temperature readings from raw data.

    Args:
        data: Parsed werte8 data (ID -> value mapping)

    Returns:
        Temperatures model with all sensors
    """
    # Core temperatures (always present)
    outdoor = extract_temperature(data, TempSensorID.OUTDOOR, TEMP_LABELS[TempSensorID.OUTDOOR])
    supply = extract_temperature(data, TempSensorID.SUPPLY, TEMP_LABELS[TempSensorID.SUPPLY])
    exhaust = extract_temperature(data, TempSensorID.EXHAUST, TEMP_LABELS[TempSensorID.EXHAUST])
    extract = extract_temperature(data, TempSensorID.EXTRACT, TEMP_LABELS[TempSensorID.EXTRACT])

    # Optional temperatures (may be None if sensor not connected)
    duct_outdoor = None
    duct_supply = None
    return_hw = None

    # Only include optional sensors if they have valid readings (not "-")
    if data.get(TempSensorID.DUCT_OUTDOOR) not in ("-", None):
        duct_outdoor = extract_temperature(
            data,
            TempSensorID.DUCT_OUTDOOR,
            TEMP_LABELS_OPTIONAL[TempSensorID.DUCT_OUTDOOR],
        )

    if data.get(TempSensorID.DUCT_SUPPLY) not in ("-", None):
        duct_supply = extract_temperature(
            data,
            TempSensorID.DUCT_SUPPLY,
            TEMP_LABELS_OPTIONAL[TempSensorID.DUCT_SUPPLY],
        )

    if data.get(TempSensorID.RETURN_HW) not in ("-", None):
        return_hw = extract_temperature(
            data, TempSensorID.RETURN_HW, TEMP_LABELS_OPTIONAL[TempSensorID.RETURN_HW]
        )

    return Temperatures(
        outdoor=outdoor,
        supply=supply,
        exhaust=exhaust,
        extract=extract,
        duct_outdoor=duct_outdoor,
        duct_supply=duct_supply,
        return_hw=return_hw,
    )


def extract_fan_speed(data: dict[str, str]) -> FanSpeed:
    """Extract fan speed information from raw data.

    During party mode, displays the party target stage (PartyModeID.FAN_STAGE)
    instead of the current actual stage (FanID.STAGE), matching the web interface.

    Args:
        data: Parsed werte8 data (ID -> value mapping)

    Returns:
        FanSpeed model
    """
    # Check if party mode is active
    party_active = _is_mode_active(data, ModeID.PARTY_ACTIVE)

    # During party mode, use party target stage instead of current actual stage
    if party_active:
        stage_raw = data.get(PartyModeID.FAN_STAGE, "-")
    else:
        stage_raw = data.get(FanID.STAGE, "-")

    pct_raw = data.get(FanID.STAGE_PCT, "-")
    rpm_s_raw = data.get(FanID.RPM_SUPPLY, "-")
    rpm_e_raw = data.get(FanID.RPM_EXTRACT, "-")

    stage = _try_int(stage_raw)
    stage_pct = _try_float(pct_raw)
    rpm_supply = _try_int(rpm_s_raw)
    rpm_extract = _try_int(rpm_e_raw)

    # Get human-readable label for stage
    stage_label = FAN_STAGE_LABELS.get(
        stage_raw, f"Unknown stage ({stage_raw})" if stage_raw != "-" else "Unknown"
    )

    return FanSpeed(
        stage=stage,
        stage_percent=stage_pct,
        stage_label=stage_label,
        rpm_supply=rpm_supply,
        rpm_extract=rpm_extract,
    )


def extract_party_state(data: dict[str, str]) -> PartyState:
    """Extract party mode state and configured values."""
    return PartyState(
        active=_is_mode_active(data, PartyModeID.ACTIVE),
        configured_duration_minutes=_try_int(data.get(PartyModeID.DURATION)),
        fan_stage=_try_int(data.get(PartyModeID.FAN_STAGE)),
        remaining_minutes=_try_int(data.get(PartyModeID.REMAINING)),
    )


def extract_device_identity(data: dict[str, str]) -> DeviceIdentity:
    """Extract static device identity metadata."""
    return DeviceIdentity(
        model=_try_str(data.get(DeviceIdentityID.MODEL)),
        firmware_version=_try_str(data.get(DeviceIdentityID.FIRMWARE)),
        mac_address=_try_str(data.get(DeviceIdentityID.MAC_ADDRESS)),
        state_flags=_try_str(data.get(DeviceIdentityID.STATE_FLAGS)),
    )


def extract_operation_mode(data: dict[str, str]) -> OperationMode:
    """Determine the current effective operation mode.

    Priority order (from JS getmodus()):
      Party > Quiet > Holiday > Manual > Automatic

    Args:
        data: Parsed werte8 data (ID -> value mapping)

    Returns:
        OperationMode model
    """
    # Parse mode flags
    party = _is_mode_active(data, ModeID.PARTY_ACTIVE)
    quiet = _is_mode_active(data, ModeID.QUIET_ACTIVE)
    holiday = _is_mode_active(data, ModeID.HOLIDAY_ACTIVE)
    manual = _is_mode_active(data, ModeID.AUTO_OR_MANUAL)

    # Determine effective mode by priority
    effective: Literal[
        "Partybetrieb (Party mode)",
        "Ruhebetrieb (Quiet mode)",
        "Urlaub (Holiday mode)",
        "Manuell (Manual)",
        "Automatisch (Automatic)",
    ]

    if party:
        effective = MODE_PARTY
    elif quiet:
        effective = MODE_QUIET
    elif holiday:
        effective = MODE_HOLIDAY
    elif manual:
        effective = MODE_MANUAL
    else:
        effective = MODE_AUTOMATIC

    automatic = not (party or quiet or holiday or manual)

    # Parse auto control submodes
    humidity_raw = data.get("v00033", "0")
    co2_raw = data.get("v00037", "0")
    voc_raw = data.get("v00040", "0")

    humidity_control = AUTO_SUBMODE_VALUES.get(humidity_raw, f"Unknown ({humidity_raw})")
    co2_control = AUTO_SUBMODE_VALUES.get(co2_raw, f"Unknown ({co2_raw})")
    voc_control = AUTO_SUBMODE_VALUES.get(voc_raw, f"Unknown ({voc_raw})")

    return OperationMode(
        effective=effective,
        party=party,
        quiet=quiet,
        holiday=holiday,
        manual=manual,
        automatic=automatic,
        humidity_control=humidity_control,  # type: ignore
        co2_control=co2_control,  # type: ignore
        voc_control=voc_control,  # type: ignore
    )
