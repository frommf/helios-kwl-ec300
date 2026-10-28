"""Opt-in real-hardware timing measurement for normal operating controls.

This file is outside the default pytest test paths. Even when selected explicitly,
it skips before creating a device connection unless HELIOS_LIVE_TEST=1 is set.
"""

import asyncio
import os
from collections.abc import Callable
from time import monotonic

import pytest

from custom_components.helios_kwl_ec300._core import Info
from custom_components.helios_kwl_ec300._core.models import HeliosStatus

pytestmark = [
    pytest.mark.live,
    pytest.mark.skipif(
        os.environ.get("HELIOS_LIVE_TEST") != "1",
        reason="real hardware writes require explicit HELIOS_LIVE_TEST=1",
    ),
]

POLL_INTERVAL_SECONDS = 1.0
MEASUREMENT_TIMEOUT_SECONDS = 30.0
STABLE_POLL_COUNT = 3


async def _wait_for_state(
    helios: Info,
    predicate: Callable[[HeliosStatus], bool],
) -> HeliosStatus | None:
    """Poll read-only until the predicate matches or the 30-second limit expires."""
    deadline = monotonic() + MEASUREMENT_TIMEOUT_SECONDS
    while True:
        status = await helios.get_status()
        if predicate(status):
            return status
        if monotonic() >= deadline:
            return None
        await asyncio.sleep(POLL_INTERVAL_SECONDS)


async def _restore_initial_state(helios: Info) -> None:
    """Restore manual stage 1, then base automatic mode, with read verification."""
    stage_status = None
    try:
        await helios.set_fan_stage(1)
        stage_status = await _wait_for_state(
            helios,
            lambda status: status.operation_mode.manual and status.fan_speed.base_stage == 1,
        )
    finally:
        # Always request the original base automatic mode, even if stage restore fails.
        await helios.set_automatic_mode(True)

    automatic_status = await _wait_for_state(
        helios,
        lambda status: not status.operation_mode.manual,
    )

    assert stage_status is not None, "Manual stage 1 was not read back during restoration"
    assert automatic_status is not None, "Base automatic mode was not read back during restoration"
    print("Restoration verified: stage 1 was read back and base automatic mode is on")


@pytest.mark.asyncio
async def test_operating_control_timing() -> None:
    """Measure auto/stage 1 to manual/stage 2 using exactly one measurement write."""
    async with Info() as helios:
        initial = await helios.get_status()
        if not initial.operation_mode.automatic or initial.fan_speed.base_stage != 1:
            pytest.fail(
                "Precondition requires effective automatic mode and base stage 1; "
                "aborting without a measurement write"
            )

        write_attempted = False
        try:
            started = monotonic()
            deadline = started + MEASUREMENT_TIMEOUT_SECONDS
            write_attempted = True
            await helios.set_fan_stage(2)

            first_seen: tuple[float, int] | None = None
            stable_since: tuple[float, int] | None = None
            consecutive_matches = 0
            poll_count = 0

            while True:
                poll_started = monotonic()
                status = await helios.get_status()
                elapsed = monotonic() - started
                poll_count += 1
                manual = status.operation_mode.manual
                stage = status.fan_speed.base_stage
                matches = manual and stage == 2
                print(
                    f"poll={poll_count:02d} elapsed={elapsed:6.3f}s "
                    f"manual={manual} base_stage={stage} target_match={matches}"
                )

                if matches:
                    if first_seen is None:
                        first_seen = (elapsed, poll_count)
                    consecutive_matches += 1
                    if consecutive_matches == STABLE_POLL_COUNT:
                        stable_since = (elapsed, poll_count)
                        break
                else:
                    consecutive_matches = 0

                if monotonic() >= deadline:
                    break
                remaining_interval = POLL_INTERVAL_SECONDS - (monotonic() - poll_started)
                if remaining_interval > 0:
                    await asyncio.sleep(remaining_interval)

            if first_seen is None:
                print("Target was not returned within the 30-second measurement window")
            else:
                print(f"First target response: poll={first_seen[1]}, elapsed={first_seen[0]:.3f}s")
            if stable_since is not None:
                print(
                    f"Stable target ({STABLE_POLL_COUNT} consecutive polls): "
                    f"poll={stable_since[1]}, elapsed={stable_since[0]:.3f}s"
                )

            assert first_seen is not None, "Manual stage 2 was not returned within 30 seconds"
            assert stable_since is not None, (
                "Manual stage 2 was not stable for three consecutive read-only polls"
            )
        finally:
            if write_attempted:
                await _restore_initial_state(helios)
