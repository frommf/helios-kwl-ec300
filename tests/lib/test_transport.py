"""Tests for async HTTP/1.0 transport."""

import asyncio
from unittest.mock import AsyncMock, Mock

import pytest

from custom_components.helios_kwl_ec300._core.exceptions import NetworkError, ProtocolError
from custom_components.helios_kwl_ec300._core.transport import AsyncHTTP10Transport, HTTPResponse


@pytest.fixture
def mock_connection(mocker):
    """Mock asyncio.open_connection with proper sync/async methods."""
    reader = AsyncMock()
    writer = Mock()  # Writer has both sync and async methods

    # Async methods
    writer.drain = AsyncMock()
    writer.wait_closed = AsyncMock()

    # Sync methods (don't use AsyncMock)
    writer.write = Mock()
    writer.close = Mock()

    # Mock read to return data
    reader.read = AsyncMock()

    async def mock_open_connection(*args, **kwargs):
        return reader, writer

    mocker.patch("asyncio.open_connection", side_effect=mock_open_connection)
    return reader, writer


class TestAsyncHTTP10Transport:
    """Tests for AsyncHTTP10Transport."""

    @pytest.mark.asyncio
    async def test_post_builds_correct_http_request(self, mock_connection):
        """Verify HTTP/1.0 request format."""
        reader, writer = mock_connection

        # Simulate successful response
        reader.read.side_effect = [
            b"HTTP/1.0 200 OK\r\nContent-Type: text/xml\r\n\r\n<xml>test</xml>",
            b"",  # EOF
        ]

        transport = AsyncHTTP10Transport("test.local")
        await transport.post("/test", "key=value")

        # Verify correct HTTP/1.0 format was sent
        sent_data = writer.write.call_args[0][0]
        sent_str = sent_data.decode("utf-8")

        assert "POST /test HTTP/1.0" in sent_str
        assert "Connection: close" in sent_str
        assert "Content-Type: application/x-www-form-urlencoded" in sent_str
        assert "Content-Length: 9" in sent_str
        assert "key=value" in sent_str

    @pytest.mark.asyncio
    async def test_post_sends_correct_host_header(self, mock_connection):
        """Verify Host header is set correctly."""
        reader, writer = mock_connection

        reader.read.side_effect = [b"HTTP/1.0 200 OK\r\n\r\n", b""]

        transport = AsyncHTTP10Transport("helios.fritz.box")
        await transport.post("/data/werte8.xml", "xml=/data/werte8.xml")

        sent_data = writer.write.call_args[0][0]
        sent_str = sent_data.decode("utf-8")

        assert "Host: helios.fritz.box" in sent_str

    @pytest.mark.asyncio
    async def test_post_drains_writer(self, mock_connection):
        """Verify writer.drain() is called."""
        reader, writer = mock_connection

        reader.read.side_effect = [b"HTTP/1.0 200 OK\r\n\r\n", b""]

        transport = AsyncHTTP10Transport("test.local")
        await transport.post("/test", "body")

        writer.drain.assert_called_once()

    @pytest.mark.asyncio
    async def test_post_closes_connection(self, mock_connection):
        """Verify connection is closed properly."""
        reader, writer = mock_connection

        reader.read.side_effect = [b"HTTP/1.0 200 OK\r\n\r\n", b""]

        transport = AsyncHTTP10Transport("test.local")
        await transport.post("/test", "body")

        writer.close.assert_called_once()
        writer.wait_closed.assert_called_once()

    @pytest.mark.asyncio
    async def test_post_timeout_on_connection(self, mocker):
        """Test timeout during connection."""

        async def timeout_connect(*args, **kwargs):
            await asyncio.sleep(100)  # Will timeout

        mocker.patch("asyncio.open_connection", side_effect=timeout_connect)

        transport = AsyncHTTP10Transport("test.local", timeout=0.1)

        with pytest.raises(NetworkError, match="Timeout"):
            await transport.post("/test", "body")

    @pytest.mark.asyncio
    async def test_post_timeout_on_read(self, mock_connection):
        """Test timeout during read."""
        reader, writer = mock_connection

        async def timeout_read(*args, **kwargs):
            await asyncio.sleep(100)

        reader.read.side_effect = timeout_read

        transport = AsyncHTTP10Transport("test.local", timeout=0.1)

        with pytest.raises(NetworkError, match="Timeout"):
            await transport.post("/test", "body")

    @pytest.mark.asyncio
    async def test_post_network_error(self, mocker):
        """Test network error during connection."""

        async def raise_os_error(*args, **kwargs):
            raise OSError("Connection refused")

        mocker.patch("asyncio.open_connection", side_effect=raise_os_error)

        transport = AsyncHTTP10Transport("test.local")

        with pytest.raises(NetworkError, match="Network error"):
            await transport.post("/test", "body")

    @pytest.mark.asyncio
    async def test_post_returns_http_response(self, mock_connection):
        """Test successful POST returns HTTPResponse."""
        reader, writer = mock_connection

        reader.read.side_effect = [
            b"HTTP/1.0 200 OK\r\nContent-Type: text/xml\r\n\r\n<xml>data</xml>",
            b"",
        ]

        transport = AsyncHTTP10Transport("test.local")
        response = await transport.post("/test", "body")

        assert isinstance(response, HTTPResponse)
        assert response.status_code == 200
        assert response.body == b"<xml>data</xml>"
        assert response.headers["content-type"] == "text/xml"


