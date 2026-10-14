"""Constants for the Helios Home Assistant integration."""

from homeassistant.const import Platform

DOMAIN = "helios_kwl_ec300"
NAME = "Helios KWL EC 300"
MANUFACTURER = "Helios"

PLATFORMS: tuple[Platform, ...] = (
    Platform.FAN,
    Platform.NUMBER,
    Platform.SELECT,
    Platform.SENSOR,
)

CONF_SCAN_INTERVAL = "scan_interval"
CONF_PARTY_DURATION = "party_duration_minutes"
CONF_PARTY_FAN_STAGE = "party_fan_stage"

DEFAULT_SCAN_INTERVAL_SECONDS = 30
DEFAULT_PARTY_DURATION_MINUTES = 90
DEFAULT_PARTY_FAN_STAGE = 3
DEFAULT_TIMEOUT_SECONDS = 10.0

ATTR_STAGE = "stage"
ATTR_STAGE_LABEL = "stage_label"
ATTR_EFFECTIVE_MODE = "effective_mode"
ATTR_RPM_SUPPLY = "rpm_supply"
ATTR_RPM_EXTRACT = "rpm_extract"
