# Tasks

## 1. Abhängigkeiten und Dateien entfernen

- [ ] 1.1 `pyproject.toml`: `homeassistant>=2024.3.3` aus der dev-Group entfernen,
      dann `uv sync` — verify: `uv sync` läuft durch, `uv.lock` ohne
      `homeassistant`-Eintrag als Paket-Root-Dep
- [ ] 1.2 `pyrightconfig.json` löschen — verify: `git ls-files | grep pyright` leer
- [ ] 1.3 `typings/` löschen (leerer Ordner) — verify: `test ! -d typings`

## 2. TODO.md

- [ ] 2.1 Checkbox #4 (Brand-Art) abhaken — verify: `git diff TODO.md` zeigt genau
      diese eine Änderung

## 3. Verifikation

- [ ] 3.1 `just check` komplett grün — verify: ruff + mypy + alle Tests unverändert
- [ ] 3.2 Referenz-Sweep — verify: `grep -ri pyright .` (ohne `.venv`/Caches) leer;
      `grep -n "homeassistant>=" pyproject.toml` leer; `test ! -d typings`
- [ ] 3.3 Safety-Audit — verify: `git diff` enthält keine `v00xxx=`-POST-Bodies (Diff
      besteht erwartungsgemäß nur aus `pyproject.toml`, `uv.lock`, gelöschten Dateien,
      `TODO.md`)