# Proposal

## Why

`SPECS.md` enthält weiterhin die einzige konsolidierte Referenz für allgemeines
Geräteprotokoll und Partybetrieb, während normale Betriebssteuerung bereits in OpenSpec
spezifiziert ist. Die verbleibenden Inhalte sollen ohne Informationsverlust in
fachlich abgegrenzte Capabilities überführt werden, damit `SPECS.md` anschließend
vollständig entfallen kann.

## What Changes

- Eine neue Capability `device-protocol` übernimmt Transport, Authentifizierung,
  XML-Datenabruf, Variablenreferenz, effektive Moduslogik und Vendor-Referenzen aus
  `SPECS.md`.
- Eine neue Capability `party-mode-control` übernimmt Partybetrieb-Verhalten,
  Aktivierung, Deaktivierung, Parameter, Anzeige der Zielstufe und
  Authentifizierungswiederholung.
- Die vorhandene `ventilation-control`-Spec bleibt unverändert; bereits dort abgedeckte
  normale Betriebssteuerung wird nicht in eine zweite Capability dupliziert.
- `AGENTS.md` und `README.md` verweisen auf die drei maßgeblichen OpenSpec-Capabilities
  anstelle von `SPECS.md`.
- `SPECS.md` wird erst gelöscht, nachdem Vollständigkeit, Referenzen und lokale Links
  geprüft wurden. Produktverhalten und Geräteeinstellungen bleiben unverändert.

## Capabilities

### New Capabilities

- `device-protocol`: Rohtransport, IP-Authentifizierung, lesender XML-Zugriff,
  zentrale Variablen, effektive Moduslogik und unveränderliche Vendor-Referenzen.
- `party-mode-control`: Zeitlich begrenzter Partybetrieb mit validierten
  Aktivierungsparametern, Deaktivierung, Zielstufenanzeige und sicherer
  Authentifizierungswiederholung.

### Modified Capabilities

- *(keine; `ventilation-control` bleibt inhaltlich unverändert)*

## Impact

- **Dokumentation:** neue Delta-Specs für zwei Capabilities, aktualisierte Verweise in
  `AGENTS.md` und `README.md`, anschließendes Löschen von `SPECS.md`.
- **OpenSpec-Haupt-Specs:** beim Archivieren werden zwei neue Haupt-Specs aus den
  Delta-Specs erzeugt.
- **Produktcode und APIs:** keine Änderungen; keine Abhängigkeiten und keine
  Geräte-Schreibzugriffe.
- **Verifikation:** Vollständigkeitsvergleich der migrierten Inhalte,
  Markdown-Linkprüfung, OpenSpec-Strict-Validierung und `just check`.
