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

Die Schritte sind in `TODO.md` #1–#2 vorbereitet; dieser Change plant und vollzieht sie
in korrekter Reihenfolge mit Verifikation.

## What Changes

- **Phase 0 (neu, fehlt in TODO.md):** `open-Spec` per Fast-Forward nach `main`
  mergen (`--ff-only`), pushen, CI-Grün auf `main` abwarten — bevor irgendetwas
  öffentlich wird
- **Phase 1 (TODO #1):** Repo auf `public` stellen (`gh repo edit … --visibility
  public`), Validate-Workflow erneut laufen lassen, bis der HACS-Job grün ist
- **Phase 2 (TODO #2):** Tag `v0.3.0` setzen und pushen, GitHub Release mit
  `--generate-notes` erstellen; Version-Konsistenz (Tag = `manifest.json` `version`
  = 0.3.0) ist bereits verifiziert
- **`TODO.md`:** Checkboxen #1/#2 abhaken, Merge-Schritt (Phase 0) als erledigt
  nachtragen
- Aufräumen: `open-Spec`-Branch nach erfolgreichem Merge löschen

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
  öffentlich; Tag `v0.3.0` + Release existieren
- **Kein Produktivcode verändert** — der einzige Repo-Content-Diff ist `TODO.md`
- **Sicherheits-Boundary unangetastet:** keine `v00xxx=`-POST-Bodies im Diff (Diff
  besteht nur aus `TODO.md`-Checkboxen)
- **Nicht Teil dieses Changes** (manuell, siehe `TODO.md` #3–#4): HACS-Store-PR
  (`hacs/default`), Austausch der `brand/`-Grafiken
- Die Sichtbarkeits-Änderung ist der einzige Schritt mit echten Konsequenzen (Code wird
  öffentlich sichtbar) — im Apply wird sie erst nach CI-Grün auf `main` vollzogen