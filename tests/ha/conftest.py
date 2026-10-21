"""Pytest fixtures for the Home Assistant integration tests.

The fake ``homeassistant``/``voluptuous`` modules are installed by the root
``tests/conftest.py`` before any test module is collected (see
``tests/fake_ha.py``).
"""

from __future__ import annotations

import sys
from typing import TYPE_CHECKING, Any

import pytest

if TYPE_CHECKING:
    from custom_components.helios_kwl_ec300._core.models import HeliosSnapshot


@pytest.fixture
def hass() -> Any:
    """Return a fake Home Assistant instance."""
    core_module: Any = sys.modules["homeassistant.core"]
    return core_module.HomeAssistant()


@pytest.fixture
def config_entry() -> Any:
    """Return a fake config entry for the Helios integration."""
    config_entries_module: Any = sys.modules["homeassistant.config_entries"]
    const_module: Any = sys.modules["homeassistant.const"]
    config_entry_cls = config_entries_module.ConfigEntry
    conf_host = const_module.CONF_HOST
    conf_password = const_module.CONF_PASSWORD

    return config_entry_cls(
        entry_id="entry-1",
        title="Helios KWL",
        unique_id="804b2001992a",
        data={conf_host: "helios.fritz.box", conf_password: "!helios!"},
        options={
            "scan_interval": 30,
            "party_duration_minutes": 90,
            "party_fan_stage": 3,
        },
    )


@pytest.fixture
def sample_snapshot() -> HeliosSnapshot:
    """Return a representative Helios snapshot for HA entity tests."""
    from custom_components.helios_kwl_ec300._core.models import (
        DeviceIdentity,
        FanSpeed,
        HeliosSnapshot,
        HeliosStatus,
        OperationMode,
        PartyState,
        Temperature,
        Temperatures,
    )

    return HeliosSnapshot(
        status=HeliosStatus(
            temperatures=Temperatures(
                outdoor=Temperature(
                    variable_id="v00104",
                    label="Outdoor air",
                    value_celsius=8.6,
                    raw_value="8.6",
                ),
                supply=Temperature(
                    variable_id="v00105",
                    label="Supply air",
                    value_celsius=22.3,
                    raw_value="22.3",
                ),
                exhaust=Temperature(
                    variable_id="v00106",
                    label="Exhaust air",
                    value_celsius=18.5,
                    raw_value="18.5",
                ),
                extract=Temperature(
                    variable_id="v00107",
                    label="Extract air",
                    value_celsius=20.1,
                    raw_value="20.1",
                ),
            ),
            fan_speed=FanSpeed(
                stage=2,
                stage_percent=24.0,
                stage_label="S2 - Reduced ventilation",
                rpm_supply=1234,
                rpm_extract=1256,
            ),
            operation_mode=OperationMode(
                effective="Automatisch (Automatic)",
                party=False,
                quiet=False,
                holiday=False,
                manual=False,
                automatic=True,
                humidity_control="Continuous (Stufenlos)",
                co2_control="Continuous (Stufenlos)",
                voc_control="Continuous (Stufenlos)",
            ),
            host="helios.fritz.box",
        ),
        party_state=PartyState(
            active=False,
            configured_duration_minutes=120,
            fan_stage=3,
            remaining_minutes=0,
        ),
        identity=DeviceIdentity(
            model="KWL EC 300W R",
            firmware_version="04232003.hGP",
            mac_address="80:4B:20:01:99:2A",
            state_flags="10001101000001110000000010000001",
        ),
    )


@pytest.fixture
def runtime_data(
    hass: Any,
    config_entry: Any,
    sample_snapshot: HeliosSnapshot,
) -> Any:
    """Return coordinator runtime data shared by entity tests."""
    from custom_components.helios_kwl_ec300.coordinator import (
        HeliosDataUpdateCoordinator,
        HeliosRuntimeData,
        HeliosSettings,
    )

    class FakeApi:
        async def get_snapshot(self) -> HeliosSnapshot:
            return sample_snapshot

        async def set_party_mode(self, duration_minutes: int, fan_stage: int) -> None:
            self.last_set = (duration_minutes, fan_stage)

        async def stop_party_mode(self) -> None:
            self.stopped = True

    api = FakeApi()
    coordinator = HeliosDataUpdateCoordinator(
        hass,
        config_entry,
        api,
        HeliosSettings(scan_interval_seconds=30, party_duration_minutes=90, party_fan_stage=3),
    )
    coordinator.data = sample_snapshot
    return HeliosRuntimeData(
        api=api,
        coordinator=coordinator,
        config_entry=config_entry,
        settings=coordinator.settings,
        device_identifier="804b2001992a",
    )
