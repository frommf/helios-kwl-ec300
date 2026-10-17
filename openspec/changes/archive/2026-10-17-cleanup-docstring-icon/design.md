# Design

## Context

- `_core/__init__.py` enthält im Modul-Docstring ein Import-Beispiel mit dem
  pfad `from helios_kwl_ec300 import Info`. Ein Top-Level-Modul dieses Namens
  existiert nicht; die Library lebt unter
  `custom_components/helios_kwl_ec300/_core/` (Import-Regel in AGENTS.md).
- `icon.svg` liegt im Integrationsverzeichnis, wird im Repo außerhalb von
  `TODO.md` nirgends referenziert. HACS/HA lesen Icons aus `brand/`.
- Die Klassen-Docstrings in `info.py` und `client.py` zeigen keine Import-Zeilen
  und sind konventionell korrekt — sie bleiben unverändert.

## Goals / Non-Goals

**Goals:**

- Docstring-Beispiel zeigt einen funktionsfähigen, verifizierten Import-Pfad
- Deploytes Komponenten-Paket enthält keine ungenutzten Icon-Dateien

**Non-Goals:**

- Keine Umbenennung oder Verschiebung der Library
- Keine Ersetzung der `brand/`-Grafiken (TODO.md #4, separater Punkt)
- Keine Änderung an Verhaltenscode

## Decisions

### Decision 1: Korrekter Import-Pfad laut AGENTS.md

Das Beispiel zeigt `from custom_components.helios_kwl_ec300._core import Info`.
Verifikation über `uv run python -c "from custom_components.helios_kwl_ec300._core
import Info"` — der Pfad muss ohne Nebenwirkungen importierbar sein.

### Decision 2: icon.svg löschen statt ignorieren

Löschen ist die Aussagekraft-stärkste Lösung: eine ungenutzte Datei im
deployten Paket verwirrt (HACS-validierung, Dateigröße). Fallback wäre
`.gitignore` — aber das löst das Problem im Checkout anderer nicht.

### Decision 3: TODO.md-Punkt 4 nur teilweise abhaken

Punkt 4 umfasst auch den Austausch der `brand/`-Grafiken, der hier explizit
nicht erledigt wird (Non-Goal). Der Unterpunkt zum `icon.svg` wird abgehakt,
der Rest bleibt offen — TODO.md bleibt wahrheitsgemäß.