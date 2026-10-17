# Tasks

## 1. Phase 0 — Branch-Merge auf `main`

- [x] 1.1 `git checkout main && git merge --ff-only open-Spec` — verify: Merge ist
      Fast-Forward und `git rev-parse main` == `git rev-parse open-Spec`; Merge
      bricht bewusst ab, falls es keine Fast-Forward-Möglichkeit gibt
- [x] 1.2 `git push origin main` — verify: `git status` zeigt `up to date` mit
      `origin/main`; der Validate-Workflow triggert automatisch
- [x] 1.3 CI-Grün auf `main` abwarten (`gh run watch` bzw. `gh run list`) — verify:
      Jobs „Lint, types and tests" und „Hassfest validation" success (HACS-Job darf
      noch rot sein — Repo ist noch privat)

## 2. Phase 1 — Repo öffentlich (ehem. TODO #1)

- [x] 2.1 `gh repo edit frommf/helios-kwl-ec300 --visibility public
      --accept-visibility-change-consequences` — verify: `gh repo view
      frommf/helios-kwl-ec300 --json isPrivate` → `false`
- [x] 2.2 Validate-Workflow erneut laufen lassen (Push hat ihn getriggert; bei Bedarf
      `gh workflow run`) — verify: HACS-Job „success", raw-URL des `manifest.json`
      liefert HTTP 200

## 3. Phase 2 — Tag + Release (ehem. TODO #2)

- [ ] 3.1 `git tag v0.3.0 && git push origin v0.3.0` — verify: `git tag -l v0.3.0`
      existiert lokal und auf origin; Tag zeigt auf den HEAD von `main`
- [ ] 3.2 `gh release create v0.3.0 --generate-notes` — verify: `gh release view
      v0.3.0` existiert; HACS zeigt beim Custom-Repository-Add `0.3.0` statt eines
      Commit-Hashes

## 4. Phase 3 (optional) — HACS-Store-PR (ehem. TODO #3)

- [ ] 4.1 PR an `hacs/default` stellen (Fork + Branch, Eintrag in den Integrations-
      Daten gemäß Contributing-Guide des Stores; Kategorie Integration, Repo
      `frommf/helios-kwl-ec300`) — verify: PR-Nummer notiert — **oder bewusst
      übersprungen** (Decision 5: Custom-Repository-Installation funktioniert ab
      Phase 1 vollständig; Skip ist ein gültiger Abschluss dieses Tasks)

## 5. Aufräumen

- [ ] 5.1 `TODO.md` löschen; Brand-Quellen-Hinweis nach AGENTS.md (Layout) migrieren:
      „`custom_components/helios_kwl_ec300/brand/` — source brand art for a future
      `home-assistant/brands` PR; nothing reads it at runtime" — verify:
      `git ls-files | grep TODO.md` leer; `grep -n "brands PR" AGENTS.md` zeigt die
      Zeile
- [ ] 5.2 `git branch -d open-Spec` (nur nach 1.1–1.3) — verify: `git branch` zeigt
      `main` (und den aktiven Arbeitsbranch)

## 6. Abschluss-Verifikation

- [ ] 6.1 Gesamtzustand: `gh repo view frommf/helios-kwl-ec300 --json
      isPrivate,latestRelease` → `isPrivate: false`, `latestRelease.tagName: v0.3.0`
- [ ] 6.2 Safety-Audit — verify: Diff gegenüber `origin/main` besteht nur aus
      TODO.md-Löschung + AGENTS.md-Zeile und enthält keine `v00xxx=`-POST-Bodies
      (grep im Diff ist leer)