"""Tests for Info class (high-level API)."""

from unittest.mock import AsyncMock

import pytest

from custom_components.helios_kwl_ec300._core import Info
from custom_components.helios_kwl_ec300._core.models import (
    DeviceIdentity,
    FanSpeed,
    HeliosSnapshot,
    HeliosStatus,
    OperationMode,
    PartyState,
    Temperatures,
)


@pytest.fixture
def mock_client(mocker):
    """Mock HeliosClient."""
    mock = mocker.patch("custom_components.helios_kwl_ec300._core.info.HeliosClient")
    mock.return_value.fetch_werte8 = AsyncMock()
    mock.return_value.fetch_werte20 = AsyncMock()
    mock.return_value.fetch_werte3 = AsyncMock()
    mock.return_value.set_party_mode = AsyncMock()
    mock.return_value.stop_party_mode = AsyncMock()
    return mock


class TestInfo:
    """Tests for Info class."""

    def test_info_initialization(self):
        """Test Info initializes with correct defaults."""
        info = Info()

        assert info.host == "helios.fritz.box"
        assert info._client is not None

    def test_info_custom_host(self):
        """Test Info accepts custom host."""
        info = Info(host="192.168.1.100")

        assert info.host == "192.168.1.100"

    @pytest.mark.asyncio
    async def test_info_context_manager(self, mock_client):
        """Test Info works as async context manager."""
        async with Info("test.local") as info:
            assert isinstance(info, Info)

    @pytest.mark.asyncio
    async def test_get_status_returns_complete_status(self, mock_client, parsed_werte8_data):
        """Test get_status returns HeliosStatus model."""
        mock_client.return_value.fetch_werte8.return_value = parsed_werte8_data

        async with Info("test.local") as info:
            status = await info.get_status()

        assert isinstance(status, HeliosStatus)
        assert isinstance(status.temperatures, Temperatures)
        assert isinstance(status.fan_speed, FanSpeed)
        assert isinstance(status.operation_mode, OperationMode)
        assert status.host == "test.local"

    @pytest.mark.asyncio
    async def test_get_status_correct_data(self, mock_client, parsed_werte8_data):
        """Test get_status returns correct parsed data."""
        mock_client.return_value.fetch_werte8.return_value = parsed_werte8_data

        async with Info("test.local") as info:
            status = await info.get_status()

        # Verify temperatures
        assert status.temperatures.outdoor.value_celsius == 8.6
        assert status.temperatures.supply.value_celsius == 22.3
        assert status.temperatures.exhaust.value_celsius == 18.5
        assert status.temperatures.extract.value_celsius == 20.1

        # Verify fan speed
        assert status.fan_speed.stage == 2
        assert status.fan_speed.stage_percent == 24.0
        assert status.fan_speed.rpm_supply == 1234
        assert status.fan_speed.rpm_extract == 1256

        # Verify operation mode
        assert status.operation_mode.automatic is True
        assert status.operation_mode.party is False

    @pytest.mark.asyncio
    async def test_get_temperatures(self, mock_client, parsed_werte8_data):
        """Test get_temperatures returns only temperature data."""
        mock_client.return_value.fetch_werte8.return_value = parsed_werte8_data

        async with Info("test.local") as info:
            temps = await info.get_temperatures()

        assert isinstance(temps, Temperatures)
        assert temps.outdoor.value_celsius == 8.6
        assert temps.supply.value_celsius == 22.3

    @pytest.mark.asyncio
    async def test_get_fan_speed(self, mock_client, parsed_werte8_data):
        """Test get_fan_speed returns only fan speed data."""
        mock_client.return_value.fetch_werte8.return_value = parsed_werte8_data

        async with Info("test.local") as info:
            fan = await info.get_fan_speed()

        assert isinstance(fan, FanSpeed)
        assert fan.stage == 2
        assert fan.rpm_supply == 1234

    @pytest.mark.asyncio
    async def test_get_operation_mode(self, mock_client, parsed_werte8_data):
        """Test get_operation_mode returns only operation mode data."""
        mock_client.return_value.fetch_werte8.return_value = parsed_werte8_data

        async with Info("test.local") as info:
            mode = await info.get_operation_mode()

        assert isinstance(mode, OperationMode)
        assert mode.automatic is True
        assert mode.effective == "Automatisch (Automatic)"

    @pytest.mark.asyncio
    async def test_multiple_calls_fetch_fresh_data(self, mock_client, parsed_werte8_data):
        """Test multiple calls each fetch fresh data."""
        mock_client.return_value.fetch_werte8.return_value = parsed_werte8_data

        async with Info("test.local") as info:
            status1 = await info.get_status()
            status2 = await info.get_status()

        # Verify fetch was called twice
        assert mock_client.return_value.fetch_werte8.call_count == 2

        # Both should have same data but be different objects
        assert (
            status1.temperatures.outdoor.value_celsius == status2.temperatures.outdoor.value_celsius
        )

    @pytest.mark.asyncio
    async def test_status_has_timestamp(self, mock_client, parsed_werte8_data):
        """Test status includes timestamp."""
        mock_client.return_value.fetch_werte8.return_value = parsed_werte8_data

        async with Info("test.local") as info:
            status = await info.get_status()

        assert status.timestamp is not None

    @pytest.mark.asyncio
    async def test_status_json_export(self, mock_client, parsed_werte8_data):
        """Test status can be exported to JSON."""
        mock_client.return_value.fetch_werte8.return_value = parsed_werte8_data

        async with Info("test.local") as info:
            status = await info.get_status()
            json_str = status.to_json()

        assert isinstance(json_str, str)
        assert "temperatures" in json_str
        assert "fan_speed" in json_str
        assert "operation_mode" in json_str

    @pytest.mark.asyncio
    async def test_get_temperatures_handles_optional_sensors(self, mock_client):
        """Test get_temperatures handles optional sensors correctly."""
        data_with_optional = {
            "v00104": "8.6",
            "v00105": "22.3",
            "v00106": "18.5",
            "v00107": "20.1",
            "v00108": "5.2",  # Duct outdoor connected
            "v00146": "-",  # Duct supply not connected
            "v00110": "-",  # Return HW not connected
        }

        mock_client.return_value.fetch_werte8.return_value = data_with_optional

        async with Info("test.local") as info:
            temps = await info.get_temperatures()

        # Optional sensor with value should be present
        assert temps.duct_outdoor is not None
        assert temps.duct_outdoor.value_celsius == 5.2

        # Optional sensors without values should be None
        assert temps.duct_supply is None
        assert temps.return_hw is None

    @pytest.mark.asyncio
    async def test_info_passes_timeout_to_client(self, mock_client):
        """Test timeout parameter is passed to client."""
        Info("test.local", timeout=30.0)

        # Verify client was initialized with correct args
        mock_client.assert_called_once()
        # Args are (host, password, timeout)
        assert mock_client.call_args[0][0] == "test.local"
        assert mock_client.call_args[0][2] == 30.0

    @pytest.mark.asyncio
    async def test_info_passes_password_to_client(self, mock_client):
        """Test password parameter is passed to client."""
        Info("test.local", password="custom_pass")

        # Verify client was initialized with correct args
        mock_client.assert_called_once()
        # Args are (host, password, timeout)
        assert mock_client.call_args[0][0] == "test.local"
        assert mock_client.call_args[0][1] == "custom_pass"

    @pytest.mark.asyncio
    async def test_set_party_mode_with_defaults(self, mock_client):
        """Test set_party_mode with default parameters."""
        async with Info("test.local") as info:
            await info.set_party_mode()

        # Verify client method was called with defaults
        mock_client.return_value.set_party_mode.assert_called_once_with(90, 3)

    @pytest.mark.asyncio
    async def test_set_party_mode_custom_params(self, mock_client):
        """Test set_party_mode with custom parameters."""
        async with Info("test.local") as info:
            await info.set_party_mode(duration_minutes=120, fan_stage=4)

        # Verify client method was called with custom values
        mock_client.return_value.set_party_mode.assert_called_once_with(120, 4)

    @pytest.mark.asyncio
    async def test_stop_party_mode(self, mock_client):
        """Test stop_party_mode delegates to client."""
        async with Info("test.local") as info:
            await info.stop_party_mode()

        # Verify client method was called
        mock_client.return_value.stop_party_mode.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_device_identity(self, mock_client, parsed_werte20_data):
        """Test get_device_identity returns parsed identity metadata."""
        mock_client.return_value.fetch_werte20.return_value = parsed_werte20_data

        async with Info("test.local") as info:
            identity = await info.get_device_identity()

        assert isinstance(identity, DeviceIdentity)
        assert identity.model == "KWL EC 300W R"
        assert identity.unique_id == "804b2001992a"

    @pytest.mark.asyncio
    async def test_get_party_state(self, mock_client, parsed_werte3_data):
        """Test get_party_state returns party metadata."""
        mock_client.return_value.fetch_werte3.return_value = parsed_werte3_data

        async with Info("test.local") as info:
            party_state = await info.get_party_state()

        assert isinstance(party_state, PartyState)
        assert party_state.active is True
        assert party_state.remaining_minutes == 45

    @pytest.mark.asyncio
    async def test_get_snapshot_returns_combined_data(
        self,
        mock_client,
        parsed_werte8_data,
        parsed_werte20_data,
        parsed_werte3_data,
    ):
        """Test get_snapshot combines status, identity, and party state."""
        mock_client.return_value.fetch_werte8.return_value = parsed_werte8_data
        mock_client.return_value.fetch_werte20.return_value = parsed_werte20_data
        mock_client.return_value.fetch_werte3.return_value = parsed_werte3_data

        async with Info("test.local") as info:
            snapshot = await info.get_snapshot()

        assert isinstance(snapshot, HeliosSnapshot)
        assert snapshot.status.host == "test.local"
        assert snapshot.identity is not None
        assert snapshot.identity.model == "KWL EC 300W R"
        assert snapshot.party_state.active is True
        assert snapshot.party_state.remaining_minutes == 45

    @pytest.mark.asyncio
    async def test_get_snapshot_falls_back_when_optional_fetches_fail(
        self,
        mock_client,
        parsed_werte8_data,
    ):
        """Test get_snapshot still returns status when extra reads fail."""
        from custom_components.helios_kwl_ec300._core.exceptions import NetworkError

        mock_client.return_value.fetch_werte8.return_value = parsed_werte8_data
        mock_client.return_value.fetch_werte20.side_effect = NetworkError("boom")
        mock_client.return_value.fetch_werte3.side_effect = NetworkError("boom")

        async with Info("test.local") as info:
            snapshot = await info.get_snapshot()

        assert snapshot.identity is None
        assert snapshot.party_state.active is False
        assert snapshot.party_state.fan_stage == 3

    @pytest.mark.asyncio
    async def test_validate_connection_returns_snapshot(
        self,
        mock_client,
        parsed_werte8_data,
        parsed_werte20_data,
        parsed_werte3_data,
    ):
        """Test validate_connection proxies to get_snapshot."""
        mock_client.return_value.fetch_werte8.return_value = parsed_werte8_data
        mock_client.return_value.fetch_werte20.return_value = parsed_werte20_data
        mock_client.return_value.fetch_werte3.return_value = parsed_werte3_data

        async with Info("test.local") as info:
            snapshot = await info.validate_connection()

        assert isinstance(snapshot, HeliosSnapshot)
        assert snapshot.identity is not None
