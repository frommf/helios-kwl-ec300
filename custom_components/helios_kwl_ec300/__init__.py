"""Home Assistant setup for the Helios KWL EC 300 integration.

Home Assistant imports are deferred into the setup functions so that the
device library (``._core``) can be imported standalone — e.g. by the CLI —
without Home Assistant installed.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from ._core import Info

if TYPE_CHECKING:
    from homeassistant.config_entries import ConfigEntry
    from homeassistant.core import HomeAssistant


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Helios from a config entry."""
    from homeassistant.const import CONF_HOST, CONF_PASSWORD

    from .const import DEFAULT_TIMEOUT_SECONDS, DOMAIN, PLATFORMS
    from .coordinator import (
        HeliosDataUpdateCoordinator,
        HeliosRuntimeData,
        settings_from_entry,
    )

    settings = settings_from_entry(entry)
    api = Info(
        host=entry.data[CONF_HOST],
        password=entry.data[CONF_PASSWORD],
        timeout=DEFAULT_TIMEOUT_SECONDS,
    )
    coordinator = HeliosDataUpdateCoordinator(hass, entry, api, settings)
    await coordinator.async_config_entry_first_refresh()

    identity = coordinator.data.identity
    device_identifier = (
        identity.unique_id
        if identity is not None and identity.unique_id is not None
        else str(entry.unique_id or entry.data[CONF_HOST]).lower()
    )

    runtime_data = HeliosRuntimeData(
        api=api,
        coordinator=coordinator,
        config_entry=entry,
        settings=settings,
        device_identifier=device_identifier,
    )
    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = runtime_data

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a Helios config entry."""
    from .const import DOMAIN, PLATFORMS

    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id, None)
    return unload_ok
