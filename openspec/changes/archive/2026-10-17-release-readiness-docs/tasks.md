# Tasks

## 1. README.md korrigieren

- [x] 1.1 Entity-Liste (Provided-Entities, ~Zeile 93–99) auf die realen Platforms
      (`SENSOR`, `FAN`, `NUMBER`, `SELECT` aus `const.py`) kürzen; Binary-Sensors-,
      Switch- und Buttons-Zeilen entfernen — verify: `grep -nE "Binary sensor|Switch|Buttons" README.md` leer
- [x] 1.2 Features-Zeile (~Zeile 21) entsprechend anpassen — verify: kein Entity-Typ
      mehr genannt, der nicht in `PLATFORMS` steht
- [x] 1.3 Fan-Beschreibung korrigieren: Prozentanzeige fürs Dashboard; Ein/Aus
      startet/stoppt den Party-Modus (entspricht `fan.py`) — verify: Formulierung
      deckt `async_turn_on`/`async_turn_off` ab
- [x] 1.4 Quick Start: `cd helios-cli` → `cd helios-kwl-ec300` — verify: die
      kopierbare Befehlsfolge clone+cd ist ausführbar

## 2. AGENTS.md Hygiene (writing-for-agents)

- [x] 2.1 `helios_status.py`-Pointer aus Layout löschen — verify: `grep -n helios_status AGENTS.md` leer
- [x] 2.2 Vendor-Regel konsolidieren: vollständige Regel (NEVER modify/commit/
      regenerate, fehlt auf frischem Clone) nur unter Layout; Reference behält nur
      den reinen Pointer; Pitfalls-Bullet entfällt — verify: das vendor-Konzept
      steht nur noch unter Layout, `grep -cn vendor AGENTS.md` zählt Pointer +
      eine Regelstelle
- [x] 2.3 Pitfalls kürzen auf nicht-duplizierte Regeln: Dependency-Footprint und
      `just check`-Criterion bleiben; Transport-/Auth-Wiederholungen entfallen —
      verify: keine Regel in Pitfalls, die nicht auch positiv in Device Protocol
      oder Commands steht, außer den beiden genannten
- [x] 2.4 Audit-Criterion schärfen: grep-Kriterium (`v00xxx=`-POST-Bodies im Diff
      müssen zu den drei erlaubten Writes gehören) — verify: Kriterium ist als
      ausführbares grep formuliert
- [x] 2.5 Fan-Entity-Regel präzisieren: ausschließlich Party-Start/Stop via
      `TURN_ON`/`TURN_OFF`; keine Stufen-/Prozent-Schreibmethoden — verify:
      Formulierung deckt `fan.py` ab und hält die Safety-Grenze

## 3. Integration Verification

- [x] 3.1 `just check` komplett grün — verify: CI-identischer Lauf
- [x] 3.2 `TODO.md` #1–#3 unverändert (GitHub-Ops bleiben manuell) — verify: `git diff TODO.md` zeigt keine Änderungen an diesen Punkten