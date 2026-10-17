# Proposal

## Why

Der Audit vor dem Release (`release-v0-3-0` ist geplant, aber noch nicht angewendet)
hat drei Überbleibsel gefunden, die seit dem Initial-Commit nie hinterfragt wurden:

1. **`homeassistant>=2024.3.3` als Dev-Dep** — installiert (~100 MB), aber funktionslos:
   Die HA-Tests stubben `homeassistant` vollständig über `tests/ha/conftest.py`
   (Fake-Module in `sys.modules`), und mypy läuft nur auf `_core` + `helios_cli` —
   beide importieren kein HA. Die Entfernung passt zur AGENTS.md-Regel („do **not**
   add a real HA dependency") und beschleunigt `uv sync` deutlich.
2. **`pyrightconfig.json`** — getrackt, aber kein Tooling nutzt Pyright (justfile und
   CI typechecken mit mypy). Zusätzlich widerspricht die Datei der Realität
   (`pythonVersion 3.11` vs. mypy/`.python-version` = 3.13).
3. **`typings/`** — leerer Ordner, existiert ausschließlich als `stubPath` des
   Pyright-Configs.

Außerdem ist TODO #4 (Brand-Art) faktisch erledigt: `brand/icon.png` (256×256) und
`brand/logo.png` (512×128) sind fertiges Artwork mit exakt den Home-Assistant-Brands-
Dimensionen — die Checkbox kann abgehakt werden.

## What Changes

- `pyproject.toml`: `homeassistant>=2024.3.3` aus der dev-Group entfernen;
  `uv.lock` regenerieren
- `pyrightconfig.json` löschen (mypy-only Tooling)
- `typings/` löschen (leer, nur Pyright-`stubPath`)
- `TODO.md`: Checkbox #4 abhaken
- Nichts davon ist Verhaltenscode — `just check` muss danach unverändert grün sein

## Capabilities

Reiner Cleanup ohne Verhaltensänderung. Der Change setzt `skip_specs: true` in
`.openspec.yaml` — es gibt keine spec-level Requirements, die sich ändern, und es
werden keine erfunden.

### New Capabilities

- *(keine)*

### Modified Capabilities

- *(keine)*

## Impact

- `pyproject.toml` (dev-Group) + `uv.lock`: HA-Dep entfernt
- `pyrightconfig.json`, `typings/`: gelöscht
- `TODO.md`: #4 abgehakt
- Kein Produktivcode verändert — Tests stubben HA weiter, mypy-Scope unverändert
- **Bewusst behalten** (Audit-Entscheidung): `.opencode/`, `openspec/`, `AGENTS.md`,
  `TODO.md` bleiben im Repo und werden mit Phase 1 von `release-v0-3-0` öffentlich —
  dokumentierter Prozess, kein Cleanup-Gegenstand
- **Nicht Teil dieses Changes:** HACS-Store-PR (`TODO.md` #3), PR an
  `home-assistant/brands` (der lokale `brand/`-Ordner bleibt als Quelle im Repo)