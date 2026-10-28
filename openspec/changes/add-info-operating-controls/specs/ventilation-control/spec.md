# Spec Delta

## Purpose

Diese Capability steuert ausschließlich die normale Lüfterstufe und den
Basis-Automatikbetrieb der Anlage. Sie stellt die Funktionen in Bibliothek, CLI und
Home Assistant bereit, ohne die Gerätekonfiguration oder andere Betriebsparameter zu
verändern.

## ADDED Requirements

### Requirement: Ausschließlich erlaubte Betriebsparameter

Jeder neue Steuerungs-Schreibvorgang SHALL ausschließlich `/info.htm` und die Parameter
`v00101` beziehungsweise `v00102` verwenden. Der bestehende Login und die bestehende
Partybetrieb-Steuerung bleiben davon unberührt.

#### Scenario: Vollständiger Schreibbody enthält keine Zusatzparameter

- **WHEN** eine der neuen Steuerungsoperationen einen Schreibvorgang auslöst
- **THEN** enthält dessen vollständiger Body nur die für diese Operation definierten
  Werte von `v00101` und/oder `v00102`, insbesondere kein `v01306`, `v00103` oder
  versteckte Formularfelder

### Requirement: Gerätekonfiguration bleibt unveränderbar

Das System MUST zu keinem Zeitpunkt Konfigurationsseiten oder Konfigurationsparameter
der Anlage schreiben. Die neue Steuerung SHALL alle übrigen Geräteeinstellungen
unverändert lassen.

#### Scenario: Zugriff außerhalb der erlaubten Betriebssteuerung

- **WHEN** eine Aktion eine Gerätekonfiguration oder einen anderen nicht freigegebenen
  Parameter verändern würde
- **THEN** wird diese Aktion ohne Schreibzugriff auf die Anlage abgelehnt

### Requirement: Automatikbetrieb schalten

Das System SHALL das Einschalten des Automatikbetriebs mit `v00101=0` und das
Ausschalten mit `v00101=1` an `/info.htm` unterstützen, ohne einen weiteren Parameter
zu übertragen.

#### Scenario: Automatikbetrieb einschalten

- **WHEN** ein Benutzer den Automatikbetrieb einschaltet
- **THEN** sendet das System an `/info.htm` ausschließlich `v00101=0`

#### Scenario: Automatikbetrieb ausschalten

- **WHEN** ein Benutzer den Automatikbetrieb ausschaltet
- **THEN** sendet das System an `/info.htm` ausschließlich `v00101=1`

### Requirement: Normale Lüfterstufe einstellen

Das System SHALL die Lüfterstufen 1, 2, 3 und 4 einstellen können. Jede Stufenänderung
SHALL in demselben Schreibvorgang den manuellen Betrieb mit `v00101=1` aktivieren.

#### Scenario: Stufe bei aktivem Automatikbetrieb einstellen

- **WHEN** bei `v00101=0` die Lüfterstufe 2 eingestellt wird
- **THEN** sendet das System an `/info.htm` ausschließlich `v00101=1&v00102=2`

#### Scenario: Andere Stufe bei manuellem Betrieb einstellen

- **WHEN** bei `v00101=1` die Lüfterstufe 4 eingestellt wird
- **THEN** sendet das System an `/info.htm` ausschließlich `v00101=1&v00102=4`

### Requirement: Ungültige Lüfterstufen vor dem Schreiben ablehnen

Das System SHALL ausschließlich ganzzahlige Lüfterstufen von 1 bis 4 für neue
Stufen-Schreibvorgänge akzeptieren und ungültige Werte vor jeder Gerätekommunikation
ablehnen.

#### Scenario: Nicht schreibbare Stufenwerte

- **WHEN** ein Wert wie 0, 5, 6 oder ein nicht ganzzahliger Wert eingestellt werden soll
- **THEN** meldet das System einen Validierungsfehler und sendet keinen Schreibvorgang

### Requirement: Basiszustand unabhängig vom effektiven Modus darstellen

Der Automatik-Schaltzustand SHALL ausschließlich aus `v00101` abgeleitet werden. Die
normale Lüfterstufe SHALL aus `v00102` stammen und nicht mit einer Party-Zielstufe
oder dem effektiven Modus verwechselt werden.

#### Scenario: Partybetrieb überlagert den Basiszustand

- **WHEN** Partybetrieb aktiv ist, `v00101=0`, `v00102=1` und die Party-Zielstufe 4 beträgt
- **THEN** zeigt die neue Automatiksteuerung weiterhin „ein“ und die normale
  Lüfterstufensteuerung den aus `v00102` gelesenen Wert 1

