# Tasks

## 1. Core-Protokoll und Basiszustand

- [x] 1.1 Spezialisierte Client-/Info-Operationen für Lüfterstufe und Automatikbetrieb
      mit strikter Validierung und exakt den drei erlaubten `/info.htm`-Bodies gemäß
      Design Decision 1 ergänzen; Client- und Info-Tests für exakte Bodies, Werte 1–4,
      ungültige Werte einschließlich Boolean/String, 403/Login/Retry und Fehlerfälle
      hinzufügen — verify: `just test-lib -k "fan_stage or automatic_mode"` ist grün und
      invalidierte Aufrufe führen nachweislich zu keinem Transportaufruf
- [x] 1.2 `FanSpeed.base_stage` additiv aus `v00102` befüllen und die bisherige
      `stage`-/`automatic`-Semantik unverändert lassen; Parser-/Modelltests einschließlich
      Party-Zielstufe ergänzen und API-Docstrings der neuen Operationen mit der
      Unterscheidung „gesendet“ versus „von der Hardware übernommen“ versehen — verify:
      `just test-lib` ist vollständig grün

## 2. CLI-Steuerung

- [x] 2.1 `helios fan-stage <1–4>` und `helios automatic <on|off>` samt Routing,
      Validierung über `argparse`-Choices und Ausgaben implementieren, die nur den
      gesendeten Auftrag und keine Hardwareverifikation behaupten; Hilfetext und
      gemockte CLI-Tests ergänzen — verify: `just test-lib -k cli` ist grün;
      `just run --help` zeigt beide Befehle und löst keinen Gerätezugriff aus

## 3. Home-Assistant-Steuerung

- [x] 3.1 Coordinator-Protokoll und Methoden für beide Operationen ergänzen und nach
      erfolgreichem Schreiben genau einmal `async_request_refresh()` ohne Sleep oder
      optimistische Datenänderung aufrufen; Coordinator-Tests mit simulierten alten und
      neuen Rücklesewerten hinzufügen — verify: `just test-ha -k coordinator` ist grün
- [x] 3.2 Lüfterstufen-Select auf Basis von `base_stage`, Automatik-Switch auf Basis von
      `not manual`, `switch.py`, `Platform.SWITCH` und die nötigen Fake-HA-Oberflächen
      ergänzen; Entity-/Setup-Tests für Optionen 1–4, Party-Überlagerung, Delegation und
      unveränderte Party-Fan-Entität hinzufügen — verify: `just test-ha` ist vollständig
      grün und die neuen Betriebsentitäten haben kein `EntityCategory.CONFIG`

## 4. Produktdokumentation und Sicherheitsgrenzen

- [x] 4.1 README um Bibliotheks-, CLI- und Home-Assistant-Nutzung, gesendete versus
      verifizierte Zustände sowie das bestehende Aktualisierungsmodell ergänzen; die
      Safety-Tabelle auf genau die drei neuen Betriebs-Bodies erweitern — verify: alle
      dokumentierten Mock-/Hilfebefehle funktionieren und die README enthält keine
      pauschale Zusage sofortiger Hardwareübernahme
- [x] 4.2 `SPECS.md` und `AGENTS.md` mit den neuen erlaubten `/info.htm`-Schreibzugriffen,
      dem Switch-/Live-Test-Layout und dem weiterhin ausnahmslosen
      Konfigurationsschutz synchronisieren — verify: Dokumente widersprechen sich nicht;
      `vendor/` ist unverändert und jede beschriebene Schreiboperation gehört zur
      ausdrücklichen Allowlist

## 5. Live-Mess-Test vorbereiten, ohne ihn auszuführen

- [x] 5.1 Separaten Livetest für Automatik ein/Stufe 1 → manuell/Stufe 2 mit
      `HELIOS_LIVE_TEST=1`-Schutz, Ausgangszustandsprüfung, genau einem Mess-Schreibzugriff,
      Sekunden-Polls, Zeit-/Poll-Protokoll, 30-Sekunden-Grenze und Wiederherstellung im
      `finally`-Block hinzufügen; Marker registrieren und dokumentieren — verify: ohne die
      Variable wird vor jeder Gerätekommunikation übersprungen und reguläres `just test`
      sammelt den Livetest nicht ein

## 6. Abschlussprüfung und reale Zeitmessung

- [x] 6.1 Vollständige Qualitäts- und Sicherheitsprüfung ohne Hardware-Schreibzugriffe
      durchführen — verify: `just check` ist grün; der Diff-Audit aller
      `v00xxx=`-POST-Bodies enthält ausschließlich Login, die bestehenden
      Partybetrieb-Bodies und die drei freigegebenen Betriebs-Bodies
- [x] 6.2 Erst nach erfolgreichem 6.1 und ausdrücklichem Start durch den Nutzer den
      Livetest mit `HELIOS_LIVE_TEST=1 uv run pytest -s
      tests/live/test_operating_control_timing.py` ausführen — verify: Protokoll zeigt
      erste Rückmeldung, benötigte Sekunden/Polls und Stabilität von `v00101=1` und
      `v00102=2`; der Ausgangszustand wurde abschließend wiederhergestellt und lesend
      verifiziert
- [x] 6.3 Messwerte und etwaige Abweichungen dokumentieren und dem Nutzer zur Entscheidung
      über eine separate Folgeänderung der Aktualisierung vorlegen; keine Wartezeit
      automatisch ergänzen — verify: Abschlussbericht enthält Messdaten,
      Wiederherstellungsstatus und die ausdrücklich offene Entscheidung „bestehendes
      Polling genügt“ versus „verzögerte Zweitaktualisierung prüfen“
