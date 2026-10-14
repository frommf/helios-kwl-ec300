"""Smoke tests for Home Assistant integration module imports."""

from __future__ import annotations

import importlib

import pytest

MODULES = [
    "custom_components.helios_kwl_ec300",
    "custom_components.helios_kwl_ec300.const",
    "custom_components.helios_kwl_ec300.coordinator",
    "custom_components.helios_kwl_ec300.entity",
    "custom_components.helios_kwl_ec300.config_flow",
    "custom_components.helios_kwl_ec300.fan",
    "custom_components.helios_kwl_ec300.sensor",
    "custom_components.helios_kwl_ec300.number",
    "custom_components.helios_kwl_ec300.select",
    "custom_components.helios_kwl_ec300.diagnostics",
]


@pytest.mark.parametrize("module_name", MODULES)
def test_module_imports(module_name: str) -> None:
    """Ensure all integration modules import without Home Assistant installed."""
    module = importlib.import_module(module_name)
    assert module is not None
