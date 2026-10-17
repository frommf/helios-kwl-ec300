# Design

## Context

- `const.py` registriert `PLATFORMS = (FAN, NUMBER, SELECT, SENSOR)`. Die README
  listet zusätzlich Binary Sensors, Switch und Buttons — Dateien `binary_sensor.py`,
  `switch.py`, `button.py` existieren nicht.
- `fan.py` implementiert: Prozente-Anzeige (read-only, fürs Dashboard) sowie
  `TURN_ON`/`TURN_OFF`, die den Party-Modus starten/stoppen. Das ist innerhalb der
  erlaubten Writes (Party start/stop), aber weder die README („read-only fan
  display") noch AGENTS.md („display-only — no writable fan methods") beschreiben
  das Verhalten korrekt.
- AGENTS.md-Audit nach writing-for-agents-Levers: ein toter Pointer
  (`helios_status.py`), drei Duplikate (Vendor-Regel ×3, Device-Protocol-Regeln
  nochmals negativ in Pitfalls, `just check` ×3), verstreute Vendor-Ko-Lokation
  (Layout/Reference/Pitfalls), unklarer Audit-Criterion („audit it so none of the
  above can be triggered").
- Die Recipe-Tabelle in AGENTS.md ist gegen den `justfile` aktuell — sie bleibt,
  weil sie dem Agenten die relevante Teilmenge vorsortiert.

## Goals / Non-Goals

**Goals:**

- README beschreibt exakt, was die Integration registriert und tut
- AGENTS.md: jede Bedeutung an genau einem Ort, alle Pointer lebendig, jeder
  Criterion prüfbar
- Safety-Grenze bleibt vollständig formuliert — Verdichtung, kein Abschwächen

**Non-Goals:**

- Kein Verhaltenscode, keine Umbenennungen, keine `SPECS.md`-Änderung
- Keine GitHub-Ops (Repo public, Tag, Release, Store-PR — verbleiben in `TODO.md`)
- Kein Austausch der `brand/`-Grafiken (`TODO.md` #4, offener Rest)

## Decisions

### Decision 1: Code als Quelle der Wahrheit für die README

Der Entity-Abschnitt wird aus `PLATFORMS` (`const.py`) und `fan.py` abgeleitet —
nicht umgekehrt. Das verhindert die nächste Abweichung, wenn Platforms dazukommen.

### Decision 2: Fan-Regel schärfen statt lockern

Die AGENTS.md-Formulierung wird ersetzt durch: die Fan-Entity darf ausschließlich
Party-Start/Stop schreiben (`TURN_ON`/`TURN_OFF`); keine Methoden, die Stufen oder
Prozente ans Gerät schreiben. Das hält die Safety-Grenze exakt ein und beschreibt
realisierte `fan.py`-Realität — die aktuelle „display-only"-Formulierung ist
faktisch falsch und wäre beim nächsten Audit als Diskrepanz aufgefallen.

### Decision 3: Pitfalls auf nicht-duplizierte Regeln kürzen

Pitfalls behalten nur Regeln, die sonst nirgends stehen (Dependency-Footprint,
`just check`-Criterion als Abschlussbedingung). Die Transport-/Auth-/Vendor-Regeln
stehen bereits positiv und vollständig in Device Protocol bzw. Layout — deren
negativen Wiederholungen entfallen. Der Vendor-Schutz lebt künftig ausschließlich
im Layout-Bullet; die Reference-Sektion behält nur den reinen Pointer.

### Decision 4: Audit-Criterion als grep-Kriterium

„Audit so none of the above can be triggered" wird ersetzt durch ein prüfbares
Kriterium: `grep` im Diff nach `v00xxx=`-POST-Bodies — jeder Treffer muss einer der
drei erlaubten Writes sein. Damit ist „done" binär entscheidbar.

## Open Questions

- *(keine)*