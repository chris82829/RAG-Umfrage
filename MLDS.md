# DIANA-Personality-MLDS

Das DIANA-Profil bildet die bearbeitbare `AdvisorConfig` als JSON ab. Die Serialisierung ist deterministisch und benötigt keinen LLM-Aufruf.

## Einordnung und Quellen

MLDS bedeutet **Meta-Language-defined Structures**. Die zugehörigen MLDSI beschreiben Syntax, Regeln und Domänensemantik. Die [endgültige Veröffentlichung](https://annals-csis.org/Volume_43/drp/pdf/5613.pdf) erläutert diese Trennung auf S. 531–534 und zeigt JSON-basierte Beispiele auf S. 535–537. Das Autorenrepository enthält eine [JSON-basierte MLDSI-Datei](https://github.com/CoNaLaDe-MLDS/Artifacts/blob/master/Meta-Language%20instructions/automotive/AutomotiveSecurityMLDSInstructions.mldsi) und eine [MLDS-Ausgabe](https://github.com/CoNaLaDe-MLDS/Artifacts/blob/master/MLDS%20output%20examples/automotive/Example%201/output.mlds).

**DIANA-Personality-MLDS ist eine eigene Domänenspezifikation.** Die Quellen definieren weder ein allgemeines Persönlichkeitsformat noch die folgenden Feldnamen, Versionsregeln oder APIs. Die Dateiendungen orientieren sich an den Autorenartefakten.

## Dateien und Datenvertrag

- `personas/Personality.mldsi`: externes JSON-Schema mit Feldbeschreibungen und Domänenregeln, erzeugt aus `persona_mlds.personality_schema()`.
- `personas/career.mlds`, `personas/expert.mlds`: eingebaute Persönlichkeitsschablonen einschließlich UI-Metadaten.
- `personas/neutral.mlds`: eingebaute neutrale Konfiguration.

Jedes MLDS-Dokument hat `format: "DIANA-Personality-MLDS"`, `schema_version: 1`, `provenance` und `personality`. Die Herkunft enthält `method: "Meta-Language-defined Structures"`, `reference: "https://doi.org/10.15439/2025F5613"` und `origin` mit einem der Werte `builtin`, `session` oder `legacy`. Bei `builtin` ist `template` mit `id`, `subtitle`, `summary` und `selectable` zwingend erforderlich. Bei `session` und `legacy` muss `template` fehlen oder `null` sein.

`personality` enthält alle sechs Felder der validierten ursprünglichen `AdvisorConfig`:

| Feld | Bedeutung und Regeln |
| --- | --- |
| `mode` | `preset` oder `custom`; bestimmt die bestehende Laufzeitauflösung. |
| `preset` | Bestehender Schlüssel: `diana`, `steve`, `angela`, `guenther` oder `neutral`. Bleibt auch im Modus `custom` als Konfigurationsfeld erhalten. |
| `name` | Bearbeitbarer Name, 1–60 Zeichen. Der Anzeigezusatz `-KI` wird erst zur Laufzeit erzeugt. |
| `traits` | Eindeutige Auswahl aus `analytisch`, `direkt`, `ermutigend`, `empathisch`, `neugierig`, `kreativ`, `strukturiert`, `kritisch`; höchstens vier, bei `custom` mindestens eine. Gestaltet Ausdruck und ergänzende Bewertungsgewichte. |
| `focus` | `ausgewogen`, `fachliche_tiefe`, `lernpotenzial` oder `innovation`; gestaltet ergänzende Bewertungsschwerpunkte. |
| `description` | Freitext bis 2000 Zeichen zu gewünschter Rolle und Ausdruck; keine Qualifikation der nutzenden Person. |

Beispiel ohne Schablonenmetadaten:

```json
{
  "format": "DIANA-Personality-MLDS",
  "schema_version": 1,
  "provenance": {
    "method": "Meta-Language-defined Structures",
    "reference": "https://doi.org/10.15439/2025F5613",
    "origin": "session"
  },
  "personality": {
    "mode": "custom",
    "preset": "diana",
    "name": "Meine DIANA",
    "description": "",
    "traits": ["analytisch", "ermutigend"],
    "focus": "ausgewogen"
  }
}
```

## Adapter und Laufzeit

| Schnittstelle in `persona_mlds` | Vertrag |
| --- | --- |
| `personality_schema()` | Liefert das JSON-Schema für `Personality.mldsi`. |
| `advisor_to_mlds(config, *, origin='session')` | Validiert die Konfiguration und erzeugt ein MLDS-Dictionary; erlaubt ausschließlich `session` oder `legacy` als Herkunft. |
| `advisor_from_mlds(value)` | Akzeptiert ein Dictionary oder JSON-Text und liefert ein normales, vollständiges `AdvisorConfig`-Dictionary. Liest auch eine rohe Legacy-Konfiguration mit den bestehenden Standardwerten, ohne die Quelle neu zu schreiben. |
| `load_templates()` | Liefert die Schablonen `career` und `expert` mit UI-Metadaten sowie `advisor` und `mlds`. |
| `load_neutral_advisor()` | Liefert die neutrale `AdvisorConfig`. |

Pydantic bleibt die Validierungsinstanz an der Anwendungsgrenze. Das externe MLDSI-Schema beschreibt dieselben Domänenregeln, einschließlich eindeutiger Eigenschaften und der Mindestanzahl im Modus `custom`. Unbekannte Versionen, fehlende erforderliche MLDS-Felder und doppelte Schlüssel im eingelesenen JSON werden abgewiesen. Fehlerhafte MLDS-Dokumente erhalten keinen Rückfall auf Legacy-Standardwerte. Strukturelle Validierung ersetzt keine inhaltliche Prüfung von Freitext.

Gespeichert wird die validierte Rohkonfiguration, nicht das Ergebnis von `resolve_advisor()`. Damit bleiben bearbeitbarer Name, Beschreibung und Auswahl erhalten. Namensnormalisierung mit `-KI`, Stilhinweise, Ausdrucksbeispiele und abgeleitete Bewertungsgewichte verbleiben in `advisor.py`. Die bestehenden Preset-Schlüssel verweisen weiterhin auf deren dort definierte Semantik; sie werden beim Laden nicht auf die neuen Schablonen umgeschrieben. Der Datenaustausch ist hinsichtlich der validierten Konfiguration verlustfrei, nicht hinsichtlich ursprünglicher JSON-Formatierung oder vor der Validierung vorhandener Rand-Leerzeichen.

## Nutzungsweg

`GET /api/persona-templates` liefert den MLDS-basierten Katalog. Das Frontend lädt ihn vor dem Onboarding und verwendet seine Schablonen in der Persönlichkeitsauswahl. Der Sitzungszustand enthält die Konfiguration als `advisor_mlds`. Der Chat liest sie mit `advisor_from_mlds()` zurück; nach einem Update wird sie erneut serialisiert. Bestehende Sitzungen mit dem rohen Feld `advisor` bleiben lesbar.

`study_release.py` bezieht `persona_mlds.py` und sämtliche Dateien in `personas/` in den Release-Hash ein. Damit werden Änderungen am Adapter, Schema und Katalog im Release-Fingerabdruck berücksichtigt.

## Datenhaltung

Der Adapter schreibt keine Dateien und migriert vorhandene Daten nicht durch Neuschreiben. Eingebaute Schablonen enthalten keine Teilnehmerdaten. Individueller Freitext bleibt im bestehenden Sitzungskontext; dieses Profil führt keine zusätzliche langfristige Speicherung von Forschungsdaten ein. `provenance` bezeichnet die vorgesehene Herkunft; sie ist keine Echtheits- oder Vertrauensgarantie und kein Nachweis der Teilnehmerdatenfreiheit einer beliebigen eingelesenen Datei.
