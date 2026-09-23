# DIANA – Prüfung vor dem Studienversand, 23. September 2026

## Zweck und Prüfstand

Vorabprüfung des öffentlichen Studienservers und des aktuellen Codes vor der Einladung von Studierenden. Ausgangscommit: `a93a3c1ea771edc5db03cd059a854a3ebe972fe9`. Während der Prüfung gefundene Fehler und anschließende Korrekturen werden nicht als bereits erfolgreich ausgerollt vorausgesetzt. Dieser Bericht ist weder eine institutionelle Datenschutzfreigabe noch eine Präregistrierung oder ein Nachweis der Kapazität für 400 gleichzeitige Personen.

Geprüfte öffentliche Instanz: `https://159.195.48.19/`, Teilnehmerroute `/umfrage`. Die Hochschulinstallation ist eine getrennte Instanz mit eigener Datenbank und gehört nicht zum hier belegten Versandziel. In dieser Prüfung wurden keine neuen Live-Umfrageteilnahmen erzeugt und keine kostenpflichtigen Modellaufrufe für einen Lasttest gestartet. Synthetische Testdaten wurden nur in temporären lokalen Datenbanken verwendet.

## Reproduzierbare Prüfungen der Studienlogik

Ausgeführt aus dem Repository mit `/tmp/diana-v14-analysis-runtime/bin/python`:

```text
-m pytest -q test_study_progress_v12.py test_survey_chat_limit.py \
  test_study_telemetry.py test_telemetry_analytics.py test_v14_analysis.py \
  test_study_versioning.py test_survey_v13.py
107 passed, 148 subtests passed in 12.98s

-m pytest -q test_v14_metadata.py test_v14_integration.py test_prompt_exposure.py
25 passed, 13 subtests passed in 3.23s
```

Die zwei Läufe enthalten insgesamt 132 bestandene Tests und 161 bestandene Subtests. Geerbte Tests werden teilweise in mehreren Testklassen ausgeführt; die Anzahl ist kein Maß für unabhängige Nutzerfälle.

Zusätzlicher manueller Offline-Test mit dem Flask-Testclient, echter SQLite-Speicherung, 10 Threads und 40 gleichzeitigen Zuteilungsrequests für dieselbe Einwilligung: 40 Antworten mit HTTP 200 und derselben Gruppe, genau eine Zeile in `study_assignments`. Die sichtbaren aktuellen Felder wurden mit `SURVEY_FIELDS` und `field_visible` gezählt: A = 26, B = 26, C = 26, ohne automatische Gruppenzuteilung.

| Gegenstand | Aktiv geprüfter Befund | Nachweis |
| --- | --- | --- |
| A/B/C-Zuteilung | Neue Einwilligungen erhalten mit gleicher Wahrscheinlichkeit eine Gruppe; bestehende Zuordnung bleibt bestehen. Gleichzeitige Requests erzeugen keine unterschiedlichen Zuordnungen. Exakt gleiche Gruppengrößen sind nicht garantiert. | `study_assignment.py`, manueller Konkurrenztest oben |
| Drei Chatnachrichten | Direkter Übergangsrequest und direkte Ergebnisabgabe mit 0–2 erfolgreichen Nachrichten werden mit 403 verweigert; nach drei erfolgreichen Nachrichten werden sie zugelassen. Fehler und automatische Begrüßungen zählen nicht. | `test_study_progress_v12.py::StudyProgressTests::test_proceed_and_direct_submission_require_three_successful_exchanges`, `test_survey_chat_limit.py` |
| Testseiten | Eigene Einwilligungszwecke; unbegrenztes Chatten ohne Studienoperationen. Ein gefälschter Testheader umgeht keine Studienberechtigung. | `test_survey_chat_limit.py`, `test_study_telemetry.py` |
| Fragebogen | 26 sichtbare Fragen pro Gruppe, davon 20 Ratings; aktuelle Version `diana-v14`. „Kann ich nicht beurteilen“ bleibt fehlend, nicht null oder Skalenmitte. | `survey_definition_v14.json`, `QUESTIONNAIRE.md`, `test_v14_analysis.py` |
| Metadaten | Zeiten sichtbarer Begründungen, Öffnen von Stellen und serverseitig gezählte erfolgreiche Chatnachrichten werden getrennt erfasst. Ereignis-ID verhindert Duplikate bei Wiederholung. | `study_telemetry.py`, `test_study_telemetry.py` |
| Verwaltung/Exporte | Nutzungsverhalten, CSV-Ereignisse, aggregierte CSV und Analysepaket vorhanden. Berechtigungen, CSRF, Gruppen-/Phasenfilter und Widerruf geprüft. | `test_telemetry_analytics.py`, `test_v14_integration.py` |
| Studienphase | Phase wird bei Beginn gespeichert und später nicht nachträglich umetikettiert. Hypothesentests verwenden Hauptstudienfälle. | `study_context.py`, `test_v14_metadata.py`, `test_v14_integration.py` |
| Analyse | Primärer C–B-Nutzenvergleich, Holm-Familie, Umgang mit fehlenden Werten, Reliabilität und Exporte rechnerisch offline geprüft. Daraus folgt keine Validierung der adaptierten Gesamtskala. | `test_v14_analysis.py` |

