"""Shared entity helpers for the Helios integration."""

from __future__ import annotations

from homeassistant.helpers.device_registry import CONNECTION_NETWORK_MAC, DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from ._core.models import HeliosSnapshot
from .const import DOMAIN, MANUFACTURER
from .coordinator import HeliosDataUpdateCoordinator, HeliosRuntimeData


class HeliosEntity(CoordinatorEntity[HeliosDataUpdateCoordinator]):
    """Common entity base wired to the shared coordinator."""

    _attr_has_entity_name = True

    def __init__(self, runtime_data: HeliosRuntimeData, unique_suffix: str) -> None:
        super().__init__(runtime_data.coordinator)
        self.runtime_data = runtime_data
        self._attr_unique_id = f"{runtime_data.device_identifier}_{unique_suffix}"

    @property
    def snapshot(self) -> HeliosSnapshot:
        """Return the current coordinator snapshot."""
        return self.coordinator.data

    @property
    def device_info(self) -> DeviceInfo:
        """Describe the shared Helios ventilation unit in the device registry."""
        identity = self.snapshot.identity
        device_info: dict[str, object] = {
            "identifiers": {(DOMAIN, self.runtime_data.device_identifier)},
            "manufacturer": MANUFACTURER,
            "name": identity.model
            if identity and identity.model
            else self.runtime_data.config_entry.title,
            "model": identity.model if identity else None,
            "sw_version": identity.firmware_version if identity else None,
            "configuration_url": f"http://{self.snapshot.status.host}",
        }

        if identity and identity.mac_address:
            device_info["connections"] = {(CONNECTION_NETWORK_MAC, identity.mac_address)}

        return DeviceInfo(**device_info)
