# DIANA – Fragebogen V14

Stand: 23. September 2026. Maßgebliche Definition: `survey_definition_v14.json`; Experiment `diana-abc-v7`.

Der Fragebogen untersucht den wahrgenommenen Nutzen, Kontrolle, Nachvollziehbarkeit, Vertrauen und das Erleben des Dialogs. Hauptvergleich ist selbst gestaltbare Beratung C gegenüber festem Top-Berufsberater B; B gegenüber A ist ein Paketvergleich.

Die Fragen nennen das System statt der Marke DIANA. Das Wiederverwendungsitem lautet „So ein System werde ich bei einer weiteren Jobsuche wieder nutzen.“ Die Wiederholungsfrage und die Frage nach selbst veränderten KI-Einstellungen werden nicht mehr gestellt; historische Antworten bleiben auswertbar.

**Umfang:** A/B/C jeweils 26 sichtbare Fragen, inklusive zwei freiwilliger Textfelder. Automatische Gruppenzuteilung zählt nicht mit. Davon 20 Bewertungsaussagen (einschließlich der separaten Kontrollvariable zur Verfügbarkeit), alle mit 1–7 plus „Kann ich nicht beurteilen“.

**Antwortskala:** 1 Stimme überhaupt nicht zu; 2 Stimme nicht zu; 3 Stimme eher nicht zu; 4 Weder noch; 5 Stimme eher zu; 6 Stimme zu; 7 Stimme voll und ganz zu. „Kann ich nicht beurteilen“ ist ein fehlender Messwert, weder 0 noch neutrale Mitte. Pflichtitems können mit dieser Option beantwortet werden.

