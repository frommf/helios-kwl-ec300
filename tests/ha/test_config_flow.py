"""Tests for the Helios Home Assistant config flow."""

from __future__ import annotations

from unittest.mock import AsyncMock

import pytest

from custom_components.helios_kwl_ec300._core import AuthenticationError, NetworkError
from custom_components.helios_kwl_ec300.config_flow import (
    HeliosConfigFlow,
    ValidationResult,
    validate_input,
)


@pytest.mark.asyncio
async def test_validate_input_uses_identity_metadata(monkeypatch, hass, sample_snapshot) -> None:
    """Validation resolves a user-visible title and stable unique id."""
    fake_info = AsyncMock()
    fake_info.validate_connection.return_value = sample_snapshot
    monkeypatch.setattr(
        "custom_components.helios_kwl_ec300.config_flow.Info",
        lambda **kwargs: fake_info,
    )

    result = await validate_input(hass, {"host": "helios.fritz.box", "password": "!helios!"})

    assert result == ValidationResult(
        title="KWL EC 300W R (helios.fritz.box)",
        unique_id="804b2001992a",
    )


@pytest.mark.asyncio
async def test_user_step_success_creates_entry(monkeypatch, hass) -> None:
    """Successful validation creates a config entry with options."""
    monkeypatch.setattr(
        "custom_components.helios_kwl_ec300.config_flow.validate_input",
        AsyncMock(return_value=ValidationResult("Helios", "804b2001992a")),
    )
    flow = HeliosConfigFlow()
    flow.hass = hass

    result = await flow.async_step_user(
        {
            "host": "helios.fritz.box",
            "password": "!helios!",
            "scan_interval": 30,
            "party_duration_minutes": 90,
            "party_fan_stage": 3,
        }
    )

    assert result["type"] == "create_entry"
    assert result["data"]["host"] == "helios.fritz.box"
    assert result["options"]["party_fan_stage"] == 3


@pytest.mark.asyncio
async def test_user_step_handles_auth_error(monkeypatch, hass) -> None:
    """Authentication failures return the form with an auth error."""
    monkeypatch.setattr(
        "custom_components.helios_kwl_ec300.config_flow.validate_input",
        AsyncMock(side_effect=AuthenticationError("bad password")),
    )
    flow = HeliosConfigFlow()
    flow.hass = hass

    result = await flow.async_step_user({"host": "helios.fritz.box", "password": "bad"})

    assert result["type"] == "form"
    assert result["errors"] == {"base": "invalid_auth"}


@pytest.mark.asyncio
async def test_user_step_handles_connectivity_error(monkeypatch, hass) -> None:
    """Connectivity failures surface as cannot_connect in the form."""
    monkeypatch.setattr(
        "custom_components.helios_kwl_ec300.config_flow.validate_input",
        AsyncMock(side_effect=NetworkError("offline")),
    )
    flow = HeliosConfigFlow()
    flow.hass = hass

    result = await flow.async_step_user({"host": "helios.fritz.box", "password": "!helios!"})

    assert result["type"] == "form"
    assert result["errors"] == {"base": "cannot_connect"}
