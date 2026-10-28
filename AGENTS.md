# AGENTS.md

Monitoring and limited operating-control tool for Helios KWL EC 300W R ventilation units: an async Python library, a CLI, and a Home Assistant custom integration. The device speaks a non-standard HTTP/1.0 dialect, so `openspec/specs/device-protocol/spec.md` governs all device traffic.

## Safety Boundaries (non-negotiable)

Device configuration is always read-only. The only permitted writes — every change must preserve this boundary:

- **Login**: POST `v00402=!helios!` to `/info.htm` (IP-based session, no cookies)
- **Normal operating controls**: base automatic mode on/off and normal fan stage 1-4 with manual mode via `/info.htm`
- **Start party mode**: POST to `/party.htm` with `v00092=<stage>&v00091=<duration>&v00093=0&v00094=1` (stage 1-4, duration 5-180 min)
- **Stop party mode**: POST to `/party.htm` with `v00094=0`

Everything else is read-only: request bodies carry only the parameters shown above (status polling POSTs data-retrieval bodies like `xml=/data/werte8.xml`, no `v00xxx=` pairs), and configuration pages (`/ruhe.htm`, `/urlaub.htm`, `/syst.htm`, anything outside the allowlist) never receive writes. The HA fan entity writes only party start/stop; only the fan-stage Select and automatic-mode Switch write normal operating controls.

Exact bodies and behavior live in `openspec/specs/ventilation-control/spec.md` (normal controls) and `openspec/specs/party-mode-control/spec.md` (party). After writing code, audit the diff: grep for `v00xxx=` POST bodies — every hit must be one of the allowed writes above.

## Layout

- `custom_components/helios_kwl_ec300/` — HA integration, deployed as this whole directory; `_core/` inside is the async device library (pydantic is its only runtime dependency — keep it that way). Import as `from custom_components.helios_kwl_ec300._core import ...`.
- `helios_cli/main.py` — CLI, installed as `helios`.
- `tests/lib`, `tests/ha` — unit and HA tests. `tests/conftest.py` installs fake `homeassistant`/`voluptuous` modules (`tests/fake_ha.py`), so tests run without an HA install — do not add a real HA dependency.
- `tests/live` — real-hardware tests, excluded from pytest and CI. The timing test writes to the device: it runs only as a final, user-started verification with `HELIOS_LIVE_TEST=1`.
- `vendor/` — git-ignored manufacturer docs + web UI dump. Never modify, commit, or regenerate it; missing on a fresh clone is expected.
- `custom_components/helios_kwl_ec300/brand/` — source brand art for a future `home-assistant/brands` PR; nothing reads it at runtime.
- `openspec/specs/` — authoritative behavior specs (`device-protocol`, `party-mode-control`, `ventilation-control`); keep implementation aligned with them.

## Device Protocol

All communication goes through the existing raw-socket transport (`_core/transport.py`) — the embedded server is non-standard HTTP/1.0 and a second transport has no place here. Wire protocol, authentication, XML retrieval, variable IDs, and mode logic: `openspec/specs/device-protocol/spec.md`. When naming new entities or fields, use the verified German labels from `vendor/helios_web_dump/data/lab8_de.xml`.

## Commands

`uv` for packaging, `just` as the task runner (`just --list` shows the recipes). `just check` (lint + fmt-check + typecheck + test) is the validation gate before finishing; CI (`validate.yml`) runs the same plus HACS and hassfest. Iterate with `just test-lib` / `just test-ha`; run local scripts with `uv run python script.py` so project packages are importable.

## HA / Release Constraints

- `manifest.json` version must always match the current git tag; keep `hacs.json` and `manifest.json` valid (hassfest: domain equals directory name).
- The HA fan entity shows percentage for dashboard visibility only — its writes are party start/stop, never device stages or percentages.
