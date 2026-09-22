# V14 – Umsetzung und technische Prüfung

Stand: 22. September 2026. Grundlage ist der Fragebogen-, Metadaten- und Analyseplan vom selben Tag. Sicherungsbranch vor dem Umbau: `sicherung-vor-v14-2026-09-22` (`af5194054faf51a7b7bc063ffffeab2feb09e65b`). Arbeits- und Veröffentlichungsbranch: `studie-v14-analyseplan-2026-09-22`.

## Umsetzung

- Neuer einziger aktiver Fragebogen `diana-v14`: bisherige Formulierungen erhalten; zwei Vertrauensitems, ein Manipulationscheck und Wiederholungsscreening ergänzt. 19 Ratings mit 1–7 und „Kann ich nicht beurteilen“, insgesamt 26 Fragen in A/B und 27 in C einschließlich Screening und optionaler Angaben. E1 nicht ergänzt. Historische V13-Daten und Definitionen bleiben getrennt erhalten.
- Verwaltung: Studienphase und E-Mail-Welle für neue Teilnahmen; Phase wird bei Einwilligung eingefroren. Standard ist `pretest`. Metadatenansicht enthält auch Einwilligungen ohne erste Fragebogenantwort, Fortschritt, Darstellungsbreite, Fehler und tatsächlich berechnete Gewichte. Rohdaten und technische Analysedaten sind exportierbar.
- Gewichtungsformel unverändert 60/15/7/6/6/6. Bekannten widersprüchlichen B-Prompt korrigiert; alte unveränderliche Teilnahmesnapshots erhalten. Neue explizit abweichende Prozentangaben werden bei der Promptbearbeitung abgewiesen.
- Statistik auf ausdrücklichen Aufruf: H1 C−B, feste sekundäre Holm-Familie, Effektgrößen und Konfidenzintervalle, Manipulationscheck, Reliabilität und Wiederholungssensitivitäten. CLI und Verwaltung nutzen dieselbe Berechnung. Nur V14-Hauptstudie; vollständig beantwortete Konstrukte können auch aus unvollständigen Fragebögen beitragen.
- Versionierter Analyseplan mit Prüfsumme. Offene Parameter bleiben `null`; Status bleibt `draft`. Gemischte Prompt- oder Systemfassungen werden ausdrücklich ausgewiesen.
- Separate Offline-Werkzeuge für 40–80 zufällige Belegtreuepaare, zwei unabhängige menschliche Rater und Cohen-κ. Keine automatisch erfundenen Raterurteile oder neuen API-Anfragen.

## Nachweise

| Prüfung | Ergebnis |
| --- | --- |
| Vollständige Python-Testsuite | 153 Tests und 174 Subtests bestanden |
| Frontend-Tests | 35 bestanden |
| Browserdurchlauf A, B, C | Einwilligung, Screening, Wartezeitfragen, drei erfolgreiche Chatnachrichten, 19 Ratings und Abschluss erfolgreich; keine JavaScript-Fehler |
| Mobile Darstellung | C bei 390 px geprüft; kein horizontaler Überlauf |
| Verwaltungsprüfung | Phasenwechsel mit CSRF/Revision, UTC-Welle, getrennte Filter, leere und befüllte Analyse, Metadaten-ZIP und Gewichtsvektoren geprüft |
| Unabhängige Integrationstests | 6 Tests für HTTP-Rechte, Schema/Exporte, vollständige und teilweise Antworten, Scoring und Promptmigration bestanden |
| Power-Gegenprüfung | d = 0,35: 130 gültige Personen je Arm bei α = 0,05 und 80 % Power unter balancierter t-Modellplanung; unabhängig gegen statsmodels geprüft |

Alle Testteilnahmen, Antworten und Modellergebnisse waren isolierte synthetische Fixtures. Kein kostenpflichtiger Modellaufruf; keine Testantworten in Produktivdatenbanken. Browseraufzeichnungen und Detailprotokolle liegen lokal unter `/tmp/diana-v14-*`; die dauerhaft wiederholbaren Regressionsprüfungen liegen im Repository. Der Frontend-Build verwendet dieselben festgeschriebenen Paketversionen; wegen lokal nicht vollständig verfügbarer iCloud-Dateien wurde isoliert gebaut, mit Lucide-CJS-Einstieg und ohne CSS-Minifizierung.

## Vor tatsächlicher Hauptrekrutierung offen

SESOI, Ausfallreserve, konkrete Rekrutierungszeiten und anschließender nachvollziehbarer Freeze sind Forschungsentscheidungen. Der kognitive Pretest und die menschliche Belegtreueprüfung sind noch nicht durchgeführt. Die beiden Vertrauensitems sind ausdrücklich eine eigene, an ResQue/CRS-Que angelehnte Adaptation. Verknüpfte Nutzungsmetadaten sind pseudonymisiert. Die Server speichern ihre Teilnahmen unabhängig voneinander; ein gleicher Softwarestand synchronisiert keine Antworten.

Methodische Details: [STUDY-PROTOCOL.md](STUDY-PROTOCOL.md), [V14-METHODS.md](V14-METHODS.md). Fragebogen: [QUESTIONNAIRE.md](QUESTIONNAIRE.md). Werkzeuge: [research/v14/README.md](research/v14/README.md).
