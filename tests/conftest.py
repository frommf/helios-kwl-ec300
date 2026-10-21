"""Root pytest configuration.

The project deliberately has no real Home Assistant dependency: the fake
``homeassistant``/``voluptuous`` modules are installed here, before any test
module is collected, so that importing ``custom_components.helios_kwl_ec300``
works in every test run — including ``tests/lib`` on its own.
"""

from __future__ import annotations

import sys
from pathlib import Path

from fake_ha import install_fake_homeassistant, install_fake_voluptuous

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

if "voluptuous" not in sys.modules:
    install_fake_voluptuous()

if "homeassistant" not in sys.modules:
    install_fake_homeassistant()
