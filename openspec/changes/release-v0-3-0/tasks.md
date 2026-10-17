# Tasks

## 1. Phase 0 — Branch-Merge auf `main`

- [ ] 1.1 `git checkout main && git merge --ff-only open-Spec` — verify: `git log
      --oneline -1` zeigt `0f4e9f1` auf `main`; Merge bricht bewusst ab, falls es
      keine Fast-Forward-Möglichkeit gibt
- [ ] 1.2 `git push origin main` — verify: `git status` zeigt `up to date` mit
      `origin/main`; der Validate-Workflow triggert automatisch
- [ ] 1.3 CI-Grün auf `main` abwarten (`gh run watch` bzw. `gh run list`) — verify:
      Jobs „Lint, types and tests" und „Hassfest validation" success (HACS-Job darf
      noch rot sein — Repo ist noch privat)

## 2. Phase 1 — Repo öffentlich (TODO #1)

- [ ] 2.1 `gh repo edit frommf/helios-kwl-ec300 --visibility public
      --accept-visibility-change-consequences` — verify: `gh repo view
      frommf/helios-kwl-ec300 --json isPrivate` → `false`
- [ ] 2.2 Validate-Workflow erneut laufen lassen (Push hat ihn getriggert; bei Bedarf
      `gh workflow run`) — verify: HACS-Job „success", raw-URL des `manifest.json`
      liefert HTTP 200

## 3. Phase 2 — Tag + Release (TODO #2)

- [ ] 3.1 `git tag v0.3.0 && git push origin v0.3.0` — verify: `git tag -l v0.3.0`
      existiert lokal und auf origin; Tag zeigt auf `0f4e9f1`
- [ ] 3.2 `gh release create v0.3.0 --generate-notes` — verify: `gh release view
      v0.3.0` existiert; HACS zeigt beim Custom-Repository-Add `0.3.0` statt eines
      Commit-Hashes

## 4. Aufräumen

- [ ] 4.1 `TODO.md`: Checkboxen #1 und #2 abhaken; Phase-0-Merge-Schritt als
      erledigt in Sektion 1 nachtragen — verify: `git diff TODO.md` zeigt genau diese
      Änderungen
- [ ] 4.2 `git branch -d open-Spec` (optional, nur nach 1.1–1.3) — verify: `git
      branch` zeigt `main` (und den aktiven Arbeitsbranch)

## 5. Abschluss-Verifikation

- [ ] 5.1 Gesamtzustand: `gh repo view frommf/helios-kwl-ec300 --json
      isPrivate,latestRelease` → `isPrivate: false`, `latestRelease.tagName: v0.3.0`
- [ ] 5.2 Safety-Audit: `git diff origin/main~1 origin/main` enthält nur `TODO.md`
      und keine `v00xxx=`-POST-Bodies — verify: grep im Diff ist leer