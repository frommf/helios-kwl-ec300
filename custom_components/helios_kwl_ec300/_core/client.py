"""Low-level async HTTP client for Helios KWL devices.

This module provides the HeliosClient class which handles HTTP communication,
IP-based authentication, and raw data fetching from the device.
"""

from types import TracebackType

from .constants import (
    AUTH_ENDPOINT,
    AUTH_PASSWORD_ID,
    DATA_ENDPOINT,
    DEFAULT_PASSWORD,
    IDENTITY_ENDPOINT,
    PARTY_ENDPOINT,
    PARTY_STATE_ENDPOINT,
    PartyModeID,
)
from .exceptions import AuthenticationError, ProtocolError
from .models import PartyModeConfig
from .parsers import parse_values_xml
from .transport import AsyncHTTP10Transport


class HeliosClient:
    """Async HTTP client for Helios KWL ventilation units.

    Handles HTTP/1.0 protocol, IP-based authentication, and XML data fetching.

    The Helios device uses IP-based session tracking. After successful login,
    the device remembers the client IP and allows access to data endpoints.

    Example:
        async with HeliosClient("helios.fritz.box") as client:
            data = await client.fetch_werte8()
            print(data["v00104"])  # Outdoor air temperature
    """

    def __init__(
        self,
        host: str,
        password: str = DEFAULT_PASSWORD,
        timeout: float = 10.0,
    ) -> None:
        """Initialize client.

        Args:
            host: Hostname or IP address of the Helios device
            password: Authentication password (default: "!helios!")
            timeout: Socket timeout in seconds (default: 10.0)
        """
        self.host = host
        self.password = password
        self.timeout = timeout
        self.transport = AsyncHTTP10Transport(host, timeout=timeout)
        self._authenticated = False

    async def __aenter__(self) -> "HeliosClient":
        """Async context manager entry."""
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        """Async context manager exit."""
        # No cleanup needed (connections close after each request)
        pass

    async def login(self) -> None:
        """Perform IP-based authentication.

        Posts the password to /info.htm to establish an IP-based session.
        After successful login, the device allows access to data endpoints.

        Raises:
            AuthenticationError: Login failed with non-200 status
            NetworkError: Network communication failure
            ProtocolError: Invalid HTTP response
        """
        body = f"{AUTH_PASSWORD_ID}={self.password}"
        response = await self.transport.post(AUTH_ENDPOINT, body)

        if response.status_code != 200:
            raise AuthenticationError(f"Login failed with status {response.status_code}")

        self._authenticated = True

    async def fetch_werte8(self, retry_auth: bool = True) -> dict[str, str]:
        """Fetch werte8.xml data (temperatures, fan speed, operation modes).

        Automatically retries with authentication if 403 Forbidden is returned.

        The device requires POSTing with body `xml=/data/werte8.xml` (not GET).
        This is a quirk of the embedded web server.

        Args:
            retry_auth: If True, automatically login and retry on 403 (default: True)

        Returns:
            Dictionary mapping variable IDs to their string values
            Example: {"v00104": "8.6", "v00105": "22.3", ...}

        Raises:
            AuthenticationError: Access forbidden even after login attempt
            ParseError: Failed to parse XML response
            NetworkError: Network communication failure
            ProtocolError: Invalid HTTP response
        """
        return await self.fetch_xml_data(DATA_ENDPOINT, retry_auth=retry_auth)

    async def fetch_werte20(self, retry_auth: bool = True) -> dict[str, str]:
        """Fetch werte20.xml data (device identity and diagnostics)."""
        return await self.fetch_xml_data(IDENTITY_ENDPOINT, retry_auth=retry_auth)

    async def fetch_werte3(self, retry_auth: bool = True) -> dict[str, str]:
        """Fetch werte3.xml data (party mode configuration and timers)."""
        return await self.fetch_xml_data(PARTY_STATE_ENDPOINT, retry_auth=retry_auth)

    async def fetch_xml_data(
        self,
        endpoint: str,
        retry_auth: bool = True,
    ) -> dict[str, str]:
        """Fetch a read-only XML data endpoint from the device.

        Only XML files below /data/ are permitted here to preserve the safety
        guarantees of the library.
        """
        if not endpoint.startswith("/data/") or not endpoint.endswith(".xml"):
            raise ValueError(f"Unsupported XML endpoint: {endpoint}")

        body = f"xml={endpoint}"
        response = await self.transport.post(endpoint, body)

        # Handle 403 Forbidden (requires authentication)
        if response.status_code == 403:
            if not retry_auth:
                raise AuthenticationError(
                    "Access forbidden (403) even after login attempt. "
                    "Check password or device configuration."
                )

            # Perform login and retry
            await self.login()
            return await self.fetch_xml_data(endpoint, retry_auth=False)

        if response.status_code != 200:
            raise ProtocolError(f"Unexpected status {response.status_code} for {endpoint}")

        # Parse XML response
        return parse_values_xml(response.body)

    async def set_party_mode(
        self,
        duration_minutes: int,
        fan_stage: int,
        retry_auth: bool = True,
    ) -> None:
        """Activate party mode with specified settings.

        Party mode enables high ventilation for a specified duration.
        This is useful for events, cooking, or other temporary high-ventilation needs.

        Args:
            duration_minutes: Duration in minutes (5-180)
            fan_stage: Fan stage 1-4
            retry_auth: If True, automatically login and retry on 403 (default: True)

        Raises:
            AuthenticationError: Access forbidden even after login attempt
            NetworkError: Network communication failure
            ProtocolError: Invalid HTTP response
            ValidationError: Invalid parameters (via Pydantic model)
        """
        # Validate via model (raises ValidationError if invalid)
        config = PartyModeConfig(
            duration_minutes=duration_minutes,
            fan_stage=fan_stage,
        )

        # Build form body
        body = (
            f"{PartyModeID.FAN_STAGE}={config.fan_stage}&"
            f"{PartyModeID.DURATION}={config.duration_minutes}&"
            f"{PartyModeID.REMAINING}=0&"
            f"{PartyModeID.ACTIVE}=1"
        )

        response = await self.transport.post(PARTY_ENDPOINT, body)

        # Handle 403 Forbidden (requires authentication)
        if response.status_code == 403:
            if not retry_auth:
                raise AuthenticationError(
                    "Access forbidden (403) even after login attempt. "
                    "Check password or device configuration."
                )

            # Perform login and retry
            await self.login()
            return await self.set_party_mode(duration_minutes, fan_stage, retry_auth=False)

        if response.status_code != 200:
            raise ProtocolError(f"Unexpected status {response.status_code} for {PARTY_ENDPOINT}")

    async def stop_party_mode(self, retry_auth: bool = True) -> None:
        """Deactivate party mode.

        Returns the ventilation system to its previous operating mode.

        Args:
            retry_auth: If True, automatically login and retry on 403 (default: True)

        Raises:
            AuthenticationError: Access forbidden even after login attempt
            NetworkError: Network communication failure
            ProtocolError: Invalid HTTP response
        """
        body = f"{PartyModeID.ACTIVE}=0"
        response = await self.transport.post(PARTY_ENDPOINT, body)

        # Handle 403 Forbidden (requires authentication)
        if response.status_code == 403:
            if not retry_auth:
                raise AuthenticationError(
                    "Access forbidden (403) even after login attempt. "
                    "Check password or device configuration."
                )

            # Perform login and retry
            await self.login()
            return await self.stop_party_mode(retry_auth=False)

        if response.status_code != 200:
            raise ProtocolError(f"Unexpected status {response.status_code} for {PARTY_ENDPOINT}")
