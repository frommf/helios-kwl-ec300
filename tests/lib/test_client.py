"""Tests for HeliosClient."""

from unittest.mock import AsyncMock

import pytest

from custom_components.helios_kwl_ec300._core.client import HeliosClient
from custom_components.helios_kwl_ec300._core.constants import (
    AUTH_ENDPOINT,
    DATA_ENDPOINT,
    IDENTITY_ENDPOINT,
    PARTY_ENDPOINT,
    PARTY_STATE_ENDPOINT,
)
from custom_components.helios_kwl_ec300._core.exceptions import AuthenticationError, ProtocolError
from custom_components.helios_kwl_ec300._core.transport import HTTPResponse


@pytest.fixture
def mock_transport(mocker):
    """Mock AsyncHTTP10Transport with async post method."""
    mock = mocker.patch("custom_components.helios_kwl_ec300._core.client.AsyncHTTP10Transport")
    # Make post() return an AsyncMock so it can be awaited
    mock.return_value.post = AsyncMock()
    return mock


class TestHeliosClient:
    """Tests for HeliosClient class."""

    def test_client_initialization(self):
        """Test client initializes with correct defaults."""
        client = HeliosClient("test.local")

        assert client.host == "test.local"
        assert client.password == "!helios!"
        assert client.timeout == 10.0
        assert client._authenticated is False

    def test_client_custom_password(self):
        """Test client accepts custom password."""
        client = HeliosClient("test.local", password="custom_password")

        assert client.password == "custom_password"

    def test_client_custom_timeout(self):
        """Test client accepts custom timeout."""
        client = HeliosClient("test.local", timeout=30.0)

        assert client.timeout == 30.0

    @pytest.mark.asyncio
    async def test_client_context_manager(self, mock_transport):
        """Test client works as async context manager."""
        async with HeliosClient("test.local") as client:
            assert isinstance(client, HeliosClient)

    @pytest.mark.asyncio
    async def test_login_success(self, mock_transport):
        """Test successful login."""
        mock_transport.return_value.post.return_value = HTTPResponse(
            status_code=200, headers={}, body=b""
        )

        client = HeliosClient("test.local")
        await client.login()

        # Verify login was called with correct parameters
        mock_transport.return_value.post.assert_called_once()
        call_args = mock_transport.return_value.post.call_args
        assert call_args[0][0] == AUTH_ENDPOINT
        assert "v00402=!helios!" in call_args[0][1]

        assert client._authenticated is True

    @pytest.mark.asyncio
    async def test_login_failure(self, mock_transport):
        """Test login failure with non-200 status."""
        mock_transport.return_value.post.return_value = HTTPResponse(
            status_code=403, headers={}, body=b""
        )

        client = HeliosClient("test.local")

        with pytest.raises(AuthenticationError, match="Login failed"):
            await client.login()

        assert client._authenticated is False

    @pytest.mark.asyncio
    async def test_login_custom_password(self, mock_transport):
        """Test login uses custom password."""
        mock_transport.return_value.post.return_value = HTTPResponse(
            status_code=200, headers={}, body=b""
        )

        client = HeliosClient("test.local", password="custom")
        await client.login()

        call_args = mock_transport.return_value.post.call_args
        assert "v00402=custom" in call_args[0][1]

    @pytest.mark.asyncio
    async def test_fetch_werte8_success(self, mock_transport):
        """Test successful fetch_werte8."""
        xml_response = b"""<?xml version="1.0" encoding="UTF-8"?>
<PARAMETER>
<ID>v00104</ID>
<VA>8.6</VA>
<ID>v00105</ID>
<VA>22.3</VA>
</PARAMETER>"""

        mock_transport.return_value.post.return_value = HTTPResponse(
            status_code=200, headers={}, body=xml_response
        )

        client = HeliosClient("test.local")
        data = await client.fetch_werte8()

        # Verify request was made correctly
        mock_transport.return_value.post.assert_called_once()
        call_args = mock_transport.return_value.post.call_args
        assert call_args[0][0] == DATA_ENDPOINT
        assert "xml=/data/werte8.xml" in call_args[0][1]

        # Verify data was parsed
        assert isinstance(data, dict)
        assert data["v00104"] == "8.6"
        assert data["v00105"] == "22.3"

    @pytest.mark.asyncio
    async def test_fetch_werte8_auto_login_on_403(self, mock_transport):
        """Test automatic login and retry on 403 Forbidden."""
        xml_response = b"""<?xml version="1.0" encoding="UTF-8"?>
<PARAMETER>
<ID>v00104</ID>
<VA>8.6</VA>
</PARAMETER>"""

        # First call returns 403, second (login) returns 200, third (retry) returns 200 with data
        mock_transport.return_value.post.side_effect = [
            HTTPResponse(status_code=403, headers={}, body=b""),  # Initial fetch
            HTTPResponse(status_code=200, headers={}, body=b""),  # Login
            HTTPResponse(status_code=200, headers={}, body=xml_response),  # Retry fetch
        ]

        client = HeliosClient("test.local")
        data = await client.fetch_werte8()

        # Verify three calls were made: fetch, login, fetch
        assert mock_transport.return_value.post.call_count == 3

        # First call: fetch werte8
        call1 = mock_transport.return_value.post.call_args_list[0]
        assert call1[0][0] == DATA_ENDPOINT

        # Second call: login
        call2 = mock_transport.return_value.post.call_args_list[1]
        assert call2[0][0] == AUTH_ENDPOINT

        # Third call: retry fetch
        call3 = mock_transport.return_value.post.call_args_list[2]
        assert call3[0][0] == DATA_ENDPOINT

        # Verify data was returned
        assert data["v00104"] == "8.6"

    @pytest.mark.asyncio
    async def test_fetch_werte8_403_after_login_fails(self, mock_transport):
        """Test 403 after login attempt raises AuthenticationError."""
        # First call returns 403, second (login) returns 200, third (retry) also returns 403
        mock_transport.return_value.post.side_effect = [
            HTTPResponse(status_code=403, headers={}, body=b""),  # Initial fetch
            HTTPResponse(status_code=200, headers={}, body=b""),  # Login
            HTTPResponse(status_code=403, headers={}, body=b""),  # Retry fetch still 403
        ]

        client = HeliosClient("test.local")

        with pytest.raises(AuthenticationError, match="Access forbidden.*after login attempt"):
            await client.fetch_werte8()

    @pytest.mark.asyncio
    async def test_fetch_werte8_no_retry_on_403(self, mock_transport):
        """Test 403 raises immediately when retry_auth=False."""
        mock_transport.return_value.post.return_value = HTTPResponse(
            status_code=403, headers={}, body=b""
        )

        client = HeliosClient("test.local")

        with pytest.raises(AuthenticationError, match="Access forbidden.*after login attempt"):
            await client.fetch_werte8(retry_auth=False)

        # Verify only one call was made (no retry)
        assert mock_transport.return_value.post.call_count == 1

    @pytest.mark.asyncio
    async def test_fetch_werte8_unexpected_status(self, mock_transport):
        """Test unexpected status code raises ProtocolError."""
        mock_transport.return_value.post.return_value = HTTPResponse(
            status_code=500, headers={}, body=b"Internal Server Error"
        )

        client = HeliosClient("test.local")

        with pytest.raises(ProtocolError, match="Unexpected status 500"):
            await client.fetch_werte8()

    @pytest.mark.asyncio
    async def test_fetch_werte8_malformed_xml(self, mock_transport):
        """Test malformed XML raises ParseError."""
        mock_transport.return_value.post.return_value = HTTPResponse(
            status_code=200, headers={}, body=b"<INVALID>XML"
        )

        client = HeliosClient("test.local")

        # ParseError should be raised from parse_werte8_xml
        from custom_components.helios_kwl_ec300._core.exceptions import ParseError

        with pytest.raises(ParseError):
            await client.fetch_werte8()

    @pytest.mark.asyncio
    async def test_fetch_werte8_with_real_fixture(self, mock_transport, sample_werte8_xml):
        """Test fetch_werte8 with real XML fixture."""
        mock_transport.return_value.post.return_value = HTTPResponse(
            status_code=200, headers={}, body=sample_werte8_xml
        )

        client = HeliosClient("test.local")
        data = await client.fetch_werte8()

        # Verify real data was parsed correctly
        assert "v00104" in data  # Outdoor air
        assert "v00105" in data  # Supply air
        assert "v00102" in data  # Fan stage
        assert isinstance(data, dict)

    @pytest.mark.asyncio
    async def test_multiple_fetch_werte8_calls(self, mock_transport):
        """Test multiple sequential fetch calls."""
        xml_response = b"""<?xml version="1.0" encoding="UTF-8"?>
<PARAMETER>
<ID>v00104</ID>
<VA>8.6</VA>
</PARAMETER>"""

        mock_transport.return_value.post.return_value = HTTPResponse(
            status_code=200, headers={}, body=xml_response
        )

        client = HeliosClient("test.local")

        # Call multiple times
        data1 = await client.fetch_werte8()
        data2 = await client.fetch_werte8()

        assert data1 == data2
        assert mock_transport.return_value.post.call_count == 2

    @pytest.mark.asyncio
    async def test_fetch_werte20_success(self, mock_transport):
        """Test successful fetch_werte20."""
        xml_response = b"""<?xml version="1.0" encoding="UTF-8"?>
<PARAMETER>
<ID>v00000</ID>
<VA>KWL EC 300W R</VA>
</PARAMETER>"""

        mock_transport.return_value.post.return_value = HTTPResponse(
            status_code=200, headers={}, body=xml_response
        )

        client = HeliosClient("test.local")
        data = await client.fetch_werte20()

        call_args = mock_transport.return_value.post.call_args
        assert call_args[0][0] == IDENTITY_ENDPOINT
        assert call_args[0][1] == f"xml={IDENTITY_ENDPOINT}"
        assert data["v00000"] == "KWL EC 300W R"

    @pytest.mark.asyncio
    async def test_fetch_werte3_success(self, mock_transport):
        """Test successful fetch_werte3."""
        xml_response = b"""<?xml version="1.0" encoding="UTF-8"?>
<PARAMETER>
<ID>v00093</ID>
<VA>45</VA>
</PARAMETER>"""

        mock_transport.return_value.post.return_value = HTTPResponse(
            status_code=200, headers={}, body=xml_response
        )

        client = HeliosClient("test.local")
        data = await client.fetch_werte3()

        call_args = mock_transport.return_value.post.call_args
        assert call_args[0][0] == PARTY_STATE_ENDPOINT
        assert call_args[0][1] == f"xml={PARTY_STATE_ENDPOINT}"
        assert data["v00093"] == "45"

    @pytest.mark.asyncio
    async def test_fetch_xml_data_rejects_non_data_endpoint(self, mock_transport):
        """Test fetch_xml_data blocks endpoints outside the read-only XML area."""
        client = HeliosClient("test.local")

        with pytest.raises(ValueError, match="Unsupported XML endpoint"):
            await client.fetch_xml_data("/info.htm")

    @pytest.mark.asyncio
    async def test_set_party_mode_success(self, mock_transport):
        """Test successful party mode activation."""
        mock_transport.return_value.post.return_value = HTTPResponse(
            status_code=200, headers={}, body=b""
        )

        client = HeliosClient("test.local")
        await client.set_party_mode(duration_minutes=90, fan_stage=3)

        # Verify request was made correctly
        mock_transport.return_value.post.assert_called_once()
        call_args = mock_transport.return_value.post.call_args
        assert call_args[0][0] == PARTY_ENDPOINT
        assert "v00092=3" in call_args[0][1]  # Fan stage
        assert "v00091=90" in call_args[0][1]  # Duration
        assert "v00093=0" in call_args[0][1]  # Remaining time
        assert "v00094=1" in call_args[0][1]  # Activation flag

    @pytest.mark.asyncio
    async def test_set_party_mode_auto_login_on_403(self, mock_transport):
        """Test automatic login and retry on 403 Forbidden."""
        # First call returns 403, second (login) returns 200, third (retry) returns 200
        mock_transport.return_value.post.side_effect = [
            HTTPResponse(status_code=403, headers={}, body=b""),  # Initial set attempt
            HTTPResponse(status_code=200, headers={}, body=b""),  # Login
            HTTPResponse(status_code=200, headers={}, body=b""),  # Retry set
        ]

        client = HeliosClient("test.local")
        await client.set_party_mode(duration_minutes=120, fan_stage=4)

        # Verify three calls were made: set, login, set
        assert mock_transport.return_value.post.call_count == 3

        # First call: set party mode
        call1 = mock_transport.return_value.post.call_args_list[0]
        assert call1[0][0] == PARTY_ENDPOINT

        # Second call: login
        call2 = mock_transport.return_value.post.call_args_list[1]
        assert call2[0][0] == AUTH_ENDPOINT

        # Third call: retry set
        call3 = mock_transport.return_value.post.call_args_list[2]
        assert call3[0][0] == PARTY_ENDPOINT

    @pytest.mark.asyncio
    async def test_set_party_mode_403_after_login_fails(self, mock_transport):
        """Test 403 after login attempt raises AuthenticationError."""
        # First call returns 403, second (login) returns 200, third (retry) also returns 403
        mock_transport.return_value.post.side_effect = [
            HTTPResponse(status_code=403, headers={}, body=b""),  # Initial attempt
            HTTPResponse(status_code=200, headers={}, body=b""),  # Login
            HTTPResponse(status_code=403, headers={}, body=b""),  # Retry still 403
        ]

        client = HeliosClient("test.local")

        with pytest.raises(AuthenticationError, match="Access forbidden.*after login attempt"):
            await client.set_party_mode(duration_minutes=90, fan_stage=3)

    @pytest.mark.asyncio
    async def test_set_party_mode_unexpected_status(self, mock_transport):
        """Test unexpected status code raises ProtocolError."""
        mock_transport.return_value.post.return_value = HTTPResponse(
            status_code=500, headers={}, body=b"Internal Server Error"
        )

        client = HeliosClient("test.local")

        with pytest.raises(ProtocolError, match="Unexpected status 500"):
            await client.set_party_mode(duration_minutes=90, fan_stage=3)

    @pytest.mark.asyncio
    async def test_set_party_mode_validates_params(self, mock_transport):
        """Test invalid parameters raise ValidationError."""
        from pydantic import ValidationError

        client = HeliosClient("test.local")

        # Invalid duration (too low)
        with pytest.raises(ValidationError):
            await client.set_party_mode(duration_minutes=4, fan_stage=3)

        # Invalid fan stage (too high)
        with pytest.raises(ValidationError):
            await client.set_party_mode(duration_minutes=90, fan_stage=5)

    @pytest.mark.asyncio
    async def test_set_party_mode_duration_rounding(self, mock_transport):
        """Test duration is rounded to nearest 5 minutes."""
        mock_transport.return_value.post.return_value = HTTPResponse(
            status_code=200, headers={}, body=b""
        )

        client = HeliosClient("test.local")
        await client.set_party_mode(duration_minutes=92, fan_stage=3)

        # Verify duration was rounded to 90
        call_args = mock_transport.return_value.post.call_args
        assert "v00091=90" in call_args[0][1]

    @pytest.mark.asyncio
    async def test_stop_party_mode_success(self, mock_transport):
        """Test successful party mode deactivation."""
        mock_transport.return_value.post.return_value = HTTPResponse(
            status_code=200, headers={}, body=b""
        )

        client = HeliosClient("test.local")
        await client.stop_party_mode()

        # Verify request was made correctly
        mock_transport.return_value.post.assert_called_once()
        call_args = mock_transport.return_value.post.call_args
        assert call_args[0][0] == PARTY_ENDPOINT
        assert "v00094=0" in call_args[0][1]  # Deactivation flag

    @pytest.mark.asyncio
    async def test_stop_party_mode_auto_login_on_403(self, mock_transport):
        """Test automatic login and retry on 403 Forbidden."""
        # First call returns 403, second (login) returns 200, third (retry) returns 200
        mock_transport.return_value.post.side_effect = [
            HTTPResponse(status_code=403, headers={}, body=b""),  # Initial stop attempt
            HTTPResponse(status_code=200, headers={}, body=b""),  # Login
            HTTPResponse(status_code=200, headers={}, body=b""),  # Retry stop
        ]

        client = HeliosClient("test.local")
        await client.stop_party_mode()

        # Verify three calls were made
        assert mock_transport.return_value.post.call_count == 3

        # Verify sequence
        call1 = mock_transport.return_value.post.call_args_list[0]
        assert call1[0][0] == PARTY_ENDPOINT

        call2 = mock_transport.return_value.post.call_args_list[1]
        assert call2[0][0] == AUTH_ENDPOINT

        call3 = mock_transport.return_value.post.call_args_list[2]
        assert call3[0][0] == PARTY_ENDPOINT
