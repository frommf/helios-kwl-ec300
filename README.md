# Helios KWL EC 300 — Monitor & Limited Control

Monitoring and limited operating-control tool for **Helios KWL EC 300W R** ventilation units running **easyControls v2.7**. Provides a Python library, CLI, and Home Assistant custom integration for live status data, normal fan-stage/automatic-mode control, and party mode control through the device's built-in web interface.

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-41BDF5.svg)](https://github.com/hacs/integration)

> **Not affiliated with Helios.** This is an independent, community-maintained project. It is **not affiliated with, endorsed by, or supported by** Helios Ventilatoren GmbH in any way. "Helios" and "KWL" are trademarks of their respective owners and are referenced here only to describe device compatibility.

> **Why HTTP and not Modbus?**
> This device supports Modbus in theory, but in practice it causes the ventilation unit to crash after running for a while. The HTTP/1.0 web interface is the only reliable communication channel for easyControls v2.7 firmware.

**Safety**: Device configuration is always read-only. The only permitted state changes are normal fan stage 1–4 with manual mode, base automatic mode on/off, and party mode start/stop.

## Features

- Temperature monitoring — all air streams (outdoor, supply, exhaust, extract)
- Fan speed tracking — current stage, percentage, RPM for both fans
- Normal fan-stage control — stages 1–4; selecting a stage also requests manual mode
- Base automatic-mode control — on/off independently of effective-mode overrides
- Operation mode status — automatic, manual, party, quiet, holiday
- Safe party mode control — explicitly limited to start/stop
- Async/await with full type annotations and Pydantic models
- Home Assistant custom integration with coordinator, sensor, fan, number, select, and switch entities

## Compatibility

- **Device**: Helios KWL EC 300W R
- **Firmware**: easyControls v2.7
- **Python**: 3.11+

## Quick Start

```bash
git clone https://github.com/frommf/helios-kwl-ec300.git
cd helios-kwl-ec300
uv sync

just run               # status from default host (helios.fritz.box)
just run status --json # JSON output
just run --help
```

## Project Structure

```
helios-cli/
├── custom_components/helios_kwl_ec300/   # HA integration (deploy this dir to HA)
│   ├── _core/                            # Device library
│   │   ├── info.py        # High-level async API (Info class)
│   │   ├── client.py      # HTTP client with auth retry
│   │   ├── transport.py   # Custom async HTTP/1.0 transport (raw sockets)
│   │   ├── models.py      # Pydantic data models
│   │   ├── parsers.py     # XML parsing helpers
│   │   ├── constants.py   # Variable IDs and endpoint constants
│   │   └── exceptions.py  # Exception hierarchy
│   ├── coordinator.py, sensor.py, fan.py, ...  # HA platform files
│   └── translations/
├── helios_cli/                           # CLI (local only)
│   └── main.py
└── tests/
    ├── lib/   # Library unit tests
    └── ha/    # HA integration tests (stub-based, no HA install needed)
```

## Home Assistant Integration

### Installation via HACS (recommended)

[![Open your Home Assistant instance and open this repository inside the Home Assistant Community Store.](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=frommf&repository=helios-kwl-ec300&category=integration)

1. Make sure [HACS](https://hacs.xyz/) is installed on your Home Assistant instance
2. Go to **HACS → ⋮ (top right) → Custom repositories**
3. Add `https://github.com/frommf/helios-kwl-ec300` with category **Integration**
   (or click the badge above to open the Custom repositories dialog directly)
4. Find **"Helios KWL EC 300"** in HACS and install it
5. Restart Home Assistant
6. Add the device: **Settings → Devices & Services → Add Integration → Helios KWL EC 300** — enter host and password

New releases show up as updates in HACS automatically.

### Manual installation (alternative)

Install the integration via HACS from this GitHub repository, or copy the entire component directory to your HA instance manually:

```bash
cp -r custom_components/helios_kwl_ec300 /path/to/ha/custom_components/
```

The component is self-contained. Provided entities:
- **Sensors** — all temperatures, fan stage/percent/RPM, operation mode, party state
- **Fan** — current speed as percentage for dashboards; turning it on/off starts/stops party mode
- **Number** — default party duration (minutes)
- **Selects** — normal fan-stage control (1–4) and default party fan stage
- **Switch** — base automatic mode, derived from `v00101` even during party/quiet/holiday overrides

After an operating-control write, Home Assistant requests an immediate refresh and then continues normal polling (default: every 30 seconds). If the device still returns the previous value during its hardware transition, the displayed state remains the actual value read from the device until a later refresh reports the new one.

## CLI Usage

```bash
# Status (default host: helios.fritz.box)
just run
just run status
just run --host 192.168.1.100 status
just run --host 192.168.1.100 --password 'my-secret' status

# JSON output
just run status --json

# Normal operating controls (request submission, not hardware verification)
just run fan-stage 2        # Also requests manual mode
just run automatic on
just run automatic off

# Party mode
just run party start --duration 120 --fan-stage 4
just run party stop

# Help
just run --help
just run fan-stage --help
just run automatic --help
just run party --help
```

Successful control commands confirm that the request was sent, not that the hardware has already applied it. The CLI does not sleep or poll automatically; use `just run status` or `just run status --json` when an explicit readback is needed.

## Python Library

```python
import asyncio
from custom_components.helios_kwl_ec300._core import Info

async def main():
    async with Info("helios.fritz.box") as helios:
        status = await helios.get_status()
        print(f"Supply air: {status.temperatures.supply.value_celsius}°C")
        print(f"Fan stage: {status.fan_speed.stage}")

        snapshot = await helios.get_snapshot()
        if snapshot.identity:
            print(snapshot.identity.unique_id)

        # These calls send operating requests; they do not verify hardware timing.
        await helios.set_fan_stage(2)          # Also requests manual mode
        await helios.set_automatic_mode(True)  # Request base automatic mode

        await helios.set_party_mode(duration_minutes=120, fan_stage=4)
        await helios.stop_party_mode()

asyncio.run(main())
```

## Why Custom HTTP/1.0 Transport?

The device's embedded web server has several quirks that rule out standard HTTP libraries:

1. **HTTP/1.0 only** — HTTP/1.1 clients fail against this server
2. **POST for data retrieval** — status XML must be fetched via POST, not GET
3. **IP-based sessions** — authentication is tracked by client IP, not cookies or tokens
4. **Non-standard framing** — requires raw socket control for reliable reads

**Modbus was evaluated but causes the device to crash** after running for a while on easyControls v2.7 firmware. The HTTP interface is the only stable option.

Communication flow:
```
POST /data/werte8.xml
  → 403 Forbidden (not authenticated)
POST /info.htm  body: v00402=!helios!
  → 200 OK (IP session established)
POST /data/werte8.xml (retry)
  → 200 OK with XML payload
Parse XML → typed Pydantic models
```

## Safety Boundaries

Only these write operations are permitted:

| Endpoint | Body | Purpose |
|----------|------|---------|
| `/info.htm` | `v00402=!helios!` | Authentication |
| `/info.htm` | `v00101=0` | Request base automatic mode |
| `/info.htm` | `v00101=1` | Request base manual mode (automatic off) |
| `/info.htm` | `v00101=1&v00102=<stage>` | Request normal fan stage 1–4 with manual mode |
| `/party.htm` | `v00092=<stage>&v00091=<duration>&v00093=0&v00094=1` | Start party mode |
| `/party.htm` | `v00094=0` | Stop party mode |

The operating-control requests contain only the listed parameters—no hidden form fields or state flags. **Never** write to `/ruhe.htm`, `/urlaub.htm`, `/syst.htm`, or any configuration/state-changing endpoint beyond the explicit table above.

## Development

### Requirements

- [uv](https://docs.astral.sh/uv/) — Python package manager
- [just](https://github.com/casey/just) — task runner (recommended)

### Setup

```bash
uv sync
just check   # lint + format check + typecheck + tests
```

### Task Runner

| Recipe | Description |
|--------|-------------|
| `just sync` | Install dependencies |
| `just test` | Run all tests |
| `just test-lib` | Library tests only |
| `just test-ha` | HA integration tests only |
| `just test-cov` | Tests with coverage |
| `just lint` | Lint with ruff |
| `just fmt` | Format with ruff |
| `just typecheck` | Type-check with mypy |
| `just check` | All checks (lint + fmt + types + tests) |
| `just fix` | Auto-fix lint + format |
| `just run *args` | Run the CLI |
| `just clean` | Remove caches |

### Running Tests

```bash
just test                       # all tests
just test-lib                   # library only
just test-ha                    # HA integration only
just test -v -k "test_parsers"  # filtered
```

HA tests use lightweight in-repo stubs for `homeassistant` and `voluptuous` — no local HA installation needed.

### Opt-in live timing measurement

`tests/live/` is excluded from normal pytest collection and CI. The operating-control timing test also skips before any device connection unless `HELIOS_LIVE_TEST=1` is set explicitly. Run it only as a final, user-started hardware verification after `just check` passes:

```bash
HELIOS_LIVE_TEST=1 uv run pytest -s tests/live/test_operating_control_timing.py
```

The test first requires effective automatic mode and base stage 1, otherwise it aborts without a measurement write. It then sends exactly one measurement request for manual stage 2, records read-only polls for up to 30 seconds, and restores stage 1 plus base automatic mode in a `finally` block with read verification. Its output shows first detection, elapsed seconds, poll counts, and stability to support a separate decision about any future delayed refresh.

## Troubleshooting

**`NetworkError: Timeout`** — Check device is reachable (`ping helios.fritz.box`), try IP instead of hostname, increase timeout: `Info(host=..., timeout=30.0)`.

**`AuthenticationError`** — Default password is `!helios!`. Pass a custom one: `Info(host=..., password="your_password")`.

## Disclaimer

This project is an **independent, community-maintained** effort. It is not affiliated with, endorsed by, or supported by Helios Ventilatoren GmbH in any way. "Helios" and "KWL" are trademarks of their respective owners and are referenced here only to describe device compatibility.

The software is provided "as is", without warranty of any kind, and is used entirely at your own risk. Any vendor support for the ventilation unit itself does not extend to this software.

## License

MIT — see [LICENSE](LICENSE)
