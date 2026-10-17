# Tasks

## 1. Docstring-Fix (`_core/__init__.py`)

- [x] 1.1 Import-Beispiel im Modul-Docstring auf `from custom_components.helios_kwl_ec300._core import Info` korrigieren — verify: `uv run python -c "from custom_components.helios_kwl_ec300._core import Info; print('ok')"`
- [x] 1.2 Prüfen, dass `info.py`/`client.py` unverändert korrekt sind (keine Import-Beispiele) — verify: Sichtprüfung, keine Änderung nötig

## 2. Icon-Aufräumen

- [x] 2.1 `custom_components/helios_kwl_ec300/icon.svg` löschen — verify: `grep -rn "icon.svg" custom_components/` ist leer; `just check` grün
- [x] 2.2 TODO.md Punkt 4: Unterpunkt `icon.svg` abhaken (Austausch der `brand/`-Grafiken bleibt offen) — verify: TODO.md zeigt den Unterpunkt als erledigt

## 3. Integration Verification

- [x] 3.1 `just check` (lint + fmt-check + typecheck + Tests) komplett grün — verify: CI-identischer Lauf