"""Data models for Helios KWL status information."""

from datetime import UTC, datetime
from typing import Literal

from pydantic import BaseModel, Field, field_validator


class Temperature(BaseModel):
    """Single temperature sensor reading.

    Attributes:
        variable_id: Device variable ID (e.g., "v00104")
        label: Human-readable label with German translation
        value_celsius: Temperature value in Celsius (None if sensor not connected)
        raw_value: Raw string value from device (e.g., "8.6" or "-")
    """

    variable_id: str
    label: str
    value_celsius: float | None
    raw_value: str

    model_config = {"frozen": True}

    @field_validator("value_celsius")
    @classmethod
    def validate_temperature_range(cls, v: float | None) -> float | None:
        """Validate temperature is within plausible range (-40°C to 80°C)."""
        if v is not None and not (-40 <= v <= 80):
            raise ValueError(f"Temperature {v}°C out of plausible range (-40 to 80°C)")
        return v


class Temperatures(BaseModel):
    """All temperature sensors.

    Attributes:
        outdoor: Outdoor air temperature (Außenluft)
        supply: Supply air temperature (Zuluft)
        exhaust: Exhaust air temperature (Fortluft)
        extract: Extract air temperature (Abluft)
        duct_outdoor: Optional duct outdoor temperature (may be None if not connected)
        duct_supply: Optional duct supply temperature (may be None if not connected)
        return_hw: Optional return hot water register temperature (may be None)
    """

    outdoor: Temperature
    supply: Temperature
    exhaust: Temperature
    extract: Temperature

    # Optional sensors (may be None if not connected)
    duct_outdoor: Temperature | None = None
    duct_supply: Temperature | None = None
    return_hw: Temperature | None = None

    model_config = {"frozen": True}


class FanSpeed(BaseModel):
    """Fan speed and stage information.

    Attributes:
        stage: Fan stage 1-4 (normal), 5-6 (external control), None if not available
        base_stage: Raw v00102 base stage, independent of party display overrides
        stage_percent: Fan stage in percent (0-100), None if not available
        stage_label: Human-readable label for the fan stage
        rpm_supply: Supply fan RPM, None if not available
        rpm_extract: Extract fan RPM, None if not available
    """

    stage: int | None = Field(None, ge=1, le=6, description="Fan stage 1-4, or 5-6 for external")
    base_stage: int | None = Field(
        None, ge=1, le=6, description="Raw v00102 stage without party display override"
    )
    stage_percent: float | None = Field(None, ge=0, le=100, description="Fan stage percentage")
    stage_label: str
    rpm_supply: int | None = Field(None, ge=0, description="Supply fan RPM")
    rpm_extract: int | None = Field(None, ge=0, description="Extract fan RPM")

    model_config = {"frozen": True}


class OperationMode(BaseModel):
    """Current operation mode.

    The effective mode is determined by priority:
    Party > Quiet > Holiday > Manual > Automatic

    Attributes:
        effective: The currently active operation mode
        party: Party mode flag (high ventilation)
        quiet: Quiet mode flag (low ventilation)
        holiday: Holiday mode flag (minimal ventilation)
        manual: Manual mode flag (user-controlled)
        automatic: Automatic mode flag (sensor-controlled)
        humidity_control: Humidity-based control setting
        co2_control: CO2-based control setting
        voc_control: VOC-based control setting
    """

    effective: Literal[
        "Partybetrieb (Party mode)",
        "Ruhebetrieb (Quiet mode)",
        "Urlaub (Holiday mode)",
        "Manuell (Manual)",
        "Automatisch (Automatic)",
    ]
    party: bool
    quiet: bool
    holiday: bool
    manual: bool
    automatic: bool

    # Auto submodes (sensor-based control)
    humidity_control: Literal["OFF (AUS)", "Stepped (Stufig)", "Continuous (Stufenlos)"]
    co2_control: Literal["OFF (AUS)", "Stepped (Stufig)", "Continuous (Stufenlos)"]
    voc_control: Literal["OFF (AUS)", "Stepped (Stufig)", "Continuous (Stufenlos)"]

    model_config = {"frozen": True}


class PartyModeConfig(BaseModel):
    """Party mode configuration with validation.

    Attributes:
        duration_minutes: Duration in minutes (5-180, rounded to nearest 5)
        fan_stage: Fan stage 1-4
    """

    duration_minutes: int = Field(ge=5, le=180, default=90, description="Duration in minutes")
    fan_stage: int = Field(ge=1, le=4, default=3, description="Fan stage")

    model_config = {"frozen": True}

    @field_validator("duration_minutes")
    @classmethod
    def round_to_five(cls, v: int) -> int:
        """Round duration to nearest 5 minutes."""
        return round(v / 5) * 5


class PartyState(BaseModel):
    """Current party mode state and configuration."""

    active: bool
    configured_duration_minutes: int | None = Field(
        None,
        ge=5,
        le=180,
        description="Configured party duration in minutes",
    )
    fan_stage: int | None = Field(None, ge=1, le=4, description="Configured party fan stage")
    remaining_minutes: int | None = Field(
        None,
        ge=0,
        le=180,
        description="Remaining party runtime in minutes",
    )

    model_config = {"frozen": True}


class DeviceIdentity(BaseModel):
    """Static device identity information for registry integration."""

    model: str | None = None
    firmware_version: str | None = None
    mac_address: str | None = None
    state_flags: str | None = None

    model_config = {"frozen": True}

    @property
    def unique_id(self) -> str | None:
        """Return a stable unique identifier when available."""
        if self.mac_address is None:
            return None
        return self.mac_address.lower().replace(":", "")


class HeliosStatus(BaseModel):
    """Complete status snapshot from Helios KWL device.

    This is the top-level model returned by the Info.get_status() method.

    Attributes:
        temperatures: All temperature sensor readings
        fan_speed: Fan speed and stage information
        operation_mode: Current operation mode
        timestamp: UTC timestamp when status was retrieved
        host: Hostname or IP address of the device
    """

    temperatures: Temperatures
    fan_speed: FanSpeed
    operation_mode: OperationMode
    timestamp: datetime = Field(default_factory=lambda: datetime.now(UTC))
    host: str

    model_config = {"frozen": True}

    def to_json(self) -> str:
        """Export as JSON string.

        Returns:
            JSON string representation with 2-space indentation
        """
        return self.model_dump_json(indent=2, exclude_none=True)


class HeliosSnapshot(BaseModel):
    """Combined state payload for dashboards and Home Assistant."""

    status: HeliosStatus
    party_state: PartyState
    identity: DeviceIdentity | None = None

    model_config = {"frozen": True}

    def to_json(self) -> str:
        """Export snapshot as JSON string."""
        return self.model_dump_json(indent=2, exclude_none=True)
