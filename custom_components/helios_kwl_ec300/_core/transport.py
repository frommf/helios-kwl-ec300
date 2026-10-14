"""Async HTTP/1.0 transport for Helios KWL devices.

This module implements a custom async HTTP client using raw TCP sockets
because the Helios device requires HTTP/1.0 protocol and has a non-compliant
embedded web server that doesn't work reliably with standard HTTP libraries.
"""

import asyncio
from typing import NamedTuple

from .exceptions import NetworkError, ProtocolError


class HTTPResponse(NamedTuple):
    """HTTP response from the device.

    Attributes:
        status_code: HTTP status code (e.g., 200, 403)
        headers: Response headers (lowercase keys)
        body: Response body as bytes
    """

    status_code: int
    headers: dict[str, str]
    body: bytes


class AsyncHTTP10Transport:
    """Async HTTP/1.0 client using raw TCP sockets.

    Why not httpx/aiohttp?
    - Helios device requires HTTP/1.0 protocol
    - Standard libraries target HTTP/1.1+
    - Raw sockets give full control over protocol version

    Example:
        transport = AsyncHTTP10Transport("helios.fritz.box")
        response = await transport.post("/data/werte8.xml", "xml=/data/werte8.xml")
    """

    def __init__(self, host: str, port: int = 80, timeout: float = 10.0) -> None:
        """Initialize transport.

        Args:
            host: Hostname or IP address
            port: HTTP port (default: 80)
            timeout: Socket timeout in seconds (default: 10.0)
        """
        self.host = host
        self.port = port
        self.timeout = timeout

    async def post(
        self, path: str, body: str, headers: dict[str, str] | None = None
    ) -> HTTPResponse:
        """Send POST request with HTTP/1.0 protocol.

        Args:
            path: Request path (e.g., "/data/werte8.xml")
            body: Request body (URL-encoded form data)
            headers: Additional headers (optional)

        Returns:
            HTTPResponse with status code, headers, and body

        Raises:
            NetworkError: Network communication failure
            ProtocolError: Invalid HTTP response
        """
        # Build request headers
        headers = headers or {}
        headers.setdefault("Host", self.host)
        headers.setdefault("Content-Type", "application/x-www-form-urlencoded")
        headers.setdefault("Content-Length", str(len(body)))
        headers.setdefault("Connection", "close")

        # Build HTTP/1.0 request
        request_lines = [f"POST {path} HTTP/1.0"]
        request_lines.extend(f"{k}: {v}" for k, v in headers.items())
        request_lines.append("")  # Empty line before body
        request_lines.append(body)

        request_bytes = "\r\n".join(request_lines).encode("utf-8")

        # Send via async socket
        try:
            reader, writer = await asyncio.wait_for(
                asyncio.open_connection(self.host, self.port), timeout=self.timeout
            )

            writer.write(request_bytes)
            await writer.drain()

            # Read response
            chunks = []
            while True:
                chunk = await asyncio.wait_for(reader.read(4096), timeout=self.timeout)
                if not chunk:
                    break
                chunks.append(chunk)

            writer.close()
            await writer.wait_closed()

        except TimeoutError as e:
            raise NetworkError(f"Timeout connecting to {self.host}:{self.port}") from e
        except OSError as e:
            raise NetworkError(f"Network error: {e}") from e

        raw_response = b"".join(chunks)
        return self._parse_response(raw_response)

    def _parse_response(self, raw: bytes) -> HTTPResponse:
        """Parse HTTP response.

        Args:
            raw: Raw HTTP response bytes

        Returns:
            Parsed HTTPResponse

        Raises:
            ProtocolError: Invalid HTTP response format
        """
        # Split headers from body
        separator = b"\r\n\r\n" if b"\r\n\r\n" in raw else b"\n\n"

        if separator not in raw:
            raise ProtocolError("Invalid HTTP response: no header/body separator")

        header_part, body = raw.split(separator, 1)
        header_lines = header_part.decode("utf-8", errors="replace").split("\r\n")
        if not header_lines:
            header_lines = header_part.decode("utf-8", errors="replace").split("\n")

        # Parse status line
        status_line = header_lines[0]
        parts = status_line.split(" ", 2)
        if len(parts) < 2:
            raise ProtocolError(f"Invalid status line: {status_line}")

        try:
            status_code = int(parts[1])
        except ValueError as e:
            raise ProtocolError(f"Invalid status code: {parts[1]}") from e

        # Parse headers
        headers = {}
        for line in header_lines[1:]:
            if ":" in line:
                key, value = line.split(":", 1)
                headers[key.strip().lower()] = value.strip()

        return HTTPResponse(status_code, headers, body)
