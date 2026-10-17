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
- `TODO.md` ist das Vor-OpenSpec-Notizbuch (#1 public, #2 Tag/Release, #3 Store-PR,
  #4 Brand-Art). #1–#2 deckt dieser Change ab, #4 ist durch `pre-release-cleanup`
  erledigt — nach diesem Change existiert die Datei nicht mehr.

## Goals / Non-Goals

**Goals:**

- `main` enthält alle 6 `open-Spec`-Commits, CI grün — bevor das Repo öffentlich wird
- HACS-Validation 9/9 (raw-URLs erreichbar)
- Tag `v0.3.0` + GitHub Release existieren; HACS zeigt die Version an
- Store-PR als optionaler Task gerettet (bewusst überspringbar)
- `TODO.md` zurückgezogen — `openspec/` ist ab jetzt die einzige Todo-Quelle; der
  Brand-Quellen-Hinweis lebt weiter in AGENTS.md

**Non-Goals:**

- Kein Verhaltenscode, keine Versionsbumps (alles ist schon 0.3.0)
- Kein PR an `home-assistant/brands` (die Art-Quelle bleibt im Repo; Verweis in
  AGENTS.md)
- Keine Änderung an Workflow-Dateien (`.github/`) oder am OpenSpec-Setup

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

### Decision 4: TODO.md zurückziehen statt aktualisieren

`TODO.md` war das manuelle Notizbuch vor OpenSpec. Eine Datei mit angehakten
Checkboxen als Zustands-Doppelbuchung zu pflegen (Changes *und* TODO) erzeugt genau
das Sediment, das OpenSpec vermeidet. Der Change löscht die Datei vollständig und
rettet den einzigen ungedeckten Rest: #3 (Store-PR) wird optionaler Phase-3-Task; der
Brand-Quellen-Hinweis wandert als eine Zeile in AGENTS.md (Layout). Danach ist
`openspec/` die einzige Todo-Quelle.

### Decision 5: Store-PR optional, nicht verpflichtend

Der `hacs/default`-Eintrag ist ein Findbarkeits-Upgrade, kein Funktions-Requirement:
ab Phase 1 funktioniert die Custom-Repository-Installation vollständig. Deshalb steht
der Task explizit als überspringbar — er ist der einzige Rest der alten Todo-Liste,
weil er denselben grünen Checks wie Phase 1–2 genügt und ohne Risiko danach folgen
kann.

### Decision 6: Sicherheits-Audit als trivialer Verify

Der Safety-Criterion aus AGENTS.md (grep nach `v00xxx=`-POST-Bodies im Diff) wird als
Abschluss-Verify geführt. Der Diff besteht erwartungsgemäß nur aus der `TODO.md`-
Löschung und der AGENTS.md-Zeile — der grep muss leer sein.

## Open Questions

- *(keine)*