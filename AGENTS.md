# AGENTS.md

Monitoring and limited operating-control tool for Helios KWL EC 300W R ventilation units: an async Python library, a CLI, and a Home Assistant custom integration. Everything talks to the device's non-standard embedded HTTP server, so the protocol quirks specified in `openspec/specs/device-protocol/spec.md` are the core of the project.

**SAFETY FIRST**: device configuration is always read-only. The only permitted writes are authentication, normal fan stage 1–4 with manual mode, base automatic mode on/off, and party mode start/stop. Every change must preserve this boundary.

## Safety Boundaries (non-negotiable)

The only writable operation groups in the entire codebase:

- **Login**: POST `v00402=!helios!` to `/info.htm` (IP-based session, no cookies)
- **Normal operating controls**: only base automatic mode on/off and normal fan stage 1-4 with manual mode via `/info.htm`. The exact allowlisted bodies and behavioral requirements live in `openspec/specs/ventilation-control/spec.md`; party bodies are specified in `openspec/specs/party-mode-control/spec.md`. Never add other parameters or hidden form fields.
- **Start party mode**: POST to `/party.htm` with `v00092=<stage>&v00091=<duration>&v00093=0&v00094=1` (stage 1-4, duration 5-180 min)
- **Stop party mode**: POST to `/party.htm` with `v00094=0`

Everything else is read-only:

- Never use POST/PUT/PATCH/DELETE that changes state beyond the operations above. Status polling POSTs only data-retrieval bodies (`xml=/data/werte8.xml`) with no `v00xxx=` pairs.
- Never write to `/ruhe.htm`, `/urlaub.htm`, `/syst.htm`, or any configuration/state-changing endpoint outside the explicit allowlist.
- Never change quiet/holiday mode, temperature thresholds, schedules, fan configuration, or any other device config.
- The HA fan entity writes only party mode start/stop. Only the dedicated fan-stage Select and automatic-mode Switch may write the normal operating controls above.
- After writing code, audit the diff: grep for `v00xxx=` POST bodies — every hit must be one of the explicitly allowed writes above.

## Layout

- `custom_components/helios_kwl_ec300/` — HA integration; deployed as the whole directory. `_core/` inside is the device library (async, Pydantic, pydantic-only runtime dep); import it from Python/HA as `from custom_components.helios_kwl_ec300._core import ...`.
- `helios_cli/main.py` — CLI, installed as `helios` via `[project.scripts]`.
- `tests/lib` (library unit tests) and `tests/ha` (HA tests). The root `tests/conftest.py` installs fake `homeassistant`/`voluptuous` modules (`tests/fake_ha.py`) for all tests — do **not** add a real HA dependency for routine work.
- `tests/live` — explicitly activated real-hardware tests only; excluded from normal pytest collection and never run in CI. The operating-control timing test requires `HELIOS_LIVE_TEST=1` and may run only as a final, user-started verification.
- `vendor/` — git-ignored manufacturer docs + web UI dump. NEVER modify, commit, or regenerate it; it may be missing on a fresh clone.
- `custom_components/helios_kwl_ec300/brand/` — source brand art for a future `home-assistant/brands` PR; nothing reads it at runtime.
- `openspec/specs/` — authoritative behavior specs; keep implementation aligned with them: `device-protocol` (wire protocol, auth, XML retrieval, variable IDs, mode logic, vendor rules), `party-mode-control` (party behavior and exact request bodies), `ventilation-control` (normal operating controls).

## Device Protocol (the reason this uses raw sockets)

The wire protocol, IP authentication, XML retrieval, and 403-retry behavior are specified in `openspec/specs/device-protocol/spec.md` — keep implementation and that spec aligned. The embedded server is non-standard HTTP/1.0, so all communication goes through the existing raw-socket transport (`_core/transport.py`) — never add another one.

## Commands

`uv` for packaging, `just` as the task runner. `just check` (lint + fmt-check + typecheck + test) is the full validation gate — GitHub CI (`validate.yml`) runs the same commands plus HACS and hassfest validation.

| just recipe | runs |
|---|---|
| `just sync` | `uv sync` |
| `just test-lib` / `just test-ha` | pytest on `tests/lib` / `tests/ha` |
| `just test <args>` | full pytest; filter with e.g. `just test -k test_parsers` |
| `just lint` / `just fmt` / `just fmt-check` | ruff check / format / `--check` on `custom_components/ helios_cli/ tests/` |
| `just typecheck` | mypy on `_core` + `helios_cli` |
| `just check` | lint + fmt-check + typecheck + test |
| `just run <args>` | `uv run helios <args>` (e.g. `just run status --json`) |

Iterate with the focused recipes: `just test-ha` while touching the integration, `just test-lib` for `_core/` changes. Run scripts locally with `uv run python script.py` so the project packages are importable.

## HA / Release Constraints

- `manifest.json` `version` must always match the current git tag (currently `0.4.0`); `hacs.json` and `manifest.json` must stay valid (HACS/hassfest enforce this in CI, domain must equal directory name).
- The HA fan entity shows percentage for dashboard visibility; its only writes are party mode start/stop — no methods that set stages or percentages on the device.

## Variables

The variable-ID reference (temperatures, fan, modes, party, status flags) is specified in `openspec/specs/device-protocol/spec.md`; effective-mode and party-target-stage display logic live there and in `openspec/specs/party-mode-control/spec.md`.

Use the verified German labels from `vendor/helios_web_dump/data/lab8_de.xml` when naming new entities/fields.

## Reference

- `openspec/specs/device-protocol/spec.md` — transport, auth, XML retrieval, variable IDs, allowed/forbidden operations
- `openspec/specs/party-mode-control/spec.md` — party-mode behavior and exact request bodies
- `openspec/specs/ventilation-control/spec.md` — normal operating-control behavior and scenarios
- `vendor/helios_web_dump/` — device web UI snapshot and XML schema
- `README.md` — user-facing docs and usage

## Pitfalls

- Keep the library dependency footprint minimal (pydantic only).
- Run `just check` before finishing.