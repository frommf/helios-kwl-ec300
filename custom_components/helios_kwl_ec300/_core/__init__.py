"""Helios KWL EC 300 - Python library for Helios KWL EC 300W R ventilation units.

This library provides async access to status information and party mode control
for Helios KWL ventilation systems.

Example (reading status):
    import asyncio
    from custom_components.helios_kwl_ec300._core import Info

    async def main():
        async with Info("helios.fritz.box") as helios:
            status = await helios.get_status()
            print(f"Supply air: {status.temperatures.supply.value_celsius}°C")
            print(f"Fan stage: {status.fan_speed.stage}")

    asyncio.run(main())

Example (party mode control):
    async def main():
        async with Info("helios.fritz.box") as helios:
            # Activate party mode for 120 minutes at fan stage 4
            await helios.set_party_mode(duration_minutes=120, fan_stage=4)

            # Deactivate party mode
            await helios.stop_party_mode()

    asyncio.run(main())

For detailed documentation, see:
- Info class: Main high-level interface
- HeliosStatus model: Complete status snapshot
- Individual models: Temperatures, FanSpeed, OperationMode, PartyModeConfig
"""

from .constants import DEFAULT_HOST, DEFAULT_PASSWORD
from .exceptions import (
    AuthenticationError,
    HeliosError,
    NetworkError,
    ParseError,
    PartyModeError,
    ProtocolError,
)
from .info import Info
from .models import (
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

__version__ = "0.3.0"

__all__ = [
    # Main interface
    "Info",
    # Models
    "HeliosStatus",
    "HeliosSnapshot",
    "Temperatures",
    "Temperature",
    "FanSpeed",
    "OperationMode",
    "PartyModeConfig",
    "PartyState",
    "DeviceIdentity",
    # Exceptions
    "HeliosError",
    "NetworkError",
    "AuthenticationError",
    "ParseError",
    "ProtocolError",
    "PartyModeError",
    # Constants
    "DEFAULT_HOST",
    "DEFAULT_PASSWORD",
]
