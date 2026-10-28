# Proposal

## Why

Die Anlage kann derzeit über das Produkt nur im Partybetrieb gezielt gesteuert werden;
die normale Lüfterstufe und der Automatikbetrieb sind ausschließlich lesbar. Die neue,
streng begrenzte Steuerung über `info.htm` soll genau diese beiden Betriebseinstellungen
verfügbar machen, ohne die bisher verbotene Gerätekonfiguration anzutasten.

## What Changes

- Die Python-Bibliothek erhält validierte Operationen für die normale Lüfterstufe 1–4
  und das Ein-/Ausschalten des Automatikbetriebs über `/info.htm`.
- Das Einstellen einer Lüfterstufe schaltet den Automatikbetrieb in demselben
  Schreibvorgang aus, damit die gewählte Stufe wirksam werden kann.
- Die CLI erhält Befehle für beide Operationen. Home Assistant erhält eine
  Lüfterstufen-Select-Entität und eine Automatikbetrieb-Switch-Entität; die bisherige
  Fan-Entität und die Partybetrieb-Steuerung bleiben unverändert.
- Für die neuen Schreibvorgänge werden ausschließlich `v00101` und `v00102` an
  `/info.htm` gesendet. Alle Konfigurationsseiten und -parameter sowie jede andere
  Geräteeinstellung bleiben zu jedem Zeitpunkt schreibgeschützt.
- Nach Schreibvorgängen nutzt Home Assistant zunächst das bestehende Verhalten aus
  sofortiger Aktualisierung und regelmäßigem Polling. Eine zusätzliche Wartezeit wird
  nicht vorab festgelegt, sondern erst nach einem abschließenden Live-Mess-Test an der
  realen Anlage entschieden.
- Dokumentation und Sicherheitsregeln werden präzise auf die neue Ausnahme erweitert.

## Capabilities

### New Capabilities

- `ventilation-control`: Steuerung der normalen Lüfterstufe und des
  Basis-Automatikbetriebs mit strikt begrenzten Schreibzugriffen, konsistenten
  Produktoberflächen und sicherer Zustandsaktualisierung.

### Modified Capabilities

- *(keine vorhandenen Capabilities)*

## Impact

- **Bibliothek:** `_core/client.py`, `_core/info.py`, Zustandsmodelle/Parser und
  Konstanten für die beiden erlaubten Betriebsparameter.
- **CLI:** neue Steuerbefehle und zugehörige Ausgaben/Fehlerbehandlung in
  `helios_cli/main.py`.
- **Home Assistant:** Coordinator-Schnittstelle, neue Select-/Switch-Entitäten,
  Plattformregistrierung und Test-Stubs.
- **Tests:** vollständig gemockte Unit-/Integrationstests; ein separater, explizit
  ausgelöster Live-Abschlusstest misst die tatsächliche Übernahmedauer.
- **Dokumentation:** `SPECS.md`, `AGENTS.md` und `README.md` müssen die neue,
  eingeschränkte Schreibausnahme konsistent beschreiben.
- **Abhängigkeiten:** keine neuen Laufzeitabhängigkeiten vorgesehen.
- **Geräte:** keine Schreibzugriffe während der normalen Entwicklung und CI; reale
  Schreibtests erfolgen ausschließlich als abschließende, bewusst gestartete Messung.
