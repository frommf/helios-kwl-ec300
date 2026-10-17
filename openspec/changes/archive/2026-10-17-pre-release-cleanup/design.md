# Design

## Context

- `homeassistant>=2024.3.3` steht seit dem Initial-Commit (`a91c223`) in der dev-Group
  und wurde nie hinterfragt. Realität heute: `tests/ha/conftest.py` installiert
  Fake-Module (`homeassistant`, `homeassistant.const`, `…core`, `…update_coordinator`
  usw.) in `sys.modules`, bevor irgendwelcher Code HA importiert; Tests referenzieren
  HA ausschließlich über diese Stubs. mypy (justfile `typecheck` und CI) läuft nur auf
  `custom_components/helios_kwl_ec300/_core` + `helios_cli` — keiner der beiden
  importiert HA. Der mypy-Override `ignore_missing_imports` für `homeassistant.*`
  existiert unabhängig davon und bleibt als Guard.
- `pyrightconfig.json` ist seit dem Initial-Commit getrackt; kein justfile-Recipe, kein
  CI-Step, kein Doc referenziert Pyright. Der Nutzer bestätigt: Pyright wird nicht im
  Editor genutzt → mypy ist der einzige Typechecker.
- `typings/` ist leer und wird nur als `stubPath` vom Pyright-Config referenziert.
- `brand/icon.png` (256×256) und `brand/logo.png` (512×128) sind fertiges Artwork in
  den exakten Home-Assistant-Brands-Dimensionen. Der Ordner hat keine Runtime-Funktion
  (HACS und HA lesen ihn nicht) und bleibt als Quelle für einen späteren
  `home-assistant/brands`-PR im Repo.

## Goals / Non-Goals

**Goals:**

- Dev-Group ohne `homeassistant` — schnelleres `uv sync`, konsistent mit AGENTS.md
- Ein einziger Typechecker (mypy) — Pyright-Reste komplett entfernt
- `TODO.md` #4 abgehakt, Brand-Ordner bleibt als Art-Quelle dokumentiert
- `just check` nach dem Cleanup unverändert grün

**Non-Goals:**

- Keine Änderung an Test-Stub-Mechanismus oder mypy-Overrides
- Kein Entfernen von `.opencode/` / `openspec/` / `AGENTS.md` / `TODO.md` (Audit-
  Entscheidung: bleiben und werden öffentlich)
- Kein Umbau des `brand/`-Ordners, kein Brands-PR
- Keine Versionsänderungen, kein Produktivcode

## Decisions

### Decision 1: HA-Dev-Dep entfernen, mypy-Override behalten

Die echte HA-Installation dient keinem der drei Verbraucher (Tests stubben, mypy-Scope
ohne HA, CI identisch). Entfernung ändert kein Prüfverhalten — der Override
`ignore_missing_imports` für `homeassistant.*` bleibt als Guard für den Fall, dass
irgendwann HA-Module in den mypy-Scope rücken. `uv.lock` wird durch `uv sync`
regeneriert.

### Decision 2: Mypy-only — Pyright-Config und stubPath löschen

Zwei Typechecker mit widersprechenden Python-Versionen (3.11 vs. 3.13) sind ein
zukünftiger Bug-Lieferant. Mit der Nutzer-Entscheidung (Pyright wird nicht genutzt)
wird die Datei gelöscht statt angeglichen; `typings/` fällt mit dem `stubPath` mit weg.

### Decision 3: TODO #4 als erledigt abhaken, Artwork im Repo lassen

Die Grafiken erfüllen den Task (echtes Brand-Art, korrekte Dimensions). Der lokale
`brand/`-Ordner bleibt — er ist die dokumentierte Quelle für den späteren
`home-assistant/brands`-PR und wird vom `deploy-ha`-Recipe mitkopiert (harmlos).

### Decision 4: Verify über greps statt nur Tests

`just check` allein beweist nicht, dass keine Referenz übrig ist. Verifiziert wird
zusätzlich: kein `pyright`-Treffer mehr im Repo, kein `homeassistant>`-Eintrag in
`pyproject.toml`/`uv.lock`-Deps, `typings/` existiert nicht. Safety-Audit wie gehabt:
keine `v00xxx=`-Bodies im Diff.

## Open Questions

- *(keine)*