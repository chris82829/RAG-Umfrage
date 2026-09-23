# DIANA – Fragebogen V14

Stand: 23. September 2026. Maßgebliche Definition: `survey_definition_v14.json`; Experiment `diana-abc-v7`.

Der Fragebogen untersucht den wahrgenommenen Nutzen, Kontrolle, Nachvollziehbarkeit, Vertrauen und das Erleben des Dialogs. Hauptvergleich ist selbst gestaltbare Beratung C gegenüber festem Top-Berufsberater B; B gegenüber A ist ein Paketvergleich.

Die Fragen nennen das System statt der Marke DIANA. Das Wiederverwendungsitem lautet „So ein System werde ich bei einer weiteren Jobsuche wieder nutzen.“ Die Wiederholungsfrage und die Frage nach selbst veränderten KI-Einstellungen werden nicht mehr gestellt; historische Antworten bleiben auswertbar.

**Umfang:** A/B/C jeweils 25 sichtbare Fragen, inklusive zwei freiwilliger Textfelder. Automatische Gruppenzuteilung zählt nicht mit. Davon 19 Bewertungsaussagen, alle mit 1–7 plus „Kann ich nicht beurteilen“.

**Antwortskala:** 1 Stimme überhaupt nicht zu; 2 Stimme nicht zu; 3 Stimme eher nicht zu; 4 Weder noch; 5 Stimme eher zu; 6 Stimme zu; 7 Stimme voll und ganz zu. „Kann ich nicht beurteilen“ ist ein fehlender Messwert, weder 0 noch neutrale Mitte. Pflichtitems können mit dieser Option beantwortet werden.

