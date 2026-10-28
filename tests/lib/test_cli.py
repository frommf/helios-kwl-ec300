"""Tests for the Helios CLI operating-control commands."""

from unittest.mock import AsyncMock

import pytest

from helios_cli.main import main


@pytest.fixture
def mock_cli_info(mocker):
    """Mock the high-level API, including its async context manager."""
    mock_info = mocker.patch("helios_cli.main.Info")
    info = mock_info.return_value
    info.__aenter__ = AsyncMock(return_value=info)
    info.__aexit__ = AsyncMock(return_value=None)
    info.set_fan_stage = AsyncMock()
    info.set_automatic_mode = AsyncMock()
    return mock_info


def test_cli_fan_stage_sends_request_without_hardware_claim(mocker, mock_cli_info, capsys):
    """The fan-stage command delegates the request and reports only submission."""
    mocker.patch("sys.argv", ["helios", "--host", "test.local", "fan-stage", "2"])

    with pytest.raises(SystemExit) as exit_info:
        main()

    assert exit_info.value.code == 0
    info = mock_cli_info.return_value
    info.set_fan_stage.assert_awaited_once_with(2)
    info.set_automatic_mode.assert_not_called()
    stderr = capsys.readouterr().err
    assert "request sent" in stderr
    assert "hardware application is not verified" not in stderr


@pytest.mark.parametrize(("state", "enabled"), [("on", True), ("off", False)])
def test_cli_automatic_sends_request(mocker, mock_cli_info, capsys, state, enabled):
    """The automatic command maps on/off to the corresponding boolean request."""
    mocker.patch("sys.argv", ["helios", "automatic", state])

    with pytest.raises(SystemExit) as exit_info:
        main()

    assert exit_info.value.code == 0
    mock_cli_info.return_value.set_automatic_mode.assert_awaited_once_with(enabled)
    assert "hardware application is not verified" not in capsys.readouterr().err


@pytest.mark.parametrize("stage", ["0", "5", "6", "invalid"])
def test_cli_rejects_invalid_stage_before_api_creation(mocker, mock_cli_info, stage):
    """Argparse rejects invalid stages without constructing the device API."""
    mocker.patch("sys.argv", ["helios", "fan-stage", stage])

    with pytest.raises(SystemExit) as exit_info:
        main()

    assert exit_info.value.code == 2
    mock_cli_info.assert_not_called()


def test_cli_rejects_invalid_automatic_state_before_api_creation(mocker, mock_cli_info):
    """Argparse accepts only explicit on/off values for automatic mode."""
    mocker.patch("sys.argv", ["helios", "automatic", "1"])

    with pytest.raises(SystemExit) as exit_info:
        main()

    assert exit_info.value.code == 2
    mock_cli_info.assert_not_called()