## Lokale Abschlussprüfungen der Korrekturen

Die vollständige Python-Suite nach der Korrektur lieferte **343 bestandene Tests und 182 bestandene Subtests in 28,15 Sekunden**. Der neu gefundene C-Abschlussfehler wurde in `survey_store.py` behoben: entfernte (`retired`) Felder gelten nicht mehr als Pflichtfelder. `test_survey_active_fields.py` sichert den Fall zusätzlich ab.

Sechs vollständige Browserabläufe (A/B/C jeweils bei 1440 und 390 Pixel Breite) wurden gegen den lokalen Server mit synthetischen Modellantworten ausgeführt: alle erfolgreich. Die lokale Datenbank enthielt danach sechs abgeschlossene Antworten, sechs Gewinnspiel-Berechtigungsvermerke und 18 erfolgreiche Chatturns sowie Sichtbarkeitsereignisse. In diesen Fällen wurden keine JavaScript-Fehler, HTTP-Fehler oder horizontalen Layoutüberläufe festgestellt. Zusätzlich bestanden sechs Browserfälle für sofortiges Leeren/Wiederherstellen des Nachrichtenfelds sowie sechs Stellenlink-Fälle.

Diese Ergebnisse prüfen die Anwendungslogik und Darstellung mit Offline-Modellantworten. Sie sind kein Nachweis dafür, dass jede Antwort eines live aufgerufenen Sprachmodells das gewünschte Format einhält. Die JavaScript-Regressionssuite bestand mit **72 Tests**, einschließlich Streamingfragmenten, unbekannten IDs, erhaltenen Titelverknüpfungen und unveränderten regulären Zahlen. Der Produktionsbuild war erfolgreich. Sechs weitere A/B/C-Browserfälle (1360/390 Pixel) bestätigen bereinigte bestehende Nutzer- und KI-Nachrichten sowie funktionierende aktuelle und historische Stellenlinks; siehe `chat-id-browser-results.json`. `browser-results.json` enthält die sechs vollständigen Studienabläufe. Mobile Prüfungen verwendeten einen Chromium-Viewport, kein echtes iPhone/Safari.

## Öffentlicher Server: beobachteter Stand

Die folgenden Werte wurden während dieses Prüfturns durch read-only HTTP-/SSH-/SQLite-Abfragen ermittelt. Es wurden keine Zugangsdaten oder personenbezogenen Einzelantworten in den Bericht übernommen.