### Requirement: Authentifizierung für Steuerungsvorgänge

Neue Steuerungsvorgänge SHALL bei HTTP 403 einmal die bestehende Anmeldung und danach
dieselbe Operation mit unverändertem Body wiederholen. Andere Übertragungsfehler SHALL
NOT als erfolgreich übernommener Gerätezustand gemeldet werden.

#### Scenario: Einmalige Wiederholung nach Anmeldung

- **WHEN** der erste Steuerungs-Schreibvorgang mit HTTP 403 abgelehnt wird
- **THEN** erfolgt die Anmeldung und anschließend genau eine Wiederholung desselben
  Schreibbodys

#### Scenario: Fehler nach der Anmeldung

- **WHEN** die Wiederholung erneut fehlschlägt oder ein anderer Übertragungsfehler auftritt
- **THEN** wird der Fehler gemeldet und kein erfolgreich geänderter Gerätezustand behauptet

### Requirement: Zustandsaktualisierung ohne vorab festgelegte Wartezeit

Home Assistant SHALL nach einem neuen Steuerungsvorgang eine Aktualisierung anfordern
und danach im konfigurierten Intervall weiterlesen. Angezeigte Werte SHALL aus
gelesenen Gerätedaten stammen; eine feste Hardware-Wartezeit SHALL NOT vorausgesetzt
werden.

#### Scenario: Sofortige und regelmäßige Aktualisierung

- **WHEN** ein neuer Steuerungsvorgang in Home Assistant erfolgreich gesendet wurde
- **THEN** wird eine Aktualisierung angefordert und anschließend weiter im
  konfigurierten Intervall gelesen, standardmäßig alle 30 Sekunden

#### Scenario: Anlage liefert zunächst noch den alten Wert

- **WHEN** eine unmittelbare Aktualisierung nach dem Schreiben noch den alten Wert liefert
- **THEN** zeigt das System weiterhin einen tatsächlich gelesenen Zustand und übernimmt
  den neuen Wert erst aus einer späteren Geräteantwort

### Requirement: CLI-Befehle für die Betriebssteuerung

Die CLI SHALL `helios fan-stage <1–4>` und `helios automatic <on|off>` anbieten. Ein
erfolgreich gesendeter Schreibauftrag SHALL NOT als bereits an der Hardware
verifizierter Zustand ausgegeben werden; Statusanzeigen erfolgen nur durch Lesevorgänge.

#### Scenario: Lüfterstufe über die CLI einstellen

- **WHEN** `helios fan-stage 2` ausgeführt wird
- **THEN** wird der definierte Schreibauftrag für Stufe 2 gesendet, ohne eine künstliche
  Wartezeit oder eine nicht gelesene Hardwarebestätigung auszugeben

#### Scenario: Automatikbetrieb über die CLI einschalten

- **WHEN** `helios automatic on` ausgeführt wird
- **THEN** wird ausschließlich `v00101=0` an `/info.htm` gesendet

### Requirement: Home-Assistant-Bedienelemente

Home Assistant SHALL eine Select-Entität für die normale Lüfterstufe 1–4 und eine
Switch-Entität für den Basis-Automatikbetrieb bereitstellen. Die bestehende
Partybetrieb-Steuerung SHALL unverändert bleiben.

#### Scenario: Lüfterstufe über die Select-Entität wählen

- **WHEN** in der Select-Entität Stufe 3 gewählt wird
- **THEN** löst die Entität den definierten Schreibvorgang für Stufe 3 und manuellen
  Betrieb aus

#### Scenario: Bestehende Fan-Entität verwenden

- **WHEN** die bestehende Fan-Entität ein- oder ausgeschaltet wird
- **THEN** startet oder stoppt sie weiterhin ausschließlich den Partybetrieb

### Requirement: Automatisierte Tests ohne reale Schreibzugriffe

Reguläre Entwicklungs- und CI-Tests MUST alle neuen Schreibvorgänge simulieren und
MUST NOT Schreibzugriffe auf eine reale Anlage ausführen. Reale Steuerungstests SHALL
ausschließlich explizit als abschließende Live-Tests gestartet werden.

#### Scenario: Reguläre Testsuite oder CI-Lauf

- **WHEN** die regulären Unit-, Integrations- oder CI-Tests ausgeführt werden
- **THEN** werden ausschließlich simulierte Transporte und Geräteantworten verwendet
