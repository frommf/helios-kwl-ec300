# Spec Delta

## Purpose

Diese Capability beschreibt das nicht standardkonforme HTTP-Protokoll der Helios-Anlage,
den lesenden XML-Zugriff und die zentrale Variablen- und Moduslogik. Sie bewahrt außerdem
die Sicherheitsgrenzen und Regeln für lokale Vendor-Referenzen.

## ADDED Requirements

### Requirement: HTTP/1.0-Rohtransport

Die Gerätekommunikation SHALL den vorhandenen asynchronen Raw-Socket-Transport mit
HTTP/1.0 verwenden und Antworten erst nach vollständigem Empfang auswerten. Standard-HTTP
Clients oder ein zusätzlicher Transport SHALL NOT verwendet werden.

#### Scenario: Anfrage an die Standardanlage

- **WHEN** ohne abweichende Konfiguration eine Anfrage an `helios.fritz.box` gesendet wird
- **THEN** erfolgt sie über Port 80 als HTTP/1.0-POST mit `Connection: close`

#### Scenario: Vollständige Antwort auswerten

- **WHEN** die eingebettete Anlage eine Antwort in mehreren TCP-Segmenten beendet
- **THEN** werden zuerst alle Segmente bis zum Verbindungsende gelesen und erst danach
  Status, Header und Body ausgewertet

### Requirement: IP-basierte Anmeldung

Die Anmeldung SHALL durch einen POST des Passworts als `v00402=<password>` an `/info.htm`
erfolgen. Die IP-Adresse des Clients SHALL als Sitzungsbindung ohne Cookie verwendet werden.

#### Scenario: Standardanmeldung

- **WHEN** mit dem Standardpasswort eine Sitzung aufgebaut wird
- **THEN** sendet das System `v00402=!helios!` an `/info.htm` und akzeptiert HTTP 200 als
  erfolgreiche Anmeldung

#### Scenario: Anmeldung abgelehnt

- **WHEN** die Anmeldung keinen HTTP-200-Status erhält
- **THEN** wird ein Authentifizierungsfehler gemeldet und keine aktive Sitzung angenommen

### Requirement: Einmalige Authentifizierungswiederholung

Bei HTTP 403 SHALL das System einmal die IP-Anmeldung durchführen und anschließend
dieselbe Anfrage mit unverändertem Body wiederholen. Ein erneutes 403 SHALL als
Authentifizierungsfehler behandelt werden.

#### Scenario: Wiederholung nach 403

- **WHEN** ein lesender oder ausdrücklich erlaubter steuernder Request mit 403 beginnt
- **THEN** folgen Anmeldung und genau eine identische Wiederholung ohne weitere
  Endpunkt- oder Parameteränderung

#### Scenario: Auch die Wiederholung scheitert

- **WHEN** die wiederholte Anfrage erneut 403 liefert
- **THEN** bricht das System mit einem Authentifizierungsfehler ab

### Requirement: Lesender XML-Datenabruf

XML-Statusdaten SHALL ausschließlich per POST von `/data/*.xml` mit Body
`xml=<endpoint>` gelesen und als ID-/Wert-Paare ausgewertet werden. Andere Endpunkte und
partielle Antworten SHALL NOT akzeptiert werden.

#### Scenario: Primärstatus lesen

- **WHEN** der Primärstatus gelesen wird
- **THEN** sendet das System `xml=/data/werte8.xml` per POST an `/data/werte8.xml` und
  liefert die XML-IDs mit ihren String-Werten zurück

#### Scenario: Weitere Statusbereiche lesen

- **WHEN** Identität oder Partybetrieb-Status benötigt wird
- **THEN** verwendet das System analog `/data/werte20.xml` beziehungsweise
  `/data/werte3.xml`

#### Scenario: Nicht zulässiger XML-Endpunkt

