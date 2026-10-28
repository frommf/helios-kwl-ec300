# Design

## Context

- `HeliosClient` kapselt bereits den Raw-Socket-Transport, die IP-Anmeldung und die
  einmalige Wiederholung nach HTTP 403. Partybetrieb ist bislang der einzige
  Geräte-Schreibzugriff neben der Anmeldung.
- Home Assistant liest standardmäßig alle 30 Sekunden über den Coordinator und fordert
  nach Partybetrieb-Schreibvorgängen sofort eine Aktualisierung an. CLI und Bibliothek
  besitzen keinen eigenen Poll-Timer.
- `FanSpeed.stage` zeigt während Partybetrieb bewusst `v00092` statt `v00102` an.
  `OperationMode.automatic` beschreibt den effektiven Modus und ist auch bei aktiven
  Party-/Ruhe-/Urlaubsüberlagerungen `False`. Beide vorhandenen Felder bleiben für ihre
  bisherigen Anzeigezwecke erhalten, eignen sich aber nicht direkt für die neuen
  Basis-Steuerungen.
- Das Formular `info.htm` enthält zahlreiche weitere sichtbare und versteckte Felder.
  Diese werden nicht nachgebildet: Die neuen Requests bestehen ausschließlich aus den
  freigegebenen Parametern `v00101` und/oder `v00102`.
- Die Anforderungen stehen in `specs/ventilation-control/spec.md`; die Motivation steht
  in `proposal.md`.

## Goals / Non-Goals

**Goals:**

- Eine zentrale, validierte und auf zwei Parameter begrenzte Schreibimplementierung für
  Bibliothek, CLI und Home Assistant.
- Bestehende Transport-, Authentifizierungs- und Coordinator-Mechanismen wiederverwenden.
- Basisbetriebszustand und effektiven Anzeigezustand ohne Breaking Change trennen.
- Reguläre Tests vollständig von realer Hardware trennen und die Übernahmedauer erst am
  Ende an einem kontrollierten Live-Test messen.

**Non-Goals:**

- Kein generischer öffentlicher Schreib-Endpoint und keine Übertragung des vollständigen
  HTML-Formulars.
- Keine Lüfter-Prozentwerte, externen Stufen 5/6 oder Änderungen an Ruhe-, Urlaubs-,
  Zeitprogramm-, Sensor-, Netzwerk- oder sonstiger Gerätekonfiguration.
- Keine neue Laufzeitabhängigkeit und kein zusätzlicher HTTP-Transport.
- Keine vorab festgelegte blockierende Wartezeit und kein optimistischer Gerätezustand.

## Decisions

### Decision 1: Zwei kleine Core-Operationen statt generischem Schreibzugriff

Die öffentliche High-Level-API erhält `Info.set_fan_stage(fan_stage)` und
`Info.set_automatic_mode(enabled)`. Beide delegieren an spezialisierte
`HeliosClient`-Methoden. Der Client validiert Stufen strikt als ganze Zahlen 1–4, bevor
ein Transportaufruf möglich ist, und erzeugt ausschließlich folgende Bodies:

- Stufe: `v00101=1&v00102=<stage>`
- Automatik ein: `v00101=0`
- Automatik aus: `v00101=1`

Ein privater gemeinsamer Ablauf für diese beiden Operationen behandelt HTTP-Status und
403/Login/Retry analog zum Partybetrieb. Es gibt keine öffentliche Methode, der ein
beliebiger Endpoint oder Body übergeben werden könnte. Die vorhandenen Partybetrieb-
Methoden werden nicht refaktoriert; dadurch bleibt der Diff klein und ihr Verhalten
unverändert.

**Alternative:** Ein generisches `set_parameters()` wäre flexibler, ließe sich aber
schwerer statisch und im Review auf die Sicherheits-Allowlist begrenzen.

### Decision 2: Bestehende Anzeigesemantik durch ein additives Basisfeld ergänzen

`FanSpeed` erhält ein additives, optionales Feld `base_stage`, das der Parser immer
unverändert aus `v00102` befüllt. Das vorhandene `stage` behält seine Party-Anzeige-
Semantik. Die neue Lüfterstufensteuerung verwendet ausschließlich `base_stage` und keinen
Fallback auf `stage`.

Der Automatik-Switch verwendet `not OperationMode.manual`, weil `manual` direkt aus
`v00101` entsteht. Das vorhandene `automatic`-Feld und die Priorität des effektiven
Modus bleiben unverändert.

**Alternative:** Die Bedeutung von `stage` oder `automatic` zu ändern würde bestehende
Sensoren, Fan-Anzeigen und API-Nutzer brechen.

### Decision 3: Eigene HA-Bedienelemente statt Erweiterung der Party-Fan-Entität

Die Lüfterstufe wird als zweite Select-Entität in `select.py` neben der lokalen
Party-Standardstufe ergänzt. Der Automatikbetrieb erhält eine neue `switch.py` und die
Registrierung von `Platform.SWITCH`. Beide Entitäten sind Betriebssteuerungen und
erhalten daher kein `EntityCategory.CONFIG`.

Die Lüfterstufen-Select bietet nur `"1"` bis `"4"` an und delegiert an neue
Coordinator-Methoden. Der Switch bildet den Basiszustand über `not manual` ab. Die
bestehende Fan-Entität bleibt unangetastet und startet/stoppt weiterhin ausschließlich
Partybetrieb.