class TestHTTPResponseParsing:
    """Tests for HTTP response parsing."""

    def test_parse_response_200_ok(self):
        """Test parsing 200 OK response."""
        transport = AsyncHTTP10Transport("test.local")
        raw = b"HTTP/1.0 200 OK\r\nContent-Type: text/xml\r\n\r\n<xml>test</xml>"

        response = transport._parse_response(raw)

        assert response.status_code == 200
        assert response.body == b"<xml>test</xml>"
        assert response.headers["content-type"] == "text/xml"

    def test_parse_response_403_forbidden(self):
        """Test parsing 403 Forbidden response."""
        transport = AsyncHTTP10Transport("test.local")
        raw = b"HTTP/1.0 403 Forbidden\r\n\r\n"

        response = transport._parse_response(raw)

        assert response.status_code == 403
        assert response.body == b""

    def test_parse_response_with_unix_newlines(self):
        """Test parsing response with Unix newlines (\\n instead of \\r\\n)."""
        transport = AsyncHTTP10Transport("test.local")
        raw = b"HTTP/1.0 200 OK\nContent-Type: text/xml\n\n<xml>test</xml>"

        response = transport._parse_response(raw)

        assert response.status_code == 200
        assert response.body == b"<xml>test</xml>"

    def test_parse_response_headers_lowercase(self):
        """Test headers are normalized to lowercase."""
        transport = AsyncHTTP10Transport("test.local")
        raw = b"HTTP/1.0 200 OK\r\nContent-Type: text/xml\r\nX-Custom-Header: value\r\n\r\n"

        response = transport._parse_response(raw)

        assert "content-type" in response.headers
        assert "x-custom-header" in response.headers
        assert response.headers["x-custom-header"] == "value"

    def test_parse_response_no_separator(self):
        """Test parsing fails without header/body separator."""
        transport = AsyncHTTP10Transport("test.local")
        raw = b"HTTP/1.0 200 OKContent-Type: text/xml"

        with pytest.raises(ProtocolError, match="no header/body separator"):
            transport._parse_response(raw)

    def test_parse_response_invalid_status_line(self):
        """Test parsing fails with invalid status line."""
        transport = AsyncHTTP10Transport("test.local")
        raw = b"INVALID\r\n\r\n"

        with pytest.raises(ProtocolError, match="Invalid status line"):
            transport._parse_response(raw)

    def test_parse_response_invalid_status_code(self):
        """Test parsing fails with non-numeric status code."""
        transport = AsyncHTTP10Transport("test.local")
        raw = b"HTTP/1.0 ABC OK\r\n\r\n"

        with pytest.raises(ProtocolError, match="Invalid status code"):
            transport._parse_response(raw)

    def test_parse_response_multiple_headers(self):
        """Test parsing response with multiple headers."""
        transport = AsyncHTTP10Transport("test.local")
        raw = (
            b"HTTP/1.0 200 OK\r\n"
            b"Content-Type: text/xml\r\n"
            b"Content-Length: 10\r\n"
            b"Connection: close\r\n"
            b"\r\n"
            b"<xml>test</xml>"
        )

        response = transport._parse_response(raw)

        assert response.headers["content-type"] == "text/xml"
        assert response.headers["content-length"] == "10"
        assert response.headers["connection"] == "close"

    def test_parse_response_empty_body(self):
        """Test parsing response with empty body."""
        transport = AsyncHTTP10Transport("test.local")
        raw = b"HTTP/1.0 403 Forbidden\r\n\r\n"

        response = transport._parse_response(raw)

        assert response.status_code == 403
        assert response.body == b""

    def test_parse_response_binary_body(self):
        """Test parsing response with binary body."""
        transport = AsyncHTTP10Transport("test.local")
        binary_data = b"\x00\x01\x02\x03\xff\xfe"
        raw = b"HTTP/1.0 200 OK\r\n\r\n" + binary_data

        response = transport._parse_response(raw)

        assert response.body == binary_data