- **WHEN** ein Pfad außerhalb von `/data/` oder ohne `.xml`-Endung gelesen werden soll
- **THEN** wird er vor dem Transport ohne Geräteanfrage abgelehnt

### Requirement: Zentrale Variablenreferenz

Die Dokumentation SHALL die IDs und Wertebereiche für Temperaturen, Lüfter, Basis- und
Sondermodi, Partybetrieb und Statusflags eindeutig bereitstellen.

#### Scenario: Zentrale IDs und Bedeutungen nachschlagen

- **WHEN** ein Entwickler oder Benutzer die zentrale Variablenreferenz verwendet
- **THEN** sind mindestens folgende Zuordnungen dokumentiert

  | Bereich | IDs und Werte |
  |---|---|
  | Temperaturen | `v00104` Außenluft, `v00105` Zuluft, `v00106` Fortluft, `v00107` Abluft in °C |
  | Lüfter | `v00102` Stufe 1–4 oder extern 5/6, `v00103` Prozent, `v00348`/`v00349` Zu-/Abluft-RPM |
  | Modi | `v00101` 0=Auto/1=Manuell, `v00094` Party, `v00099` Ruhe, `v00601` Urlaub |
  | Partybetrieb | `v00091` Dauer 5–180 min, `v00092` Stufe 1–4, `v00093` Restzeit, `v00094` aktiv |
  | Status | `v01306` 32-Bit-Zustandsflags |

### Requirement: Effektive Moduslogik

Der effektive Modus SHALL aus den Modusflags mit der Priorität Partybetrieb, Ruhebetrieb,
Urlaub, manuell und automatisch bestimmt werden. Der Basis-Automatikzustand SHALL NOT mit
dieser effektiven Anzeige verwechselt werden.

#### Scenario: Höhere Priorität überlagert manuellen Betrieb

- **WHEN** neben `v00101=1` auch Party-, Ruhe- oder Urlaubsbetrieb aktiv ist
- **THEN** bestimmt der aktive Sondermodus in der genannten Prioritätsreihenfolge die
  effektive Anzeige

#### Scenario: Kein Sondermodus aktiv

- **WHEN** Party, Ruhe und Urlaub inaktiv sind
- **THEN** zeigt `v00101=1` manuellen und `v00101=0` automatischen Betrieb als effektiven
  Modus

### Requirement: Konfigurationsschutz und Schreib-Allowlist

Jede Gerätekonfiguration MUST read-only bleiben. Schreibvorgänge SHALL auf Anmeldung, die
exakten normalen Betriebsparameter und die exakten Partybetrieb-Bodies begrenzt bleiben;
andere Parameter und versteckte Formularfelder SHALL NOT gesendet werden.

#### Scenario: Nicht freigegebener Schreibzugriff

- **WHEN** eine Aktion `/ruhe.htm`, `/urlaub.htm`, `/syst.htm`, eine andere
  Konfigurationsseite oder einen nicht allowlisted Parameter verändern würde
- **THEN** wird die Aktion ohne Schreibzugriff abgelehnt

### Requirement: Unveränderliche Vendor-Referenzen

`vendor/` SHALL als lokales, git-ignoriertes Referenzmaterial behandelt und weder
verändert, committed noch regeneriert werden. Deutsche Labels SHALL aus dem verifizierten
Web-Dump übernommen werden; fehlendes Vendor-Material SHALL NOT neu erzeugt werden.

#### Scenario: Frischer Klon ohne Vendor-Material

- **WHEN** `vendor/` in einem frischen Klon fehlt
- **THEN** wird dies als erwarteter Zustand akzeptiert und kein Ersatz heruntergeladen oder
  generiert

#### Scenario: Neue deutsche Entitäts- oder Feldbezeichnungen

- **WHEN** neue Bezeichnungen aus Herstellerinformationen benötigt werden
- **THEN** dient `vendor/helios_web_dump/data/lab8_de.xml` als verifizierte Referenz,
  sofern das lokale Material vorhanden ist
