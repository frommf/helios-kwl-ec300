"""Custom exceptions for Helios KWL library."""


class HeliosError(Exception):
    """Base exception for all Helios KWL errors."""

    pass


class NetworkError(HeliosError):
    """Network communication failure (timeout, connection refused, etc.)."""

    pass


class AuthenticationError(HeliosError):
    """Failed to authenticate with the device (403 Forbidden even after login attempt)."""

    pass


class ParseError(HeliosError):
    """Failed to parse XML response from device."""

    pass


class ProtocolError(HeliosError):
    """HTTP protocol violation or unexpected response from device."""

    pass


class PartyModeError(HeliosError):
    """Party mode operation failed."""

    pass
