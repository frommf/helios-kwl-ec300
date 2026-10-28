# Design

## Context

- `SPECS.md` ist aktuell die einzige konsolidierte Referenz für allgemeines Protokoll und
  Partybetrieb. Die Haupt-Spec `ventilation-control` deckt bereits die normale
  Betriebssteuerung ab und bleibt unverändert.
- Der Produktcode implementiert das gewünschte Verhalten bereits. Der Change ist eine
  Dokumentationsmigration, keine Protokoll- oder Verhaltensänderung.
- `AGENTS.md` und `README.md` enthalten aktuelle Verweise auf `SPECS.md`.
- Archivierte OpenSpec-Changes sind historische Nachweise und werden nicht nachträglich
  geändert. `vendor/` ist git-ignoriertes, ausdrücklich unveränderliches Referenzmaterial;
  dessen lokale Textverweise werden nicht gepflegt und nicht verändert.
- Die Zielanforderungen stehen in den zwei Delta-Specs `device-protocol` und
  `party-mode-control`.

## Goals / Non-Goals

**Goals:**

- Jede einzigartige Information aus `SPECS.md` hat genau eine fachliche Heimat in
  OpenSpec; bereits vorhandene `ventilation-control`-Inhalte werden wiederverwendet.
- Alle gepflegten aktuellen Verweise zeigen auf vorhandene Haupt-Specs, bevor `SPECS.md`
  gelöscht wird.
- Die Migration ist durch eine explizite Inhaltsmatrix, Linkprüfung und Projekt-Checks
  nachweisbar verlustfrei.

**Non-Goals:**

- Keine Code-, API-, Test- oder Geräteverhaltenänderung.
- Keine Änderung an `ventilation-control`, archivierten Changes oder `vendor/`.
- Keine neuen Anforderungen über den dokumentierten Ist-Zustand hinaus und kein Release.

## Decisions

### Decision 1: Feste fachliche Zuordnung statt erneuter Sammlung in einer Sammeldatei

Die Migration folgt dieser Inhaltsmatrix:

| Quelle in `SPECS.md` | Ziel |
|---|---|
| §1 Protokoll & Authentifizierung | `device-protocol`: Rohtransport, IP-Anmeldung, 403-Retry |
| §2 Datenabruf | `device-protocol`: lesende POST-XML-Zugriffe |
| §3 Variablenreferenz | `device-protocol`: zentrale IDs und Wertebereiche |
| §4 Effektive Moduslogik | `device-protocol`: Priorität und Basis-/Effektivmodus |
| §5 Verbotene Operationen | `device-protocol`: Konfigurationsschutz und Allowlist |
| §6 Normale Betriebssteuerung | vorhandene `ventilation-control`, keine Duplikation |
| §7 Partybetrieb | `party-mode-control`: Aktivierung, Deaktivierung, Status und Anzeige |
| §8 Ressourcen | `device-protocol`: Vendor-Regeln; aktuelle Dokumentverweise in README/AGENTS |

Damit ist `SPECS.md` die letzte Sammeldatei, die entfernt wird; es entsteht keine neue
Sammeldatei mit anderem Namen.

### Decision 2: Haupt-Specs vor dem Referenzwechsel synchronisieren

Während der Umsetzung werden die Delta-Specs zunächst mit dem OpenSpec-Sync-Workflow in
`openspec/specs/device-protocol/spec.md` und
`openspec/specs/party-mode-control/spec.md` überführt und strict validiert. Erst danach
werden README und AGENTS auf diese Pfade umgestellt und `SPECS.md` gelöscht.

Der spätere Archiv-Change kann dadurch als bereits synchronisiert geprüft werden; es gibt
keinen Zeitraum mit Verweisen auf noch nicht existierende Haupt-Specs.

**Alternative:** `SPECS.md` erst nach dem Archivieren zu löschen würde einen zweiten,
schlecht nachverfolgbaren Migrationsschritt außerhalb der Tasks erzeugen und ist daher
verworfen.

### Decision 3: Aktuelle Dokumente als kurze Einstiege, OpenSpec als fachliche Heimat