**Alternative:** `SET_SPEED` auf der bestehenden Fan-Entität würde Partybetrieb und
normale Lüftung auf derselben Ein-/Aus-Semantik vermischen.

### Decision 4: Bestehendes Aktualisierungsmodell ohne künstliches Sleep

Die neuen Coordinator-Methoden rufen nach erfolgreichem API-Schreibvorgang wie beim
Partybetrieb `async_request_refresh()` auf. Danach gilt weiterhin das konfigurierte
Polling-Intervall, standardmäßig 30 Sekunden. Es gibt kein `asyncio.sleep()`, keine
10-Sekunden-Sperre und keinen separaten Poll-Timer.

Die Entitäten schreiben keinen optimistischen Zielwert in den Coordinator. Liefert die
sofortige Aktualisierung noch alte Werte, bleiben diese sichtbar, bis ein späterer
Lesevorgang neue Werte liefert.

Die neuen CLI-Befehle führen nur den jeweiligen Schreibauftrag aus. Ihre Ausgabe
bezeichnet den Auftrag als gesendet, nicht als an der Hardware verifiziert. Ein erneuter
Statusabruf erfolgt nur durch einen ausdrücklich aufgerufenen Statusbefehl.

### Decision 5: Explizit aktivierter Live-Test statt Standard-Hardwaretest

Ein separater pytest-Livetest wird nur bei ausdrücklich gesetzter
`HELIOS_LIVE_TEST=1` ausgeführt; in allen anderen Fällen wird er vor jeder
Gerätekommunikation übersprungen. Der reguläre `just test`-Lauf bleibt dadurch
schreibfrei.

Der Test prüft zunächst lesend die erwartete Ausgangslage Automatik ein/Stufe 1. Bei
einer anderen Ausgangslage bricht er ohne Schreibzugriff ab. Anschließend:

1. genau ein Schreibvorgang `v00101=1&v00102=2` an `/info.htm`,
2. Zeitstempel und gelesene Werte von `v00101`/`v00102` etwa einmal pro Sekunde
   aufzeichnen, bis die Zielwerte stabil gelesen werden oder 30 Sekunden verstrichen
   sind,
3. erste Erkennung, Poll-Anzahl und Stabilität ausgeben,
4. im `finally`-Block den Ausgangszustand mit den erlaubten Operationen Stufe 1 und
   anschließend Automatik ein wiederherstellen.

Das gemessene Ergebnis wird abschließend berichtet. Eine etwaige zusätzliche
Laufzeit-Wartezeit oder verzögerte Zweitaktualisierung wird nicht automatisch angenommen,
sondern anhand der Messdaten als separate Entscheidung festgelegt.

**Alternative:** Ein dauerhaft aktivierter Integrationstest mit Standard-Host könnte in
Entwicklung oder CI unbeabsichtigt reale Hardware verändern und ist ausgeschlossen.

### Decision 6: Sicherheitsdokumentation und Audit als Teil des Changes

`SPECS.md`, `AGENTS.md` und `README.md` werden zusammen mit der Implementierung
aktualisiert. Die Dokumente benennen die drei exakten neuen Request-Bodies und führen
Konfiguration weiterhin als ausnahmslos schreibgeschützt. Der Abschluss-Audit prüft den
Diff auf alle `v00xxx=`-Bodies; erlaubt bleiben nur Login, die bestehenden
Partybetrieb-Bodies und die drei neuen Betriebs-Bodies. `vendor/` bleibt unverändert.

## Risks / Trade-offs

- **[Der minimale Body wird von einer Firmwarevariante nicht akzeptiert]** → Der
  abschließende Livetest prüft dies an realer Hardware. Es gibt keinen automatischen
  Fallback auf `v01306`, andere Endpunkte oder zusätzliche Formularfelder; stattdessen
  wird der Befund ohne weitere Schreibversuche gemeldet.
- **[HTTP 200 bedeutet noch keine sofortige Hardwareübernahme]** → Keine optimistische
  Anzeige oder Verifikationsbehauptung; die Live-Messung liefert die Grundlage für eine
  spätere Aktualisierungsentscheidung.
- **[Die sofortige Aktualisierung zeigt kurzzeitig alte Werte]** → Bewusster Trade-off
  zugunsten des bestehenden einfachen Polling-Modells; spätere Polls korrigieren den
  Zustand ausschließlich anhand gelesener Daten.
- **[Partybetrieb verfälscht die neue Anzeige]** → `base_stage` und `manual` entkoppeln
  die Basissteuerung vom effektiven Anzeige- und Party-Zustand.
- **[Ein Live-Test könnte im manuellen Zustand enden]** → Ausgangswerte protokollieren,
  Wiederherstellung im `finally`-Block und anschließende Leseverifikation.
- **[Ungültige Python-Werte wie `True` wirken wie Ganzzahl 1]** → Die Core-Validierung
  verlangt einen echten Integer und akzeptiert keine Booleans oder still konvertierten
  Strings.

## Migration Plan

Es gibt keine Migration persistenter Daten oder bestehender Entity-IDs. Nach einem
Update erscheinen lediglich die neue Select- und Switch-Entität. Ein Software-Rollback
entfernt diese wieder, verändert aber nicht selbstständig den zuletzt am Gerät
eingestellten Betriebszustand; vor einem Rollback ist daher der gewünschte Zustand mit
den erlaubten Steuerungen herzustellen.