Es handelt sich um eine deutschsprachige, auf Jobsuche angepasste Auswahl aus [ResQue (Pu, Chen & Hu, 2011)](https://doi.org/10.1145/2043932.2043962) und [CRS-Que (Jin et al., 2024)](https://doi.org/10.1145/3631534), ergänzt um eigene Studienitems. Auswahl, Übersetzung, siebenstufige Harmonisierung und neue Trust-Zweiergruppe sind **keine bereits validierte deutsche Gesamtskala**. Quellenabgleich und Grenzen: `V14-METHODS.md`.

Die Referenznummern erhalten die V13-Zuordnung; T1/T2/M1 sind ergänzte Einschübe. Die laufende Reihenfolge unten entspricht V14.

| Nr. | Referenz | Datenfeld | Wortlaut | Antwortformat | Typ / Herkunft |
| --- | --- | --- | --- | --- | --- |
| 1 | 1 | `education` | Was beschreibt deine aktuelle Situation am besten? | Bachelorstudium / Masterstudium / Anderes Studium / Promotion / Schule oder Ausbildung / Aktuell nicht im Studium oder in Ausbildung / Keine Angabe | context · DIANA |
| 2 | 2 | `study_field` | Was ist deine Studien- oder Fachrichtung? | Freitext (freiwillig) | context · DIANA |
| 3 | 3 | `job_portal_experience` | Wie häufig hast du in den letzten sechs Monaten Online-Jobportale genutzt? | Nie / Seltener als einmal pro Woche / Mindestens wöchentlich, aber nicht täglich / Täglich / Keine Angabe | context · DIANA |
| 4 | 4 | `ai_chat_experience` | Wie häufig hast du in den letzten sechs Monaten KI-Chatbots genutzt? | Nie / Seltener als einmal pro Woche / Mindestens wöchentlich, aber nicht täglich / Täglich / Keine Angabe | context · DIANA |
| 5 | 5 | `search_goal` | Wonach hast du mit dem System gesucht? | Freitext | context · DIANA |
| 6 | 6 | `usefulness_ideal` | Das System hat mir geholfen, die ideale Stelle für mein Suchvorhaben zu finden. | 1–7 + nicht beurteilbar | multi_item · ResQue |
| 7 | 7 | `usefulness_find_easy` | Mit dem System war es einfach, Stellen zu finden, die mir gefallen. | 1–7 + nicht beurteilbar | multi_item · ResQue |
| 8 | 8 | `usefulness_suggestions` | Das System hat mir gute Vorschläge gemacht. | 1–7 + nicht beurteilbar | multi_item · ResQue |
| 9 | T1 | `trust_fit` | Ich vertraue darauf, dass die vom System vorgeschlagenen Stellen wirklich zu mir passen. | 1–7 + nicht beurteilbar | multi_item · ResQue / CRS-Que (angelehnt) |
| 10 | T2 | `trust_credibility` | Die Einschätzungen des Systems zur Passung erschienen mir glaubwürdig. | 1–7 + nicht beurteilbar | multi_item · ResQue / CRS-Que (angelehnt) |
| 11 | 9 | `dialogue_understanding` | Ich hatte den Eindruck, dass der Chatbot verstand, was ich wollte. | 1–7 + nicht beurteilbar | single_item · CRS-Que |
| 12 | 10 | `dialogue_response_quality` | Die meisten Antworten des Chatbots ergaben für mich Sinn. | 1–7 + nicht beurteilbar | single_item · CRS-Que |
| 13 | 11 | `dialogue_attentiveness` | Der Chatbot schenkte meinen Aussagen Aufmerksamkeit. | 1–7 + nicht beurteilbar | single_item · CRS-Que |
| 14 | M1 | `perceived_character` | Die Beratung im Chat hatte für mich einen erkennbaren eigenen Charakter (z. B. Tonfall, Persönlichkeit). | 1–7 + nicht beurteilbar | single_item · DIANA |
| 15 | 12 | `control_preferences` | Ich hatte die Kontrolle darüber, meine Suchwünsche im Chat zu verändern. | 1–7 + nicht beurteilbar | multi_item · CRS-Que |
| 16 | 13 | `control_recommendations` | Ich konnte beeinflussen, welche Empfehlungen der Chatbot mir gab. | 1–7 + nicht beurteilbar | multi_item · CRS-Que |
| 17 | 14 | `control_adjustment` | Ich hatte die Kontrolle darüber, die Empfehlungen an meine Wünsche anzupassen. | 1–7 + nicht beurteilbar | multi_item · CRS-Que |
| 18 | 15 | `transparency_why` | Ich habe verstanden, warum mir die Stellen empfohlen wurden. | 1–7 + nicht beurteilbar | multi_item · CRS-Que |
| 19 | 16 | `transparency_assessment` | Ich habe verstanden, wie das System die Eignung der Stellen beurteilt hat. | 1–7 + nicht beurteilbar | multi_item · CRS-Que |
| 20 | 17 | `transparency_fit` | Ich habe verstanden, wie gut die Empfehlungen zu meinen Wünschen passten. | 1–7 + nicht beurteilbar | multi_item · CRS-Que |
| 21 | 18 | `overall_satisfaction` | Insgesamt bin ich mit dem System zufrieden. | 1–7 + nicht beurteilbar | single_item · ResQue |
| 22 | 19 | `intention_reuse` | So ein System werde ich bei einer weiteren Jobsuche wieder nutzen. | 1–7 + nicht beurteilbar | single_item · ResQue |
| 23 | 20 | `study_effort` | Die Nutzung des Systems war für mich aufwendig. | 1–7 + nicht beurteilbar | single_item · DIANA |
| 24 | 21 | `study_style_control` | Ich konnte den Sprachstil der Beratung an meine persönlichen Vorstellungen anpassen. | 1–7 + nicht beurteilbar | single_item · DIANA |
| 25 | 22 | `feedback` | Was hat dir bei deiner Suche geholfen, und was hat dir gefehlt? | Freitext (freiwillig) | single_item · DIANA |

## Auswertung und Interpretation

Nutzen, Kontrolle und Nachvollziehbarkeit: jeweils Mittelwert nur bei drei gültigen numerischen Antworten. Vertrauen: Mittelwert nur bei beiden gültigen Antworten. Fehlendes wird nicht imputiert; keine Umpolung des Aufwanditems und kein Gesamtwert über alle Konstrukte. Das Codebuch benennt Einzelitems, Mehrfachitems, Quellen und Anpassungen explizit.

M1 prüft den wahrgenommenen Charakter in allen Gruppen. Fehlende Evidenz für einen Unterschied ist kein Beleg, dass Personalisierung unwirksam ist, und kein individuelles Ausschlusskriterium. Historische S0-Antworten können separat betrachtet werden; bei neuen Teilnahmen wird die frühere Teilnahme nicht mehr abgefragt und darf nicht als „Nein“ interpretiert werden. Die Frage zur selbst vorgenommenen Änderung der KI-Einstellungen wird nicht mehr gestellt. Vorhandene historische Antworten bleiben erhalten; neue Teilnahmen benötigen keine Antwort darauf.

Pretest und Hauptstudie werden bei Einwilligung getrennt zugeordnet. Alte V13-Antworten bleiben historisch erhalten und werden nicht mit V14 zusammengeführt. Alle Rohwerte inklusive M1/T1/T2 erscheinen mit eindeutigen Spaltennamen und Antwortstatus im Export.

Der festgelegte Analyseumfang und noch offene Festlegungen stehen in `STUDY-PROTOCOL.md`; ausführbare Auswertung und unabhängige Rater-Werkzeuge unter `research/v14/`.