Es handelt sich um eine deutschsprachige, auf Jobsuche angepasste Auswahl aus [ResQue (Pu, Chen & Hu, 2011)](https://doi.org/10.1145/2043932.2043962) und [CRS-Que (Jin et al., 2024)](https://doi.org/10.1145/3631534), ergänzt um eigene Studienitems. Auswahl, Übersetzung, siebenstufige Harmonisierung und neue Trust-Zweiergruppe sind **keine bereits validierte deutsche Gesamtskala**. Quellenabgleich und Grenzen: `V14-METHODS.md`.

Die laufende Reihenfolge unten entspricht der Revision `diana-v14-corpus-aware-2026-09-23`.

| Nr. | Datenfeld | Wortlaut | Antwortformat | Typ / Herkunft |
| --- | --- | --- | --- | --- |
| 1 | `education` | Was beschreibt deine aktuelle Situation am besten? | Bachelorstudium / Masterstudium / Anderes Studium / Promotion / Schule oder Ausbildung / Aktuell nicht im Studium oder in Ausbildung / Keine Angabe | context · DIANA |
| 2 | `study_field` | Was ist deine Studien- oder Fachrichtung? | Freitext (freiwillig) | context · DIANA |
| 3 | `job_portal_experience` | Wie häufig hast du in den letzten sechs Monaten Online-Jobportale genutzt? | Nie / Seltener als einmal pro Woche / Mindestens wöchentlich, aber nicht täglich / Täglich / Keine Angabe | context · DIANA |
| 4 | `ai_chat_experience` | Wie häufig hast du in den letzten sechs Monaten KI-Chatbots genutzt? | Nie / Seltener als einmal pro Woche / Mindestens wöchentlich, aber nicht täglich / Täglich / Keine Angabe | context · DIANA |
| 5 | `search_goal` | Wonach hast du mit dem System gesucht? | Freitext | context · DIANA |
| 6 | `catalog_availability` | Für mein Anliegen gab es im System grundsätzlich passende Stellenangebote. | 1–7 + nicht beurteilbar | control_variable · DIANA |
| 7 | `usefulness_ideal` | Das System hat mir geholfen, unter den verfügbaren Angeboten die für mich relevantesten Stellen zu finden. | 1–7 + nicht beurteilbar | multi_item · ResQue |
| 8 | `usefulness_find_easy` | Mit dem System war es einfach, meine Suche einzugrenzen und relevante Stellen zu sichten. | 1–7 + nicht beurteilbar | multi_item · ResQue |
| 9 | `usefulness_suggestions` | Das System hat aus dem verfügbaren Angebot die bestmöglichen Vorschläge gemacht. | 1–7 + nicht beurteilbar | multi_item · ResQue |
| 10 | `trust_fit` | Ich vertraue der Einschätzung des Systems, welche der verfügbaren Stellen am besten zu mir passen. | 1–7 + nicht beurteilbar | multi_item · ResQue / CRS-Que (angelehnt) |
| 11 | `trust_credibility` | Die Einschätzungen des Systems zur Passung der gefundenen Stellen erschienen mir glaubwürdig. | 1–7 + nicht beurteilbar | multi_item · ResQue / CRS-Que (angelehnt) |
| 12 | `dialogue_understanding` | Ich hatte den Eindruck, dass der Chatbot verstand, was ich wollte. | 1–7 + nicht beurteilbar | single_item · CRS-Que |
| 13 | `dialogue_response_quality` | Die Antworten des Chatbots ergaben für mich Sinn. | 1–7 + nicht beurteilbar | single_item · CRS-Que |
| 14 | `dialogue_attentiveness` | Der Chatbot schenkte meinen Aussagen Aufmerksamkeit. | 1–7 + nicht beurteilbar | single_item · CRS-Que |
| 15 | `perceived_character` | Die Beratung im Chat hatte für mich einen erkennbaren eigenen Charakter (z. B. Tonfall, Persönlichkeit). | 1–7 + nicht beurteilbar | single_item · DIANA |
| 16 | `control_preferences` | Ich hatte die Kontrolle darüber, meine Suchwünsche im Chat zu verändern. | 1–7 + nicht beurteilbar | multi_item · CRS-Que |
| 17 | `control_recommendations` | Ich konnte beeinflussen, welche Empfehlungen der Chatbot mir gab. | 1–7 + nicht beurteilbar | multi_item · CRS-Que |
| 18 | `control_adjustment` | Ich hatte die Kontrolle darüber, die Empfehlungen an meine Wünsche anzupassen. | 1–7 + nicht beurteilbar | multi_item · CRS-Que |
| 19 | `transparency_why` | Ich habe verstanden, warum mir die Stellen empfohlen wurden. | 1–7 + nicht beurteilbar | multi_item · CRS-Que |
| 20 | `transparency_assessment` | Ich habe verstanden, wie das System die Eignung der Stellen beurteilt hat. | 1–7 + nicht beurteilbar | multi_item · CRS-Que |
| 21 | `transparency_fit` | Ich habe verstanden, wie gut die Empfehlungen zu meinen Wünschen passten. | 1–7 + nicht beurteilbar | multi_item · CRS-Que |
| 22 | `overall_satisfaction` | Insgesamt bin ich mit dem System zufrieden. | 1–7 + nicht beurteilbar | single_item · ResQue |
| 23 | `intention_reuse` | So ein System werde ich bei einer weiteren Jobsuche wieder nutzen. | 1–7 + nicht beurteilbar | single_item · ResQue |
| 24 | `study_effort` | Die Nutzung des Systems war für mich aufwendig. | 1–7 + nicht beurteilbar | single_item · DIANA |
| 25 | `study_style_control` | Ich konnte den Sprachstil der Beratung an meine persönlichen Vorstellungen anpassen. | 1–7 + nicht beurteilbar | single_item · DIANA |
| 26 | `feedback` | Was hat dir bei deiner Suche geholfen, und was hat dir gefehlt? | Freitext (freiwillig) | single_item · DIANA |

## Auswertung und Interpretation

Nutzen, Kontrolle und Nachvollziehbarkeit: jeweils Mittelwert nur bei drei gültigen numerischen Antworten. Vertrauen: Mittelwert nur bei beiden gültigen Antworten. Fehlendes wird nicht imputiert; keine Umpolung des Aufwanditems und kein Gesamtwert über alle Konstrukte. Das Codebuch benennt Einzelitems, Mehrfachitems, Quellen und Anpassungen explizit.

M1 prüft den wahrgenommenen Charakter in allen Gruppen. Fehlende Evidenz für einen Unterschied ist kein Beleg, dass Personalisierung unwirksam ist, und kein individuelles Ausschlusskriterium. Historische S0-Antworten können separat betrachtet werden; bei neuen Teilnahmen wird die frühere Teilnahme nicht mehr abgefragt und darf nicht als „Nein“ interpretiert werden. Die Frage zur selbst vorgenommenen Änderung der KI-Einstellungen wird nicht mehr gestellt. Vorhandene historische Antworten bleiben erhalten; neue Teilnahmen benötigen keine Antwort darauf.

Pretest und Hauptstudie werden bei Einwilligung getrennt zugeordnet. Alte V13-Antworten bleiben historisch erhalten und werden nicht mit V14 zusammengeführt. Alle Rohwerte inklusive M1/T1/T2 erscheinen mit eindeutigen Spaltennamen und Antwortstatus im Export.

Der festgelegte Analyseumfang und noch offene Festlegungen stehen in `STUDY-PROTOCOL.md`; ausführbare Auswertung und unabhängige Rater-Werkzeuge unter `research/v14/`.

## Korpusbezogene Anpassung vom 23. September 2026

Die drei Nutzen- und zwei Vertrauensaussagen beziehen sich nun auf verfügbare Angebote bzw. den Suchprozess. Das ist eine eigenständige weitere Adaption, keine wortgetreue oder neu validierte ResQue-/CRS-Que-Skala. `catalog_availability` wird als einzelne Kontrollvariable separat dargestellt und exportiert. Es fließt weder in die Mittelwerte noch in Cronbach-α ein. Die Konstruktzuordnung der übrigen Items bleibt unverändert. Frühere Antworten werden nicht umgeschrieben; bei Vergleichen sind die unterschiedlichen Wortlaute anhand der System-Releases zu berücksichtigen.
