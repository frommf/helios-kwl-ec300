"""Pytest configuration and fixtures for helios-kwl-ec300 tests."""

from pathlib import Path

import pytest


@pytest.fixture
def sample_werte8_xml() -> bytes:
    """Load sample werte8.xml response from fixture file."""
    fixture_path = Path(__file__).parent / "fixtures" / "werte8.xml"
    return fixture_path.read_bytes()


@pytest.fixture
def parsed_werte8_data() -> dict[str, str]:
    """Pre-parsed werte8 data for testing parsers and models."""
    return {
        "v00104": "8.6",  # Outdoor air
        "v00105": "22.3",  # Supply air
        "v00106": "18.5",  # Exhaust air
        "v00107": "20.1",  # Extract air
        "v00108": "-",  # Duct outdoor (not connected)
        "v00146": "-",  # Duct supply (not connected)
        "v00110": "-",  # Return HW (not connected)
        "v00102": "2",  # Fan stage
        "v00103": "24",  # Fan stage %
        "v00348": "1234",  # Supply RPM
        "v00349": "1256",  # Extract RPM
        "v00092": "3",  # Party mode target stage
        "v00101": "0",  # Auto/Manual (0 = auto)
        "v00094": "0",  # Party mode (0 = off)
        "v00099": "0",  # Quiet mode (0 = off)
        "v00601": "0",  # Holiday mode (0 = off)
        "v00033": "2",  # Humidity control (2 = continuous)
        "v00037": "2",  # CO2 control (2 = continuous)
        "v00040": "2",  # VOC control (2 = continuous)
    }


@pytest.fixture
def parsed_werte3_data() -> dict[str, str]:
    """Pre-parsed werte3 data for testing party state extraction."""
    return {
        "v00091": "120",
        "v00092": "3",
        "v00093": "45",
        "v00094": "1",
    }


@pytest.fixture
def parsed_werte20_data() -> dict[str, str]:
    """Pre-parsed werte20 data for testing device identity extraction."""
    return {
        "v01306": "10001101000001110000000010000001",
        "v00000": "KWL EC 300W R",
        "v00001": "04232003.hGP",
        "v00002": "80:4B:20:01:99:2A",
    }
