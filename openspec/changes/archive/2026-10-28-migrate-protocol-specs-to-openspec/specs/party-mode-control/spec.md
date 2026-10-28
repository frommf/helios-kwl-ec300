# Spec Delta

## Purpose

Diese Capability beschreibt den ausdrücklich erlaubten, zeitlich begrenzten Partybetrieb
mit Lüfterstufe 1–4. Sie umfasst dessen sichere Aktivierung und Deaktivierung,
Statusabfrage, Zielstufenanzeige und die bestehenden Produktoberflächen.

## ADDED Requirements

### Requirement: Partybetrieb aktivieren

Die Aktivierung SHALL per POST an `/party.htm` mit Lüfterstufe, Dauer, Restzeit 0 und
Aktivierungsflag erfolgen. Der vollständige Body SHALL das Format
`v00092=<stage>&v00091=<minutes>&v00093=0&v00094=1` haben.

#### Scenario: Partybetrieb für 90 Minuten mit Stufe 3 starten

- **WHEN** Partybetrieb mit Dauer 90 Minuten und Stufe 3 aktiviert wird
- **THEN** sendet das System exakt `v00092=3&v00091=90&v00093=0&v00094=1` an `/party.htm`

### Requirement: Aktivierungsparameter validieren

Die Partydauer SHALL zwischen 5 und 180 Minuten liegen und auf Vielfache von 5 Minuten
gerundet werden; die Lüfterstufe SHALL zwischen 1 und 4 liegen. Ungültige Werte SHALL NOT
an die Anlage gesendet werden.

#### Scenario: Dauer auf fünf Minuten runden

- **WHEN** eine Aktivierung mit 92 Minuten und Stufe 3 angefordert wird
- **THEN** verwendet der Aktivierungs-Body eine gerundete Dauer von 90 Minuten

#### Scenario: Werte außerhalb der Grenzen ablehnen

- **WHEN** Dauer unter 5 oder über 180 Minuten beziehungsweise Stufe außerhalb 1–4 beträgt
- **THEN** meldet das System einen Validierungsfehler ohne Partybetrieb-Schreibzugriff

### Requirement: Partybetrieb deaktivieren

Die Deaktivierung SHALL per POST an `/party.htm` erfolgen und ausschließlich
`v00094=0` enthalten. Danach SHALL die Anlage zum vorherigen Betriebsmodus zurückkehren.

#### Scenario: Partybetrieb stoppen

- **WHEN** ein Benutzer den Partybetrieb deaktiviert
- **THEN** sendet das System exakt `v00094=0` an `/party.htm`

### Requirement: Partybetrieb-Zustand lesen

Der Partybetrieb-Zustand SHALL lesend aus `/data/werte3.xml` mit Body
`xml=/data/werte3.xml` abgerufen werden und Aktivierung, konfigurierte Dauer, Zielstufe
und Restzeit abbilden.

#### Scenario: Aktiven Partybetrieb auswerten

- **WHEN** die XML-Daten `v00094=1`, `v00091=120`, `v00092=4` und `v00093=45` enthalten
- **THEN** zeigt der Zustand aktiven Partybetrieb mit 120 Minuten Konfiguration, Stufe 4
  und 45 Minuten Restzeit

### Requirement: Party-Zielstufe anzeigen

Während aktivem Partybetrieb SHALL die effektive Lüfterstufenanzeige die Party-Zielstufe
`v00092` verwenden. Die normale Basisstufe `v00102` SHALL dabei separat erhalten bleiben.

#### Scenario: Zielstufe während Hochfahren der Lüfter

- **WHEN** Partybetrieb aktiv ist, `v00092=3` und `v00102=2` beträgt
- **THEN** zeigt die effektive Anzeige Stufe 3 als Party-Zielstufe, während die normale
  Basisstufe weiterhin 2 lautet

#### Scenario: Kein Partybetrieb aktiv

- **WHEN** `v00094=0` gilt
- **THEN** verwendet die effektive Lüfterstufenanzeige `v00102`

### Requirement: Authentifizierung für Partybetrieb

Partybetrieb-Schreibvorgänge SHALL die gemeinsame IP-Anmeldung und einmalige
403-Wiederholung aus `device-protocol` verwenden. Andere HTTP-Fehler SHALL NOT als
erfolgreiche Partybetrieb-Änderung gemeldet werden.

#### Scenario: Identische Partybetrieb-Anfrage nach Anmeldung wiederholen

- **WHEN** ein Partybetrieb-Schreibvorgang zunächst mit 403 abgelehnt wird
- **THEN** erfolgt die Anmeldung und genau eine Wiederholung mit unverändertem Body

#### Scenario: Unerwarteter HTTP-Status

- **WHEN** ein Partybetrieb-Schreibvorgang nach etwaiger Wiederholung keinen HTTP-200-Status
  erhält
- **THEN** wird ein Protokoll- oder Authentifizierungsfehler gemeldet

### Requirement: Home-Assistant-Partybetrieb-Fan

Die bestehende Home-Assistant-Fan-Entität SHALL ihren Ein-/Aus-Zustand aus der
Partybetrieb-Aktivität ableiten und ausschließlich Partybetrieb starten oder stoppen.
Ihre Prozentanzeige SHALL nur der Darstellung dienen und keine Geräte-Schreibvorgänge
auslösen.

#### Scenario: Fan einschalten

- **WHEN** die Fan-Entität eingeschaltet wird
- **THEN** startet sie Partybetrieb mit der lokal konfigurierten Standarddauer und
  Standardstufe

#### Scenario: Fan ausschalten

- **WHEN** die Fan-Entität ausgeschaltet wird
- **THEN** deaktiviert sie ausschließlich den Partybetrieb, ohne normale Lüfterstufe oder
  Gerätekonfiguration zu verändern
