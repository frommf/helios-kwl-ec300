"""Tests for coordinator behavior in the Home Assistant integration."""

from __future__ import annotations

from unittest.mock import AsyncMock

import pytest
from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers.update_coordinator import UpdateFailed

from custom_components.helios_kwl_ec300._core import AuthenticationError
from custom_components.helios_kwl_ec300.coordinator import (
    HeliosDataUpdateCoordinator,
    HeliosSettings,
    persist_settings,
    settings_from_entry,
)


def test_settings_from_entry(config_entry) -> None:
    """Config entry options are mapped into runtime settings."""
    settings = settings_from_entry(config_entry)

    assert settings.scan_interval_seconds == 30
    assert settings.party_duration_minutes == 90
    assert settings.party_fan_stage == 3


def test_persist_settings(hass, runtime_data) -> None:
    """Persisting settings updates config entry options."""
    runtime_data.settings.party_duration_minutes = 120
    runtime_data.settings.party_fan_stage = 4

    persist_settings(hass, runtime_data)

    assert runtime_data.config_entry.options["party_duration_minutes"] == 120
    assert runtime_data.config_entry.options["party_fan_stage"] == 4
    assert hass.config_entries.updated_entries


class _FakeApiBase:
    """Shared no-op implementations for the HeliosApi protocol."""

    async def set_party_mode(self, duration_minutes: int, fan_stage: int) -> None:
        pass

    async def stop_party_mode(self) -> None:
        pass


@pytest.mark.asyncio
async def test_async_update_data_returns_snapshot(hass, config_entry, sample_snapshot) -> None:
    """Coordinator returns the snapshot from the API layer."""

    class FakeApi(_FakeApiBase):
        async def get_snapshot(self):
            return sample_snapshot

    coordinator = HeliosDataUpdateCoordinator(
        hass,
        config_entry,
        FakeApi(),
        HeliosSettings(),
    )

    data = await coordinator._async_update_data()
    assert data == sample_snapshot


@pytest.mark.asyncio
async def test_async_update_data_maps_auth_failures(hass, config_entry) -> None:
    """Authentication errors become HA config entry auth failures."""

    class FakeApi(_FakeApiBase):
        async def get_snapshot(self):
            raise AuthenticationError("nope")

    coordinator = HeliosDataUpdateCoordinator(
        hass,
        config_entry,
        FakeApi(),
        HeliosSettings(),
    )

    with pytest.raises(ConfigEntryAuthFailed):
        await coordinator._async_update_data()


@pytest.mark.asyncio
async def test_async_update_data_maps_general_failures(hass, config_entry) -> None:
    """Other Helios errors become HA update failures."""

    class FakeApi(_FakeApiBase):
        async def get_snapshot(self):
            raise AuthenticationError("nope")

    coordinator = HeliosDataUpdateCoordinator(
        hass,
        config_entry,
        FakeApi(),
        HeliosSettings(),
    )

    coordinator.api = SimpleApiError()
    with pytest.raises(UpdateFailed):
        await coordinator._async_update_data()


class SimpleApiError(_FakeApiBase):
    """Fake API that raises a generic Helios error."""

    async def get_snapshot(self):
        from custom_components.helios_kwl_ec300._core import NetworkError

        raise NetworkError("offline")


@pytest.mark.asyncio
async def test_async_set_fan_stage_refreshes_without_optimistic_state(
    runtime_data, sample_snapshot
) -> None:
    """Fan-stage writes refresh once without assigning an optimistic target."""
    original_snapshot = runtime_data.coordinator.data
    refreshed_snapshot = sample_snapshot.model_copy(deep=True)
    runtime_data.api.set_fan_stage = AsyncMock()
    runtime_data.coordinator.api = runtime_data.api
    runtime_data.coordinator.async_request_refresh = AsyncMock(return_value=refreshed_snapshot)

    await runtime_data.coordinator.async_set_fan_stage(2)

    runtime_data.api.set_fan_stage.assert_awaited_once_with(2)
    runtime_data.coordinator.async_request_refresh.assert_awaited_once()
    assert runtime_data.coordinator.data is original_snapshot


@pytest.mark.asyncio
@pytest.mark.parametrize("enabled", [True, False])
async def test_async_set_automatic_mode_refreshes_actual_state(
    runtime_data, sample_snapshot, enabled
) -> None:
    """Automatic-mode writes delegate once and then request one actual-state refresh."""
    refreshed_snapshot = sample_snapshot.model_copy(deep=True)
    runtime_data.api.set_automatic_mode = AsyncMock()
    runtime_data.coordinator.api = runtime_data.api
    runtime_data.coordinator.async_request_refresh = AsyncMock(return_value=refreshed_snapshot)

    await runtime_data.coordinator.async_set_automatic_mode(enabled)

    runtime_data.api.set_automatic_mode.assert_awaited_once_with(enabled)
    runtime_data.coordinator.async_request_refresh.assert_awaited_once()


@pytest.mark.asyncio
async def test_async_start_party_mode_uses_runtime_defaults(runtime_data, sample_snapshot) -> None:
    """Party mode start uses configured defaults and refreshes state."""
    runtime_data.api.set_party_mode = AsyncMock()
    runtime_data.coordinator.api = runtime_data.api
    runtime_data.coordinator.async_request_refresh = AsyncMock(return_value=sample_snapshot)

    await runtime_data.coordinator.async_start_party_mode()

    runtime_data.api.set_party_mode.assert_awaited_once_with(duration_minutes=90, fan_stage=3)
    runtime_data.coordinator.async_request_refresh.assert_awaited_once()


@pytest.mark.asyncio
async def test_async_stop_party_mode_refreshes_state(runtime_data, sample_snapshot) -> None:
    """Stopping party mode forwards to the API and refreshes state."""
    runtime_data.api.stop_party_mode = AsyncMock()
    runtime_data.coordinator.api = runtime_data.api
    runtime_data.coordinator.async_request_refresh = AsyncMock(return_value=sample_snapshot)

    await runtime_data.coordinator.async_stop_party_mode()

    runtime_data.api.stop_party_mode.assert_awaited_once_with()
    runtime_data.coordinator.async_request_refresh.assert_awaited_once()
