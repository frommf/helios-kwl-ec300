"""Tests for integration setup and diagnostics helpers."""

from __future__ import annotations

import pytest

from custom_components.helios_kwl_ec300 import async_setup_entry, async_unload_entry
from custom_components.helios_kwl_ec300.const import DOMAIN, PLATFORMS
from custom_components.helios_kwl_ec300.diagnostics import async_get_config_entry_diagnostics


@pytest.mark.asyncio
async def test_async_setup_entry_stores_runtime_data(
    monkeypatch, hass, config_entry, sample_snapshot
) -> None:
    """Setup creates runtime data and forwards platform setup."""

    class FakeCoordinator:
        def __init__(self, hass, entry, api, settings):
            self.hass = hass
            self.entry = entry
            self.api = api
            self.settings = settings
            self.data = sample_snapshot

        async def async_config_entry_first_refresh(self) -> None:
            return None

    monkeypatch.setattr(
        "custom_components.helios_kwl_ec300.coordinator.HeliosDataUpdateCoordinator",
        FakeCoordinator,
    )

    result = await async_setup_entry(hass, config_entry)

    assert result is True
    assert DOMAIN in hass.data
    assert config_entry.entry_id in hass.data[DOMAIN]
    assert hass.config_entries.forwarded == [(config_entry, PLATFORMS)]


@pytest.mark.asyncio
async def test_async_unload_entry_removes_runtime_data(hass, config_entry, runtime_data) -> None:
    """Unload removes stored runtime data after platform unload succeeds."""
    hass.data[DOMAIN] = {config_entry.entry_id: runtime_data}

    result = await async_unload_entry(hass, config_entry)

    assert result is True
    assert hass.config_entries.unloaded == [(config_entry, PLATFORMS)]
    assert hass.data[DOMAIN] == {}


@pytest.mark.asyncio
async def test_diagnostics_redacts_password(hass, config_entry, runtime_data) -> None:
    """Diagnostics redact credentials while exposing snapshot data."""
    hass.data[DOMAIN] = {config_entry.entry_id: runtime_data}

    diagnostics = await async_get_config_entry_diagnostics(hass, config_entry)

    assert diagnostics["entry"]["data"]["password"] == "REDACTED"
    assert diagnostics["snapshot"]["status"]["host"] == "helios.fritz.box"