- Die aktive Studienkonfiguration war Revision 2, angelegt am `2026-09-23T10:41:38.588778Z`, mit `study_wave=pretest` und `recruitment_batch=2026-09-23T10:41:00Z`.
- `/api/privacy` meldete `ready=true`; die produktive Datenschutzkonfiguration enthielt `approved=true`. Dies ist ein technischer Konfigurationszustand, kein unabhängiger Nachweis einer inhaltlichen oder institutionellen Freigabe.
- HTTPS-Zertifikat gültig; Caddy verwaltet das kurzlebige Let's-Encrypt-IP-Zertifikat automatisch.
- SQLite-Prüfung der Studiendatenbank ohne gemeldeten Integritätsfehler. Die tägliche Studiendatenbanksicherung vom Prüfungstag war vorhanden und bestand die Integritätsprüfung.
- Der read-only Test auf dem Indexstatus-Endpunkt umfasste 48 Requests bei Parallelität 12; alle antworteten mit HTTP 200. Dieser Endpunkt führt keine Suche und keine OpenAI-Verarbeitung aus.
- In den betrachteten letzten zwei Stunden waren fünf protokollierte LLM-Requests vorhanden, jeweils beim ersten Versuch erfolgreich geparst. Diese kleine, beobachtete Stichprobe ist kein Zuverlässigkeits- oder Lastnachweis für die gesamte Erhebung.
- Die Gewinnspiel-Anmeldung war aktiv (`enabled=true`) und verwendete die separate E-Mail-Datenbank.

## Gefundene Fehler und ausstehende Freigabepunkte

| Priorität | Punkt | Beleg und erforderliche Klärung |
| --- | --- | --- |
| Lokal behoben; Rollout noch zu verifizieren | C konnte im Browser den Fragebogen nicht abschließen. | Die Abschlussvalidierung verlangte den bereits entfernten Wert `personality_customized`. Der Fehler wurde im Browser gefunden, obwohl vorhandene Backend-Tests bestanden. Validator und neue Regression korrigiert; sechs vollständige A/B/C-Browserabläufe sowie die volle Python-Suite bestanden. Erst nach verifiziertem Rollout auch auf dem öffentlichen Server als erledigt markieren. |
| Vor Versand umstellen | Öffentliche Instanz steht noch auf Pretest. | Live-Konfiguration oben. In Verwaltung → „Studienphase für neue Teilnahmen“ die Hauptstudie mit tatsächlichem Versandzeitpunkt festlegen. Bereits begonnene Pretests nicht nachträglich als Hauptstudie ausgeben. |
| Vor Versand inhaltlich klären | Datenschutzhinweise enthalten einen unerledigten Platzhalter zur OpenAI-Verarbeitung. | In der produktiven Konfiguration trotz `approved=true`: „Die für diese Studie geltenden Empfänger, Verarbeitungsorte und Übermittlungsgrundlagen werden vor der Freigabe ergänzt.“ Derselbe Satz steht in `deploy/netcup/privacy_settings.json`. Tatsächliche Bedingungen/Kontoeinstellungen müssen von der Studienleitung geklärt und korrekt eingetragen werden; nicht erfinden. |
| Lokal korrigiert; gemeinsam ausrollen | Datenschutzhinweise beschrieben entfernte Funktionen. | `privacy.py` wurde sachlich angepasst: Scores und Chat-Stellenlinks nur B/C; keine Behauptung einer erhobenen früheren Teilnahme. Die fehlenden Angaben zur tatsächlichen OpenAI-Verarbeitung bleiben offen. Eine Textänderung erzeugt eine neue Einwilligungsfassung. |
| Vor Bewerbung des Gewinnspiels klären | Gewinne, Teilnahmebedingungen und Anmeldeschluss sind nicht festgelegt. | Die Funktion sammelt Adressen, hat aber keine definierten organisatorischen Angaben oder automatische Auslosung. Die Studienleitung muss diese Angaben festlegen oder die Anmeldung bis dahin schließen. |
| Betrieblich ergänzen | Tägliches Backup umfasst nur die Studiendatenbank. | `deploy/netcup/backup.py` sichert `jobs.sqlite3`, nicht `raffle.sqlite3`. Bei Verlust der E-Mail-Datei können Anmeldungen nicht aus den Forschungsdaten rekonstruiert werden. Getrennte Sicherung samt Lösch-/Aufbewahrungskonzept festlegen. |
| Vor konfirmatorischer Haupterhebung festlegen | Analyseplan ist noch Entwurf. | `research/v14/analysis_plan.json`: `status=draft`; Freeze, Rekrutierungsbeginn/-ende, relevante Effektgröße, Ausfallreserve und geplante gültige Fallzahl fehlen. Vor Erhebung entscheiden und zeitlich nachvollziehbar dokumentieren. Keine rückwirkende Präregistrierung behaupten. |

