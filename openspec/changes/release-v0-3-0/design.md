# Design

## Context

- `main` = `origin/main` (`e75fc07`), keine Divergenz; `open-Spec` ist 6 Commits ahead
  (OpenSpec-Setup, `cleanup-docstring-icon` `fb87a8a`, `release-readiness-docs`
  `c18d210`, zwei Skill-Aufräum-Commits) → Fast-Forward-Merge ist verlustfrei möglich.
- Repo `frommf/helios-kwl-ec300` ist privat; CI-Job „HACS validation" scheitert mit
  „is private, the HACS action can only validate public repositories".
- Lokal existiert kein Tag; GitHub hat kein Release (`latestRelease: null`).
- Version-Konsistenz 0.3.0 ist über pyproject.toml, `manifest.json`,
  `_core/__init__.py` und CLI `--version` bereits verifiziert; `hacs.json` ist valide
  (`name`, `homeassistant: 2024.3.0`).
- Validate-Workflow (`validate.yml`) läuft identisch zu `just check` plus HACS und
  hassfest; er triggert auf Push nach `main`.
- `TODO.md` #1–#2 dokumentieren Repo-public und Tag/Release bereits präzise — es fehlt
  nur der Merge-Schritt (Phase 0), der durch die OpenSpec-Arbeit nötig wurde.

## Goals / Non-Goals

**Goals:**

- `main` enthält alle 6 `open-Spec`-Commits, CI grün — bevor das Repo öffentlich wird
- HACS-Validation 9/9 (raw-URLs erreichbar)
- Tag `v0.3.0` + GitHub Release existieren; HACS zeigt die Version an
- `TODO.md` spiegelt den neuen Zustand (Checkboxen, Phase-0-Nachtrag)

**Non-Goals:**

- Kein Verhaltenscode, keine Versionsbumps (alles ist schon 0.3.0)
- Kein HACS-Store-PR (`TODO.md` #3 — bleibt manuell, kann nach Phase 1–2 jederzeit
  folgen)
- Kein Austausch der `brand/`-Grafiken (`TODO.md` #4)
- Keine Änderung an Workflow-Dateien (`.github/`)

## Decisions

### Decision 1: Reihenfolge merge → CI-Grün → public → tag/release

Die Sichtbarkeits-Änderung ist der einzige Schritt mit echten Konsequenzen. Sie wird
erst vollzogen, wenn `main` die komplette Arbeit trägt und der Validate-Lauf (Lint/
Tests/Hassfest) grün ist. So wird nie ein unfertiger Stand öffentlich sichtbar, und der
HACS-Job hat beim ersten grünen Lauf bereits den finalen Content.

### Decision 2: Fast-Forward-Merge lokal statt PR

Solo-Repo, keine Divergenz (`main` hat 0 Commits, die `open-Spec` nicht hat): ein PR
würde nur Ceremony ohne Review-Gewinn erzeugen. `git merge --ff-only open-Spec` ist
deterministisch — schlägt es fehl, existiert unerwartet eine Divergenz und der Merge
bricht bewusst ab statt zu verschmutzen.

### Decision 3: Tag und Release als letzte Content-Abhängigkeit

HACS liest die Version aus dem neuesten Release-Tag. Der Tag wird erst gesetzt, wenn
Repo-public und HACS-Validation grün sind — sonst zeigt HACS zwar ein Release, aber
die Validierung scheitert weiter und Nutzer könnten eine gebrochene First-Experience
sehen.

### Decision 4: `TODO.md` ist Teil des Diffs, das Rest ist Prozedur

Der einzige Repo-Content-Diff dieses Changes ist `TODO.md` (Checkboxen #1/#2, Phase-0-
Nachtrag). Alle anderen Schritte sind Git/GitHub-Zustandsänderungen, die in den
Tasks als explizite Kommandos mit Verify-Schritten stehen — kein Skript im Repo, das
später veralten würde (prozedurales Wissen gehört in die archivierte Change-Historie,
nicht in wartbare Dateien).

### Decision 5: Sicherheits-Audit als trivialer Verify

Der Safety-Criterion aus AGENTS.md (grep nach `v00xxx=`-POST-Bodies im Diff) wird als
Abschluss-Verify geführt. Der Diff besteht erwartungsgemäß nur aus `TODO.md` — der
grep muss leer sein.

## Open Questions

- *(keine)*