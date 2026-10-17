# Proposal

## Why

Der Codebase-Teil der Release-Readiness ist abgeschlossen (`release-readiness-docs`,
Commit `c18d210`): README entspricht dem Code, AGENTS.md ist aufgeräumt. Das eigentliche
Shipping blockiert aber an drei Stellen:

1. **Branch-Split:** Die 6 OpenSpec-/Docs-Commits liegen nur auf `open-Spec`; `main`
   (Default-Branch, = `origin/main`, keine Divergenz) kennt sie nicht. Ein Release-Tag
   auf `main` würde ohne die Fixes ausgeliefert. Diesen Merge-Schritt kennt `TODO.md`
   noch nicht — er ist erst durch die OpenSpec-Arbeit entstanden.
2. **Privates Repo:** Die HACS-Validation liest `manifest.json`/`hacs.json` über
   `raw.githubusercontent.com` und läuft deshalb aktuell auf 2/9 (404). Nutzer können
   das Repo nicht als Custom Repository hinzufügen.
3. **Kein Tag/Release:** HACS nimmt die angezeigte Version aus dem neuesten
   GitHub-Release-Tag; ohne Release zeigt es einen nackten Commit-Hash und bietet kein
   Upgrade an.

`TODO.md` ist das Vor-OpenSpec-Notizbuch und deckt dieselben Punkte ab (#1–#2), plus
Store-PR (#3) und Brand-Art (#4, erledigt `pre-release-cleanup`). Mit diesem Change
wird `TODO.md` zurückgezogen: die Ops vollzieht der Change selbst, den Store-PR rettet
er als optionalen Task, und `openspec/` ist ab jetzt die einzige Todo-Quelle.

## What Changes

- **Phase 0 (neu, fehlt in TODO.md):** `open-Spec` per Fast-Forward nach `main`
  mergen (`--ff-only`), pushen, CI-Grün auf `main` abwarten — bevor irgendetwas
  öffentlich wird
- **Phase 1 (TODO #1):** Repo auf `public` stellen (`gh repo edit … --visibility
  public`), Validate-Workflow erneut laufen lassen, bis der HACS-Job grün ist
- **Phase 2 (TODO #2):** Tag `v0.3.0` setzen und pushen, GitHub Release mit
  `--generate-notes` erstellen; Version-Konsistenz (Tag = `manifest.json` `version`
  = 0.3.0) ist bereits verifiziert
- **Phase 3 (optional, übernimmt TODO #3):** PR an `hacs/default` (Kategorie
  Integration), damit die Integration ohne Custom-Repository-URL auffindbar ist —
  bewusst überspringbar
- **Phase 4 — TODO.md-Rückzug:** `TODO.md` vollständig löschen; den Brand-Quellen-
  Hinweis (`brand/`-Ordner ist die Quelle für einen späteren `home-assistant/brands`-
  PR) als eine Zeile nach AGENTS.md migrieren; `open-Spec`-Branch nach erfolgreichem
  Merge löschen

## Capabilities

Dies ist ein reiner Ops-Change ohne Verhaltensänderung am Code. Der Change setzt
`skip_specs: true` in `.openspec.yaml` — es gibt keine spec-level Requirements, die
sich ändern, und es werden keine erfunden.

### New Capabilities

- *(keine)*

### Modified Capabilities

- *(keine)*

## Impact

- **Git/GitHub-Zustand:** `main` enthält die 6 Commits von `open-Spec`; Repo ist
  öffentlich; Tag `v0.3.0` + Release existieren; Store-PR optional gestellt
- **Repo-Content-Diff:** `TODO.md` gelöscht, `AGENTS.md` um eine Brand-Quellen-Zeile
  ergänzt — sonst kein Produktivcode verändert
- **Sicherheits-Boundary unangetastet:** keine `v00xxx=`-POST-Bodies im Diff
- **Nicht Teil dieses Changes:** PR an `home-assistant/brands` (der lokale `brand/`-
  Ordner bleibt als Quelle im Repo; der Verweis lebt künftig in AGENTS.md)
- Die Sichtbarkeits-Änderung ist der einzige Schritt mit echten Konsequenzen (Code wird
  öffentlich sichtbar) — im Apply wird sie erst nach CI-Grün auf `main` vollzogen