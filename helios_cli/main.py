#!/usr/bin/env python3
"""CLI entry point for helios-kwl-ec300.

Provides status monitoring and narrowly limited operating controls for Helios
KWL EC 300W R ventilation units.
"""

import argparse
import asyncio
import sys

from custom_components.helios_kwl_ec300._core import (
    DEFAULT_HOST,
    DEFAULT_PASSWORD,
    HeliosError,
    Info,
    PartyModeError,
)
from custom_components.helios_kwl_ec300._core.models import HeliosStatus


def print_status(status: HeliosStatus) -> None:
    """Print human-readable status report.

    Args:
        status: HeliosStatus model from the library
    """
    sep = "─" * 52

    print()
    print("╔══════════════════════════════════════════════════╗")
    print("║        Helios KWL — Live Status Report           ║")
    print("╚══════════════════════════════════════════════════╝")

    # ── Temperatures ────────────────────────────────────
    print("\n  🌡  TEMPERATURES")
    print(f"  {sep}")

    # Core temperatures
    temps = status.temperatures
    for temp in [temps.outdoor, temps.supply, temps.exhaust, temps.extract]:
        if temp.value_celsius is not None:
            val_str = f"{temp.value_celsius:.1f} °C"
        else:
            val_str = "— (not connected)"
        print(f"  {temp.label:40s}  {val_str}")

    # Optional sensors — only show if connected
    optional = []
    if temps.duct_outdoor and temps.duct_outdoor.value_celsius is not None:
        optional.append(temps.duct_outdoor)
    if temps.duct_supply and temps.duct_supply.value_celsius is not None:
        optional.append(temps.duct_supply)
    if temps.return_hw and temps.return_hw.value_celsius is not None:
        optional.append(temps.return_hw)

    if optional:
        print("\n  Optional sensors:")
        for temp in optional:
            val_str = f"{temp.value_celsius:.1f} °C" if temp.value_celsius is not None else "—"
            print(f"  {temp.label:40s}  {val_str}")

    # ── Fan Speed ────────────────────────────────────────
    print("\n  💨  FAN SPEED")
    print(f"  {sep}")

    fan = status.fan_speed
    stage_str = f"Stage {fan.stage}" if fan.stage is not None else "Unknown"
    pct_str = f"{fan.stage_percent:.0f} %" if fan.stage_percent is not None else "—"
    rps_str = f"{fan.rpm_supply} RPM" if fan.rpm_supply is not None else "—"
    rpe_str = f"{fan.rpm_extract} RPM" if fan.rpm_extract is not None else "—"

    print(f"  {'Fan stage':40s}  {stage_str}  ({pct_str})")
    print(f"  {'':40s}  {fan.stage_label}")
    print(f"  {'Supply fan RPM  (Drehzahl Zuluft)':40s}  {rps_str}")
    print(f"  {'Extract fan RPM (Drehzahl Abluft)':40s}  {rpe_str}")

    # ── Operation Mode ───────────────────────────────────
    print("\n  ⚙️   OPERATION MODE")
    print(f"  {sep}")
    print(f"  {'Effective mode':40s}  {status.operation_mode.effective}")

    print("\n  Sensor-based auto control:")
    mode = status.operation_mode
    print(f"  {'Humidity control (Feuchtesteuerung)':40s}  {mode.humidity_control}")
    print(f"  {'CO2 control':40s}  {mode.co2_control}")
    print(f"  {'VOC control':40s}  {mode.voc_control}")

    print()


async def cmd_status(args: argparse.Namespace) -> int:
    """Handle status command.

    Args:
        args: Parsed command-line arguments

    Returns:
        Exit code (0 = success, 1 = error)
    """
    print(f"Fetching data from {args.host} …", file=sys.stderr)

    async with Info(args.host, password=args.password) as helios:
        status = await helios.get_status()

        if args.json:
            # Use built-in JSON export from model
            print(status.to_json())
        else:
            # Human-readable output
            print_status(status)

    return 0


async def cmd_fan_stage(args: argparse.Namespace) -> int:
    """Send a manual fan-stage request without claiming hardware verification."""
    print(f"Sending fan stage {args.fan_stage} request to {args.host} …", file=sys.stderr)

    async with Info(args.host, password=args.password) as helios:
        await helios.set_fan_stage(args.fan_stage)

    print(
        "✓ Fan stage request sent with manual mode",
        file=sys.stderr,
    )
    return 0


async def cmd_automatic(args: argparse.Namespace) -> int:
    """Send an automatic-mode request without claiming hardware verification."""
    enabled = args.automatic_state == "on"
    state = "on" if enabled else "off"
    print(f"Sending automatic mode '{state}' request to {args.host} …", file=sys.stderr)

    async with Info(args.host, password=args.password) as helios:
        await helios.set_automatic_mode(enabled)

    print("✓ Automatic mode request sent", file=sys.stderr)
    return 0


