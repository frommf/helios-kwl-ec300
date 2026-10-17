# Proposal

## Why

Das Docstring-Beispiel in der `_core`-Library lehrt einen nicht existierenden Import-Pfad
(`from helios_kwl_ec300 import Info`) — der erste Copy-Paste-Versuch jedes neuen Nutzers
schlägt fehl. Zusätzlich liegt eine ungenutzte `icon.svg` im Integrationsverzeichnis, in dem
HACS/HA Icons ausschließlich aus `brand/` lesen: toter Ballast im deployten Paket.

## What Changes

- Import-Beispiel in `_core/__init__.py` auf den realen Pfad korrigieren
  (`from custom_components.helios_kwl_ec300._core import Info`)
- Ungenutzte `custom_components/helios_kwl_ec300/icon.svg` löschen
- Entsprechenden Punkt in `TODO.md` (Nr. 4) abhaken

## Capabilities

Dies ist ein reiner Dokumentations-/Aufräum-Change ohne Verhaltensänderung.
Der Change setzt `skip_specs: true` in `.openspec.yaml` — es gibt keine
spec-level Requirements, die sich ändern, und es werden keine erfunden.

### New Capabilities

- *(keine)*

### Modified Capabilities

- *(keine)*

## Impact

- `custom_components/helios_kwl_ec300/_core/__init__.py`: Docstring-Beispiel korrigiert
- `custom_components/helios_kwl_ec300/icon.svg`: gelöscht
- `TODO.md`: Punkt 4 abgehakt
- Kein Verhaltenscode verändert — `just check` bleibt unverändert grün