Der öffentliche Rollout wird getrennt über `/opt/diana-survey/DEPLOYED_COMMIT` und `DEPLOYMENT_MANIFEST.json` (Dateiprüfsummen) belegt. Ein Prüfbericht oder Commit allein beweist keine erfolgreiche Bereitstellung. Die offenen organisatorischen Punkte verhindern weiterhin eine Versandfreigabe.

## Grenzen, die bei Versand und Auswertung bestehen bleiben

**Mehrfachteilnahme:** Der Zugangscode liegt im Sitzungsspeicher des Browsers (`frontend/privacy.js`). Ein neuer unabhängiger Browserkontext kann eine neue Einwilligung und Gruppe erhalten. Es gibt keine verlässliche Einmal-pro-Person-Prüfung. Die entfernte Wiederholungsfrage kann neue Mehrfachteilnahmen nicht mehr erfassen. Die Gewinnspiel-Deduplizierung einer E-Mail-Adresse verhindert keine mehrfachen Forschungsantworten, weil beide Datensätze absichtlich nicht verbunden sind. Einladung daher mindestens mit der Bitte um einmalige Teilnahme formulieren; eine stärkere Absicherung wäre eine eigene Studiendesignentscheidung.

**Untersuchungsgegenstand:** B gegen A ist ein Paketvergleich einschließlich Berufsberater-RAG-Auftrag, Gesprächsinitiative, Score-Darstellung und Stellenlinks. Er isoliert nicht allein Persönlichkeit. C gegen B prüft das Angebot zusätzlicher Selbstgestaltung auf gemeinsamer fachlicher Grundlage. Gleiche Gewichte und Retrievalverfahren garantieren keine identischen generativen Bewertungen oder Ergebnisreihenfolgen. Diese Einordnung muss in Forschungsfrage, Hypothesen und Paper konsistent bleiben.

**Fragebogen:** Es handelt sich um eine dokumentierte deutschsprachige, teilweise umformulierte Auswahl nach ResQue und CRS-Que mit eigenen Ergänzungen. Erfolgreiche Softwaretests sind kein kognitiver Pretest und keine psychometrische Validierung. Die Anzahl beträgt aktuell in allen Gruppen 26; ältere Angaben im README/Protokoll wurden in dieser Prüfung berichtigt.

**Last und APIs:** 400 erwartete Teilnahmen insgesamt sind nicht 400 gleichzeitige Anfragen. Nicht geprüft wurden 400 parallele Suchen, OpenAI-Rate-Limits unter einer Versandspitze oder reale Kosten bei einem solchen Lastprofil. Ein leichter HTTP-Test und freie Serverressourcen belegen diese Kapazität nicht. Die Einladungswelle und Beobachtung von Fehlern/Wartezeiten müssen diese Grenze berücksichtigen.

**Telemetrie:** Erfasst wird Sichtbarkeit, nicht tatsächliches Lesen. Mehrere gleichzeitig sichtbare Stellenkarten liefern überlappende Zeiten. Browserereignisse sind best-effort und können bei Unterbrechungen fehlen. Fehlende Messung wird nicht als null Sekunden interpretiert. Historische Stellen aus früheren Suchergebnissen sind keine aktuelle Rangpositions-Exposition.

**Datentrennung:** Studienantworten und Metadaten sind pseudonym verknüpfbar. Separat erfasste Gewinnspieladressen haben keinen direkten Datenbankschlüssel zu den Antworten; diese Trennung ist keine pauschale Garantie vollständiger Anonymität. Dieselbe Serverinstanz verarbeitet beide Anfragen. Löschung von Forschungsdaten entfernt absichtlich keine unzuordenbare E-Mail-Adresse; der gesonderte Löschweg muss verständlich bleiben.
