"""Constants for Helios KWL EC 300W R ventilation units.

This module contains all variable IDs, endpoint paths, labels, and device-specific
constants used to communicate with the Helios KWL system.
"""

from typing import Final, Literal

# ==============================================================================
# Network & Authentication
# ==============================================================================

DEFAULT_HOST: Final[str] = "helios.fritz.box"
DEFAULT_PASSWORD: Final[str] = "!helios!"
DEFAULT_PORT: Final[int] = 80
DEFAULT_TIMEOUT: Final[float] = 10.0

# ==============================================================================
# Endpoints
# ==============================================================================

DATA_ENDPOINT: Final[str] = "/data/werte8.xml"
IDENTITY_ENDPOINT: Final[str] = "/data/werte20.xml"
PARTY_STATE_ENDPOINT: Final[str] = "/data/werte3.xml"
AUTH_ENDPOINT: Final[str] = "/info.htm"
OPERATING_CONTROL_ENDPOINT: Final[str] = "/info.htm"
PARTY_ENDPOINT: Final[str] = "/party.htm"

# ==============================================================================
# Protocol Values
# ==============================================================================

# Mode/flag activation states
FLAG_ACTIVE: Final[str] = "1"
FLAG_INACTIVE: Final[str] = "0"

# ==============================================================================
# Variable IDs - Temperatures
# ==============================================================================


class TempSensorID:
    """Temperature sensor variable IDs."""

    # Core temperature sensors (always present)
    OUTDOOR: Final[str] = "v00104"  # Außenluft
    SUPPLY: Final[str] = "v00105"  # Zuluft
    EXHAUST: Final[str] = "v00106"  # Fortluft
    EXTRACT: Final[str] = "v00107"  # Abluft

    # Optional temperature sensors (may show "-" if not connected)
    DUCT_OUTDOOR: Final[str] = "v00108"  # Kanal Außenluft
    DUCT_SUPPLY: Final[str] = "v00146"  # Frostschutz/Kanal Zuluft
    RETURN_HW: Final[str] = "v00110"  # Rücklauf WW-Register


# Temperature labels (German)
TEMP_LABELS: Final[dict[str, str]] = {
    TempSensorID.OUTDOOR: "Outdoor air   (Außenluft)",
    TempSensorID.SUPPLY: "Supply air    (Zuluft)",
    TempSensorID.EXHAUST: "Exhaust air   (Fortluft)",
    TempSensorID.EXTRACT: "Extract air   (Abluft)",
}

TEMP_LABELS_OPTIONAL: Final[dict[str, str]] = {
    TempSensorID.DUCT_OUTDOOR: "Duct outdoor  (Kanal Außenluft)",
    TempSensorID.DUCT_SUPPLY: "Duct supply   (Frostschutz/Kanal Zuluft)",
    TempSensorID.RETURN_HW: "Return HW reg (Rücklauf WW-Register)",
}

# ==============================================================================
# Variable IDs - Fan Speed
# ==============================================================================


class FanID:
    """Fan speed and stage variable IDs."""

    STAGE: Final[str] = "v00102"  # Current fan stage (1-4, 5/6 = external)
    STAGE_PCT: Final[str] = "v00103"  # Fan stage in %
    RPM_SUPPLY: Final[str] = "v00348"  # Supply fan RPM
    RPM_EXTRACT: Final[str] = "v00349"  # Extract fan RPM


# Fan stage labels
FAN_STAGE_LABELS: Final[dict[str, str]] = {
    "1": "S1 — Moisture protection (Feuchteschutz)",
    "2": "S2 — Reduced ventilation (Reduz. Lüftung)",
    "3": "S3 — Nominal ventilation (Nennlüftung)",
    "4": "S4 — Intensive ventilation (Intensivlüftung)",
    "5": "External — Supply air only (EXT. ZULUFT)",
    "6": "External — Extract air only (EXT. ABLUFT)",
}

# ==============================================================================
# Variable IDs - Operation Modes
# ==============================================================================


class ModeID:
    """Operation mode variable IDs."""

    AUTO_OR_MANUAL: Final[str] = "v00101"  # 0 = auto, 1 = manual
    PARTY_ACTIVE: Final[str] = "v00094"  # 1 = party mode on
    QUIET_ACTIVE: Final[str] = "v00099"  # 1 = quiet (Ruhebetrieb) on
    HOLIDAY_ACTIVE: Final[str] = "v00601"  # 1 = holiday mode on


class DeviceIdentityID:
    """Device identity variable IDs."""

    MODEL: Final[str] = "v00000"
    FIRMWARE: Final[str] = "v00001"
    MAC_ADDRESS: Final[str] = "v00002"
    STATE_FLAGS: Final[str] = "v01306"


# Auto control submode IDs (humidity/CO2/VOC)
AUTO_SUBMODE_IDS: Final[dict[str, str]] = {
    "v00033": "Humidity control (Feuchtesteuerung)",
    "v00037": "CO2 control",
    "v00040": "VOC control",
}

# Auto submode values
AUTO_SUBMODE_VALUES: Final[dict[str, str]] = {
    "0": "OFF (AUS)",
    "1": "Stepped (Stufig)",
    "2": "Continuous (Stufenlos)",
}

# ==============================================================================
# Operation Mode Names
# ==============================================================================

MODE_PARTY: Final[Literal["Partybetrieb (Party mode)"]] = "Partybetrieb (Party mode)"
MODE_QUIET: Final[Literal["Ruhebetrieb (Quiet mode)"]] = "Ruhebetrieb (Quiet mode)"
MODE_HOLIDAY: Final[Literal["Urlaub (Holiday mode)"]] = "Urlaub (Holiday mode)"
MODE_MANUAL: Final[Literal["Manuell (Manual)"]] = "Manuell (Manual)"
MODE_AUTOMATIC: Final[Literal["Automatisch (Automatic)"]] = "Automatisch (Automatic)"

# ==============================================================================
# Variable IDs - Party Mode
# ==============================================================================


class PartyModeID:
    """Party mode variable IDs."""

    DURATION: Final[str] = "v00091"  # Duration in minutes (5-180)
    FAN_STAGE: Final[str] = "v00092"  # Fan stage (1-4)
    REMAINING: Final[str] = "v00093"  # Remaining time (read-only)
    ACTIVE: Final[str] = "v00094"  # Activation flag (0=off, 1=on)


# ==============================================================================
# Authentication
# ==============================================================================

# Variable ID for password authentication
AUTH_PASSWORD_ID: Final[str] = "v00402"
