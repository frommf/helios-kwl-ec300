"""High-level async API for Helios KWL status information.

This module provides the Info class, which is the main interface users should
interact with. It wraps the low-level HeliosClient with a clean, simple API.
"""

from types import TracebackType

from .client import HeliosClient
from .constants import DEFAULT_HOST, DEFAULT_PASSWORD
from .exceptions import HeliosError
from .models import (
    DeviceIdentity,
    FanSpeed,
    HeliosSnapshot,
    HeliosStatus,
    OperationMode,
    PartyState,
    Temperatures,
)
from .parsers import (
    extract_device_identity,
    extract_fan_speed,
    extract_operation_mode,
    extract_party_state,
    extract_temperatures,
)


class Info:
    """High-level async interface for reading Helios KWL status.

    This is the primary API users should interact with. It provides a simple,
    intuitive interface for fetching status information from the device.

    Example:
        async with Info("helios.fritz.box") as helios:
            status = await helios.get_status()
            print(f"Supply air: {status.temperatures.supply.value_celsius}°C")
            print(f"Fan stage: {status.fan_speed.stage}")
            print(f"Mode: {status.operation_mode.effective}")

    Example (JSON output):
        async with Info("helios.fritz.box") as helios:
            status = await helios.get_status()
            print(status.to_json())
    """

    def __init__(
        self,
        host: str = DEFAULT_HOST,
        password: str = DEFAULT_PASSWORD,
        timeout: float = 10.0,
    ) -> None:
        """Initialize Info interface.

        Args:
            host: Hostname or IP address of the Helios device (default: "helios.fritz.box")
            password: Authentication password (default: "!helios!")
            timeout: Socket timeout in seconds (default: 10.0)
        """
        self.host = host
        self._client = HeliosClient(host, password, timeout)

    async def __aenter__(self) -> "Info":
        """Async context manager entry."""
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        """Async context manager exit."""
        await self._client.__aexit__(exc_type, exc_val, exc_tb)

    async def get_status(self) -> HeliosStatus:
        """Fetch complete status snapshot.

        This is the main method that fetches all data from the device and
        returns it as a structured HeliosStatus object.

        Returns:
            HeliosStatus with temperatures, fan speed, and operation mode

        Raises:
            AuthenticationError: Failed to authenticate with device
            NetworkError: Network communication failure
            ParseError: Failed to parse device response
            ProtocolError: Invalid HTTP response

        Example:
            async with Info("helios.fritz.box") as helios:
                status = await helios.get_status()
                print(f"Outdoor: {status.temperatures.outdoor.value_celsius}°C")
        """
        data = await self._client.fetch_werte8()
        return self._build_status(data)

    async def get_temperatures(self) -> Temperatures:
        """Fetch only temperature data.

        Returns:
            Temperatures model with all temperature sensors

        Raises:
            Same exceptions as get_status()

        Example:
            async with Info("helios.fritz.box") as helios:
                temps = await helios.get_temperatures()
                print(f"Outdoor: {temps.outdoor.value_celsius}°C")
                print(f"Supply: {temps.supply.value_celsius}°C")
        """
        data = await self._client.fetch_werte8()
        return extract_temperatures(data)

    async def get_fan_speed(self) -> FanSpeed:
        """Fetch only fan speed data.

        Returns:
            FanSpeed model with stage, percentage, and RPM information

        Raises:
            Same exceptions as get_status()

        Example:
            async with Info("helios.fritz.box") as helios:
                fan = await helios.get_fan_speed()
                print(f"Stage: {fan.stage} ({fan.stage_percent}%)")
                print(f"Supply RPM: {fan.rpm_supply}")
        """
        data = await self._client.fetch_werte8()
        return extract_fan_speed(data)

    async def get_operation_mode(self) -> OperationMode:
        """Fetch only operation mode information.

        Returns:
            OperationMode model with current mode and flags

        Raises:
            Same exceptions as get_status()

        Example:
            async with Info("helios.fritz.box") as helios:
                mode = await helios.get_operation_mode()
                print(f"Mode: {mode.effective}")
                print(f"Automatic: {mode.automatic}")
        """
        data = await self._client.fetch_werte8()
        return extract_operation_mode(data)

    async def get_device_identity(self) -> DeviceIdentity:
        """Fetch static device identity information."""
        data = await self._client.fetch_werte20()
        return extract_device_identity(data)

    async def get_party_state(self) -> PartyState:
        """Fetch party mode configuration and remaining runtime."""
        data = await self._client.fetch_werte3()
        return extract_party_state(data)

    async def get_snapshot(self) -> HeliosSnapshot:
        """Fetch a combined snapshot for dashboards and Home Assistant."""
        status_data = await self._client.fetch_werte8()
        status = self._build_status(status_data)

        identity = None
        try:
            identity = extract_device_identity(await self._client.fetch_werte20())
        except HeliosError:
            pass

        party_data = status_data
        try:
            party_data = {**status_data, **await self._client.fetch_werte3()}
        except HeliosError:
            pass

        return HeliosSnapshot(
            status=status,
            party_state=extract_party_state(party_data),
            identity=identity,
        )

    async def validate_connection(self) -> HeliosSnapshot:
        """Validate connectivity and return a complete device snapshot."""
        return await self.get_snapshot()

    async def set_party_mode(
        self,
        duration_minutes: int = 90,
        fan_stage: int = 3,
    ) -> None:
        """Activate party mode with specified settings.

        Party mode enables high ventilation for a specified duration.
        This is useful for events, cooking, or other temporary high-ventilation needs.

        Args:
            duration_minutes: Duration in minutes (5-180, default: 90)
            fan_stage: Fan stage 1-4 (default: 3 - nominal ventilation)

        Raises:
            AuthenticationError: Failed to authenticate with device
            NetworkError: Network communication failure
            ProtocolError: Invalid HTTP response
            ValidationError: Invalid parameters (e.g., duration out of range)

        Example:
            async with Info("helios.fritz.box") as helios:
                await helios.set_party_mode(duration_minutes=120, fan_stage=4)
        """
        await self._client.set_party_mode(duration_minutes, fan_stage)

    async def stop_party_mode(self) -> None:
        """Deactivate party mode.

        Returns the ventilation system to its previous operating mode.

        Raises:
            AuthenticationError: Failed to authenticate with device
            NetworkError: Network communication failure
            ProtocolError: Invalid HTTP response

        Example:
            async with Info("helios.fritz.box") as helios:
                await helios.stop_party_mode()
        """
        await self._client.stop_party_mode()

    def _build_status(self, data: dict[str, str]) -> HeliosStatus:
        """Build a typed status model from parsed werte8 data."""
        return HeliosStatus(
            temperatures=extract_temperatures(data),
            fan_speed=extract_fan_speed(data),
            operation_mode=extract_operation_mode(data),
            host=self.host,
        )
