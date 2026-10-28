# Ergebnisse des Live-Mess-Tests

## Ausführung

- **Datum:** 2026-10-28
- **Befehl:** `HELIOS_LIVE_TEST=1 uv run pytest -s tests/live/test_operating_control_timing.py`
- **Vorbedingung lesend bestätigt:** effektiver Automatikbetrieb und Basis-Lüfterstufe 1
- **Mess-Schreibzugriff:** genau ein POST `v00101=1&v00102=2` an `/info.htm`
- **Ergebnis:** bestanden, keine Abweichungen oder zusätzlichen Mess-Schreibversuche

## Messwerte

| Read-only-Poll | Zeit nach Schreibbeginn | `v00101` manuell | `v00102` | Zielwerte gelesen |
|---:|---:|:---:|---:|:---:|
| 1 | 0,274 s | ja | 2 | ja |
| 2 | 1,277 s | ja | 2 | ja |
| 3 | 2,279 s | ja | 2 | ja |

- **Erste korrekte Rückmeldung:** Poll 1 nach 0,274 Sekunden
- **Stabile Rückmeldung:** drei aufeinanderfolgende Polls, bestätigt bei Poll 3 nach
  2,279 Sekunden
- **Gesamtdauer des pytest-Laufs einschließlich Wiederherstellung:** 2,96 Sekunden

## Wiederherstellung

Der `finally`-Block hat Stufe 1 und anschließend den Basis-Automatikbetrieb erneut
angefordert. Stufe 1 wurde vor der Automatikaktivierung lesend bestätigt; anschließend
wurde der eingeschaltete Basis-Automatikbetrieb ebenfalls lesend verifiziert.

## Bewertung und offene Entscheidung

Für den gemessenen Fall genügte die bereits vorhandene sofortige Aktualisierung: Der
erste Read-only-Poll lieferte beide Zielwerte. Es wurde keine Wartezeit, kein Sleep und
keine zusätzliche verzögerte Aktualisierung in den Produktcode eingebaut.

Zur abschließenden Nutzerentscheidung stehen damit:

1. **Bestehendes Polling genügt (empfohlen anhand dieser Messung):** sofortige
   Aktualisierung und reguläres konfiguriertes Polling unverändert beibehalten.
2. **Verzögerte Zweitaktualisierung prüfen:** nur als separate Folgeänderung, falls
   trotz des unmittelbar korrekten Messergebnisses zusätzliche Robustheit gewünscht ist.
