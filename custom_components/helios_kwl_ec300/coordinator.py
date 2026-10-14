"""Runtime data and coordinator for the Helios integration."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import timedelta
from typing import Protocol

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from ._core import AuthenticationError, HeliosError
from ._core.models import HeliosSnapshot
from .const import (
    CONF_PARTY_DURATION,
    CONF_PARTY_FAN_STAGE,
    CONF_SCAN_INTERVAL,
    DEFAULT_PARTY_DURATION_MINUTES,
    DEFAULT_PARTY_FAN_STAGE,
    DEFAULT_SCAN_INTERVAL_SECONDS,
    DOMAIN,
)

_LOGGER = logging.getLogger(__name__)


class HeliosApi(Protocol):
    """Structural interface for the Helios API used by the coordinator."""

    async def get_snapshot(self) -> HeliosSnapshot: ...

    async def set_party_mode(self, duration_minutes: int, fan_stage: int) -> None: ...

    async def stop_party_mode(self) -> None: ...


@dataclass(slots=True)
class HeliosSettings:
    """Mutable integration settings stored at runtime and in entry options."""

    scan_interval_seconds: int = DEFAULT_SCAN_INTERVAL_SECONDS
    party_duration_minutes: int = DEFAULT_PARTY_DURATION_MINUTES
    party_fan_stage: int = DEFAULT_PARTY_FAN_STAGE


@dataclass(slots=True)
class HeliosRuntimeData:
    """Shared runtime state for platform entities."""

    api: HeliosApi
    coordinator: HeliosDataUpdateCoordinator
    config_entry: ConfigEntry
    settings: HeliosSettings
    device_identifier: str


class HeliosDataUpdateCoordinator(DataUpdateCoordinator[HeliosSnapshot]):
    """Coordinate polling and write-through refreshes for Helios state."""

    def __init__(
        self,
        hass: HomeAssistant,
        config_entry: ConfigEntry,
        api: HeliosApi,
        settings: HeliosSettings,
    ) -> None:
        super().__init__(
            hass,
            _LOGGER,
            config_entry=config_entry,
            name=DOMAIN,
            update_interval=timedelta(seconds=settings.scan_interval_seconds),
            always_update=False,
        )
        self.api = api
        self.settings = settings

    async def _async_update_data(self) -> HeliosSnapshot:
        """Fetch the latest snapshot from the device."""
        try:
            return await self.api.get_snapshot()
        except AuthenticationError as err:
            raise ConfigEntryAuthFailed from err
        except HeliosError as err:
            raise UpdateFailed(f"Error communicating with Helios device: {err}") from err

    async def async_start_party_mode(
        self,
        duration_minutes: int | None = None,
        fan_stage: int | None = None,
    ) -> None:
        """Start party mode and refresh the shared snapshot."""
        duration = duration_minutes or self.settings.party_duration_minutes
        stage = fan_stage or self.settings.party_fan_stage
        await self.api.set_party_mode(duration_minutes=duration, fan_stage=stage)
        await self.async_request_refresh()

    async def async_stop_party_mode(self) -> None:
        """Stop party mode and refresh the shared snapshot."""
        await self.api.stop_party_mode()
        await self.async_request_refresh()


def settings_from_entry(config_entry: ConfigEntry) -> HeliosSettings:
    """Build runtime settings from persisted entry options."""
    return HeliosSettings(
        scan_interval_seconds=int(
            config_entry.options.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL_SECONDS)
        ),
        party_duration_minutes=int(
            config_entry.options.get(CONF_PARTY_DURATION, DEFAULT_PARTY_DURATION_MINUTES)
        ),
        party_fan_stage=int(
            config_entry.options.get(CONF_PARTY_FAN_STAGE, DEFAULT_PARTY_FAN_STAGE)
        ),
    )


def persist_settings(hass: HomeAssistant, runtime_data: HeliosRuntimeData) -> None:
    """Persist runtime settings back into config entry options."""
    hass.config_entries.async_update_entry(
        runtime_data.config_entry,
        options={
            CONF_SCAN_INTERVAL: runtime_data.settings.scan_interval_seconds,
            CONF_PARTY_DURATION: runtime_data.settings.party_duration_minutes,
            CONF_PARTY_FAN_STAGE: runtime_data.settings.party_fan_stage,
        },
    )
