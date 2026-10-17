# Proposal

## Why

Das Release v0.3.0 steht an, aber die Dokumentation widerspricht dem Code an zwei
Stellen: Die README verspricht Entities (Binary Sensors, Switch, Buttons), die die
Integration nicht registriert, und der Quick-Start-`cd`-Befehl bricht beim ersten
Kopieren. Zusätzlich trägt `AGENTS.md` Sediment aus dem writing-for-agents-Audit:
einen toten Pointer, drei duplizierte Regeln, eine verstreute Ko-Lokation, einen
schwammigen Audit-Criterion und eine ungenaue Fan-Entity-Formulierung.

Die GitHub-Ops (Repo public stellen, Tag v0.3.0, Release) sind bereits präzise in
`TODO.md` #1–#2 dokumentiert und bleiben manuelle Schritte — dieser Change macht den
Codebase-Teil release-fähig.

## What Changes

- `README.md`: Entity-Abschnitt (Features-Zeile und Provided-Entities-Liste) an die
  real registrierten Platforms anpassen (`SENSOR`, `FAN`, `NUMBER`, `SELECT` laut
  `const.py`); Fan-Entity korrekt beschreiben (Prozentanzeige; Ein/Aus startet/stoppt
  den Party-Modus)
- `README.md`: Quick Start auf den tatsächlichen Clone-Ordnernamen fixen
  (`cd helios-kwl-ec300`)
- `AGENTS.md`: `helios_status.py`-Pointer löschen (Datei existiert nicht mehr)
- `AGENTS.md`: Vendor-Regel als Single Source of Truth unter Layout konsolidieren;
  Pitfalls auf Regeln kürzen, die nicht schon positiv woanders stehen; `just check`
  nur noch einmal als Criterion; Audit-Criterion als prüfbares grep-Kriterium
  schärfen; Fan-Entity-Regel präzisieren (Party-Start/Stop erlaubt, keine
  Stufen-/Prozent-Schreibmethoden)

## Capabilities

Dies ist ein reiner Dokumentations-Change ohne Verhaltensänderung. Der Change setzt
`skip_specs: true` in `.openspec.yaml` — es gibt keine spec-level Requirements, die
sich ändern, und es werden keine erfunden.

### New Capabilities

- *(keine)*

### Modified Capabilities

- *(keine)*

## Impact

- `README.md`: sachlich korrigiert (Entities, Quick Start)
- `AGENTS.md`: Sediment entfernt, Regeln verdichtet und geschärft
- Kein Produktivcode verändert — `just check` bleibt grün
- **Nicht Teil dieses Changes** (manuell, siehe `TODO.md` #1–#4): `gh repo edit
  --visibility public`, `git tag v0.3.0`, `gh release create`, HACS-Store-PR,
  Austausch der `brand/`-Grafiken