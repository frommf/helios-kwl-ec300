# AGENTS.md

Monitoring and limited operating-control tool for Helios KWL EC 300W R ventilation units: an async Python library, a CLI, and a Home Assistant custom integration. Everything talks to the device's non-standard embedded HTTP server, so the protocol quirks below are the core of the project.

**SAFETY FIRST**: device configuration is always read-only. The only permitted writes are authentication, normal fan stage 1–4 with manual mode, base automatic mode on/off, and party mode start/stop. Every change must preserve this boundary.

## Safety Boundaries (non-negotiable)

The only writable operations in the entire codebase:

- **Login**: POST `v00402=!helios!` to `/info.htm` (IP-based session, no cookies)
- **Base automatic mode**: POST only `v00101=0` (on) or `v00101=1` (off/manual) to `/info.htm`
- **Normal fan stage**: POST only `v00101=1&v00102=<stage>` to `/info.htm` (stage 1-4; always requests manual mode in the same body)
- **Start party mode**: POST to `/party.htm` with `v00092=<stage>&v00091=<duration>&v00093=0&v00094=1` (stage 1-4, duration 5-180 min)
- **Stop party mode**: POST to `/party.htm` with `v00094=0`

Everything else is read-only:

- Never use POST/PUT/PATCH/DELETE that changes state beyond the operations above. Status polling POSTs only data-retrieval bodies (`xml=/data/werte8.xml`) with no `v00xxx=` pairs.
- Never write to `/ruhe.htm`, `/urlaub.htm`, `/syst.htm`, or any configuration/state-changing endpoint outside the explicit allowlist.
- The `/info.htm` control bodies contain no hidden form fields, `v01306`, `v00103`, or other parameters. Never change quiet/holiday mode, temperature thresholds, schedules, fan configuration, or any other device config.
- The HA fan entity writes only party mode start/stop. Only the dedicated fan-stage Select and automatic-mode Switch may write the normal operating controls above.
- After writing code, audit the diff: grep for `v00xxx=` POST bodies — every hit must be one of the explicitly allowed writes above.

## Layout

- `custom_components/helios_kwl_ec300/` — HA integration; deployed as the whole directory. `_core/` inside is the device library (async, Pydantic, pydantic-only runtime dep); import it from Python/HA as `from custom_components.helios_kwl_ec300._core import ...`.
- `helios_cli/main.py` — CLI, installed as `helios` via `[project.scripts]`.
- `tests/lib` (library unit tests) and `tests/ha` (HA tests). The root `tests/conftest.py` installs fake `homeassistant`/`voluptuous` modules (`tests/fake_ha.py`) for all tests — do **not** add a real HA dependency for routine work.
- `tests/live` — explicitly activated real-hardware tests only; excluded from normal pytest collection and never run in CI. The operating-control timing test requires `HELIOS_LIVE_TEST=1` and may run only as a final, user-started verification.
- `vendor/` — git-ignored manufacturer docs + web UI dump. NEVER modify, commit, or regenerate it; it may be missing on a fresh clone.
- `custom_components/helios_kwl_ec300/brand/` — source brand art for a future `home-assistant/brands` PR; nothing reads it at runtime.
- `SPECS.md` — authoritative protocol and variable reference.

## Device Protocol (the reason this uses raw sockets)

- The embedded server is HTTP/1.0 only and non-standard; standard HTTP clients (`requests`, aiohttp) are unreliable. Use the existing raw-socket transport (`_core/transport.py`) — never add another one.
- Status XML is fetched via **POST**, not GET (e.g. body `xml=/data/werte8.xml`).
- Auth is IP-based sessions: on 403, POST `v00402=!helios!` to `/info.htm`, then retry. Keep that retry logic on all requests.
- Parse only complete socket responses — never partial reads.

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

## Key Variable IDs (used by monitors and parsers)

- Temperatures: `v00104` outdoor, `v00105` supply, `v00106` exhaust, `v00107` extract air
- Fan: `v00102` stage (1-4, 5/6 = external), `v00103` stage %, `v00348` supply RPM, `v00349` extract RPM
- Modes: `v00101` auto/manual, `v00094` party active, `v00099` quiet active, `v00601` holiday active

Use the verified German labels from `vendor/helios_web_dump/data/lab8_de.xml` when naming new entities/fields.

## Reference

- `SPECS.md` — IDs, endpoints, allowed/forbidden operations
- `vendor/helios_web_dump/` — device web UI snapshot and XML schema
- `README.md` — user-facing docs and usage

## Pitfalls

- Keep the library dependency footprint minimal (pydantic only).
- Run `just check` before finishing.