`AGENTS.md` erhält für Protokoll, Variablen und Partybetrieb Verweise auf die jeweilige
Capability statt weiterer Detailkopien. Die nicht verhandelbaren Sicherheitsregeln
bleiben als kompakte Zusammenfassung sichtbar; exakte Bodies und Szenarien stehen in den
Specs. `README.md` behält seine benutzerfreundlichen Erklärungen, ersetzt aber den
Protokoll-Verweis durch Links auf alle drei Capabilities.

Historische Verweise in archivierten Changes bleiben absichtlich unverändert. Ebenso
bleibt `vendor/README.md` trotz seines lokalen Textverweises unangetastet, weil Vendor-
Material laut Projektregeln nicht modifiziert werden darf. Diese nicht gepflegten und
nicht verlinkten Altverweise sind kein Ziel der Migration.

### Decision 4: Verlustfreiheit durch Tokens, Links und Diff-Umfang nachweisen

Vor dem Löschen wird geprüft:

- Alle IDs aus der Inhaltsmatrix (`v00104`–`v00107`, `v00102`, `v00103`, `v00348`,
  `v00349`, `v00101`, `v00094`, `v00099`, `v00601`, `v00091`–`v00094`, `v01306`,
  `v00402`) kommen in den vorgesehenen Haupt-Specs vor.
- Alle Protokoll- und Partybetrieb-Endpunkte, exakten Bodies, Retry-Regeln,
  Modusprioritäten und Vendor-Regeln sind vertreten.
- `SPECS.md` hat keine verbleibenden Verweise in `AGENTS.md` oder `README.md`; alle
  lokalen Markdown-Links dieser Dateien und der neuen Specs existieren.
- `openspec validate --specs --strict`, `just check` und `git diff --check` sind grün.
- Der Diff enthält nur die vorgesehenen Dokumentationsänderungen und die Löschung von
  `SPECS.md`, keine Code- oder Vendor-Änderung.

### Decision 5: Delta und Haupt-Spec inhaltlich identisch halten

Die Delta-Specs sind während des Changes die Arbeitsgrundlage. Der Sync überträgt Purpose
und alle ADDED Requirements unverändert in neue Haupt-Specs mit kanonischem Titel und
einem einzigen `## Requirements`-Abschnitt. Nach dem Sync werden beide Fassungen
programmgesteuert verglichen; spätere inhaltliche Korrekturen müssten erneut synchronisiert
werden.

## Risks / Trade-offs

- **[Einzigartige Protokollinformation geht verloren]** → Inhaltsmatrix und explizite
  Token-/Referenzprüfung vor der Löschung; bei jeder Lücke bleibt `SPECS.md` erhalten.
- **[Links zeigen vor dem Archiv auf fehlende Haupt-Specs]** → Sync bereits während der
  Umsetzung und vor dem Referenzwechsel durchführen.
- **[Delta und Haupt-Spec laufen auseinander]** → Beide Fassungen nach dem Sync exakt
  vergleichen und Strict-Validierung ausführen.
- **[Historische oder Vendor-Altverweise werden als verbleibendes Problem interpretiert]**
  → Gepflegte aktuelle Dokumente und unveränderliche historische/lokale Materialien
  ausdrücklich trennen; nur Erstere werden migriert.
- **[Dokumentationsmigration verändert versehentlich Verhalten]** → Diff-Umfang auf
  Markdown-Dateien begrenzen; `just check` dient als Regressionssicherung.

## Migration Plan

1. Delta-Specs in neue Haupt-Specs synchronisieren und Inhalte vergleichen.
2. AGENTS und README auf die drei Capabilities umstellen.
3. Vollständigkeits-, Referenz- und Linkprüfung durchführen.
4. Erst bei vollständig grünen Prüfungen `SPECS.md` löschen und `just check` wiederholen.
5. Bei einem Befund vor einem Commit die geänderten Dokumente einschließlich `SPECS.md`
   mit Git wiederherstellen; neue Haupt-Specs bleiben unverändert zur Analyse bestehen.