async def cmd_party_start(args: argparse.Namespace) -> int:
    """Handle party mode start command.

    Args:
        args: Parsed command-line arguments

    Returns:
        Exit code (0 = success, 1 = error)
    """
    print(
        f"Activating party mode on {args.host} "
        f"(duration: {args.duration} min, fan stage: {args.fan_stage}) …",
        file=sys.stderr,
    )

    async with Info(args.host, password=args.password) as helios:
        await helios.set_party_mode(
            duration_minutes=args.duration,
            fan_stage=args.fan_stage,
        )

    print("✓ Party mode activated", file=sys.stderr)
    return 0


async def cmd_party_stop(args: argparse.Namespace) -> int:
    """Handle party mode stop command.

    Args:
        args: Parsed command-line arguments

    Returns:
        Exit code (0 = success, 1 = error)
    """
    print(f"Deactivating party mode on {args.host} …", file=sys.stderr)

    async with Info(args.host, password=args.password) as helios:
        await helios.stop_party_mode()

    print("✓ Party mode deactivated", file=sys.stderr)
    return 0


async def async_main(args: argparse.Namespace) -> int:
    """Async main function - routes to appropriate command handler.

    Args:
        args: Parsed command-line arguments

    Returns:
        Exit code (0 = success, 1 = error)
    """
    try:
        # Default to status if no command specified (backwards compatibility)
        if args.command is None:
            args.command = "status"
            args.json = False

        # Route to appropriate command handler
        if args.command == "status":
            return await cmd_status(args)
        elif args.command == "fan-stage":
            return await cmd_fan_stage(args)
        elif args.command == "automatic":
            return await cmd_automatic(args)
        elif args.command == "party":
            if args.party_action == "start":
                return await cmd_party_start(args)
            elif args.party_action == "stop":
                return await cmd_party_stop(args)

        return 1

    except PartyModeError as e:
        print(f"\nParty mode error: {e}", file=sys.stderr)
        return 1
    except HeliosError as e:
        print(f"\nError: {e}", file=sys.stderr)
        return 1
    except KeyboardInterrupt:
        print("\nInterrupted", file=sys.stderr)
        return 130


def main() -> None:
    """CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Monitor and control Helios KWL ventilation units.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s                                  # Show status (default)
  %(prog)s status --json                    # JSON output for scripting
  %(prog)s --password 'secret' status       # Authenticate with a custom password
  %(prog)s fan-stage 2                      # Request manual fan stage 2
  %(prog)s automatic on                     # Request automatic mode
  %(prog)s party start --duration 120       # Activate party mode for 120 min
  %(prog)s party stop                       # Deactivate party mode

Safety:
  Device writes are limited to party mode, fan stages 1-4 with manual mode,
  and automatic mode. Device configuration always remains read-only.
        """,
    )
    parser.add_argument(
        "--host",
        default=DEFAULT_HOST,
        metavar="HOSTNAME",
        help=f"Hostname or IP of the Helios unit (default: {DEFAULT_HOST})",
    )
    parser.add_argument(
        "--password",
        default=DEFAULT_PASSWORD,
        metavar="PASSWORD",
        help=f"Device web-interface password (default: {DEFAULT_PASSWORD})",
    )
    parser.add_argument(
        "--version",
        action="version",
        version="%(prog)s 0.3.0 (helios-kwl-ec300)",
    )

    # Subcommands
    subparsers = parser.add_subparsers(dest="command", help="Commands")

    # Status subcommand (default)
    status_parser = subparsers.add_parser(
        "status",
        help="Show current status (default)",
    )
    status_parser.add_argument(
        "--json",
        action="store_true",
        help="Output results as JSON instead of human-readable text",
    )

    # Normal operating controls
    fan_stage_parser = subparsers.add_parser(
        "fan-stage",
        help="Request manual fan stage 1-4",
    )
    fan_stage_parser.add_argument(
        "fan_stage",
        type=int,
        choices=(1, 2, 3, 4),
        metavar="STAGE",
        help="Fan stage 1-4 (also requests manual mode)",
    )

    automatic_parser = subparsers.add_parser(
        "automatic",
        help="Request base automatic mode on or off",
    )
    automatic_parser.add_argument(
        "automatic_state",
        choices=("on", "off"),
        metavar="STATE",
        help="Use 'on' for automatic or 'off' for manual mode",
    )

    # Party mode subcommand
    party_parser = subparsers.add_parser(
        "party",
        help="Control party mode (high ventilation)",
    )
    party_subparsers = party_parser.add_subparsers(
        dest="party_action",
        required=True,
        help="Party mode actions",
    )

    # Party start
    start_parser = party_subparsers.add_parser(
        "start",
        help="Activate party mode",
    )
    start_parser.add_argument(
        "--duration",
        type=int,
        default=90,
        metavar="MINUTES",
        help="Duration in minutes (5-180, default: 90)",
    )
    start_parser.add_argument(
        "--fan-stage",
        type=int,
        default=3,
        metavar="STAGE",
        help="Fan stage 1-4 (default: 3)",
    )

    # Party stop
    party_subparsers.add_parser(
        "stop",
        help="Deactivate party mode",
    )

    args = parser.parse_args()

    # Run async event loop
    try:
        exit_code = asyncio.run(async_main(args))
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\nInterrupted", file=sys.stderr)
        sys.exit(130)


if __name__ == "__main__":
    main()
