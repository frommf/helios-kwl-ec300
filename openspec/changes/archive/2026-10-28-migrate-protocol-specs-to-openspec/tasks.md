# Tasks

## 1. Neue Haupt-Specs erzeugen

- [x] 1.1 Mit dem OpenSpec-Sync-Workflow und einem zuvor gelesenen Specs-Regel-Snapshot
      `device-protocol` und `party-mode-control` in neue Haupt-Specs überführen; Purpose und
      alle ADDED Requirements exakt vergleichen — verify: beide Dateien unter
      `openspec/specs/` haben kanonische Titel und einen einzigen `## Requirements`-Abschnitt,
      enthalten keine Delta-Header und `openspec validate --specs --strict` ist grün

## 2. Aktuelle Dokumentverweise umstellen

- [x] 2.1 `AGENTS.md` auf die drei Capabilities umstellen und doppelte Detailabschnitte zu
      Protokoll, Variablen und Partybetrieb durch Verweise ersetzen; kompakte
      Sicherheitszusammenfassung und unveränderliche Vendor-/Archiv-Regeln beibehalten —
      verify: `grep -n "SPECS.md" AGENTS.md` ist leer und alle referenzierten
      OpenSpec-Pfade existieren
- [x] 2.2 `README.md` auf `device-protocol`, `party-mode-control` und die unveränderte
      `ventilation-control`-Spec umstellen, ohne benutzerfreundliche Erklärungen oder
      Sicherheitshinweise zu entfernen — verify: `grep -n "SPECS.md" README.md` ist leer
      und alle lokalen Markdown-Links werden per Linkprüfung gefunden

## 3. Vollständigkeit vor dem Löschen nachweisen

- [x] 3.1 Die Inhaltsmatrix aus dem Design mit einem dokumentierten Prüfskript oder
      gleichwertigen Assertions auswerten: sämtliche IDs, Endpunkte, exakten Bodies,
      Retry-Regeln, Modusprioritäten und Vendor-Regeln in den vorgesehenen Haupt-Specs
      nachweisen; Diff-Umfang und unveränderte `ventilation-control`-Spec kontrollieren —
      verify: keine fehlenden Tokens oder unerwarteten Code-/Vendor-Änderungen; andernfalls
      stoppen und `SPECS.md` nicht löschen

## 4. `SPECS.md` entfernen und Migration abschließen

- [x] 4.1 Erst nach erfolgreichem Abschluss von 1.1–3.1 `SPECS.md` löschen und die
      vollständige Dokumentations- und Projektverifikation wiederholen — verify:
      `just check`, `openspec validate --specs --strict`, lokale Linkprüfung und
      `git diff --check` sind grün; der Abschluss-Diff enthält ausschließlich die
      vorgesehenen Markdown-Änderungen, neuen Haupt-Specs und die Löschung von `SPECS.md`
