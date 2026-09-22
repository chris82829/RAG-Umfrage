# DIANA – Fragebogen V14

Stand: 22. September 2026. Maßgebliche Definition: `survey_definition_v14.json`; Experiment `diana-abc-v7`.

Der Fragebogen untersucht den wahrgenommenen Nutzen, Kontrolle, Nachvollziehbarkeit, Vertrauen und das Erleben des Dialogs. Hauptvergleich ist selbst gestaltbare Beratung C gegenüber festem Top-Berufsberater B; B gegenüber A ist ein Paketvergleich.

Die bisherigen **14 Framework-Items und zwei eigenen Bewertungsitems bleiben im Wortlaut unverändert**. Neu sind eine eigenständig angelehnte Vertrauens-Zweiergruppe T1/T2, ein eigener Manipulationscheck M1 und die Wiederholungsfrage S0. Das optionale zusätzliche Bedienungsitem wurde zugunsten einer kürzeren Befragung nicht aufgenommen.

**Umfang:** A/B 26, C 27 sichtbare Fragen, inklusive zwei freiwilliger Textfelder. Automatische Gruppenzuteilung zählt nicht mit. Davon 19 Bewertungsaussagen, alle mit 1–7 plus „Kann ich nicht beurteilen“. Die im Vorschlag genannte Zahl 25/26 berücksichtigte die zusätzliche Screeningfrage noch nicht.

**Antwortskala:** 1 Stimme überhaupt nicht zu; 2 Stimme nicht zu; 3 Stimme eher nicht zu; 4 Weder noch; 5 Stimme eher zu; 6 Stimme zu; 7 Stimme voll und ganz zu. „Kann ich nicht beurteilen“ ist ein fehlender Messwert, weder 0 noch neutrale Mitte. Pflichtitems können mit dieser Option beantwortet werden.

Es handelt sich um eine deutschsprachige, auf Jobsuche angepasste Auswahl aus [ResQue (Pu, Chen & Hu, 2011)](https://doi.org/10.1145/2043932.2043962) und [CRS-Que (Jin et al., 2024)](https://doi.org/10.1145/3631534), ergänzt um eigene Studienitems. Auswahl, Übersetzung, siebenstufige Harmonisierung und neue Trust-Zweiergruppe sind **keine bereits validierte deutsche Gesamtskala**. Quellenabgleich und Grenzen: `V14-METHODS.md`.

Die Referenznummern erhalten die V13-Zuordnung; S0/T1/T2/M1 sind neue Einschübe. Die laufende Reihenfolge unten entspricht V14.

| Nr. | Referenz | Datenfeld | Wortlaut | Antwortformat | Typ / Herkunft |
| --- | --- | --- | --- | --- | --- |
| 1 | S0 | `previous_participation` | Hast du bereits einmal an dieser Studie teilgenommen? | Ja / Nein / Unsicher | screening · DIANA |
| 2 | 1 | `education` | Was beschreibt deine aktuelle Situation am besten? | Bachelorstudium / Masterstudium / Anderes Studium / Promotion / Schule oder Ausbildung / Aktuell nicht im Studium oder in Ausbildung / Keine Angabe | context · DIANA |
| 3 | 2 | `study_field` | Was ist deine Studien- oder Fachrichtung? | Freitext (freiwillig) | context · DIANA |
| 4 | 3 | `job_portal_experience` | Wie häufig hast du in den letzten sechs Monaten Online-Jobportale genutzt? | Nie / Seltener als einmal pro Woche / Mindestens wöchentlich, aber nicht täglich / Täglich / Keine Angabe | context · DIANA |
| 5 | 4 | `ai_chat_experience` | Wie häufig hast du in den letzten sechs Monaten KI-Chatbots genutzt? | Nie / Seltener als einmal pro Woche / Mindestens wöchentlich, aber nicht täglich / Täglich / Keine Angabe | context · DIANA |
| 6 | 5 | `search_goal` | Wonach hast du mit DIANA gesucht? | Freitext | context · DIANA |
| 7 | 6 | `usefulness_ideal` | DIANA hat mir geholfen, die ideale Stelle für mein Suchvorhaben zu finden. | 1–7 + nicht beurteilbar | multi_item · ResQue |
| 8 | 7 | `usefulness_find_easy` | Mit DIANA war es einfach, Stellen zu finden, die mir gefallen. | 1–7 + nicht beurteilbar | multi_item · ResQue |
| 9 | 8 | `usefulness_suggestions` | DIANA hat mir gute Vorschläge gemacht. | 1–7 + nicht beurteilbar | multi_item · ResQue |
| 10 | T1 | `trust_fit` | Ich vertraue darauf, dass die von DIANA vorgeschlagenen Stellen wirklich zu mir passen. | 1–7 + nicht beurteilbar | multi_item · ResQue / CRS-Que (angelehnt) |
| 11 | T2 | `trust_credibility` | Die Einschätzungen von DIANA zur Passung erschienen mir glaubwürdig. | 1–7 + nicht beurteilbar | multi_item · ResQue / CRS-Que (angelehnt) |
| 12 | 9 | `dialogue_understanding` | Ich hatte den Eindruck, dass der Chatbot verstand, was ich wollte. | 1–7 + nicht beurteilbar | single_item · CRS-Que |
| 13 | 10 | `dialogue_response_quality` | Die meisten Antworten des Chatbots ergaben für mich Sinn. | 1–7 + nicht beurteilbar | single_item · CRS-Que |
| 14 | 11 | `dialogue_attentiveness` | Der Chatbot schenkte meinen Aussagen Aufmerksamkeit. | 1–7 + nicht beurteilbar | single_item · CRS-Que |
| 15 | M1 | `perceived_character` | Die Beratung im Chat hatte für mich einen erkennbaren eigenen Charakter (z. B. Tonfall, Persönlichkeit). | 1–7 + nicht beurteilbar | single_item · DIANA |
| 16 | 12 | `control_preferences` | Ich hatte die Kontrolle darüber, meine Suchwünsche im Chat zu verändern. | 1–7 + nicht beurteilbar | multi_item · CRS-Que |
| 17 | 13 | `control_recommendations` | Ich konnte beeinflussen, welche Empfehlungen der Chatbot mir gab. | 1–7 + nicht beurteilbar | multi_item · CRS-Que |
| 18 | 14 | `control_adjustment` | Ich hatte die Kontrolle darüber, die Empfehlungen an meine Wünsche anzupassen. | 1–7 + nicht beurteilbar | multi_item · CRS-Que |
| 19 | 15 | `transparency_why` | Ich habe verstanden, warum mir die Stellen empfohlen wurden. | 1–7 + nicht beurteilbar | multi_item · CRS-Que |
| 20 | 16 | `transparency_assessment` | Ich habe verstanden, wie DIANA die Eignung der Stellen beurteilt hat. | 1–7 + nicht beurteilbar | multi_item · CRS-Que |
| 21 | 17 | `transparency_fit` | Ich habe verstanden, wie gut die Empfehlungen zu meinen Wünschen passten. | 1–7 + nicht beurteilbar | multi_item · CRS-Que |
| 22 | 18 | `overall_satisfaction` | Insgesamt bin ich mit DIANA zufrieden. | 1–7 + nicht beurteilbar | single_item · ResQue |
| 23 | 19 | `intention_reuse` | Ich werde DIANA bei einer weiteren Jobsuche wieder nutzen. | 1–7 + nicht beurteilbar | single_item · ResQue |
| 24 | 20 | `study_effort` | Die Nutzung von DIANA war für mich aufwendig. | 1–7 + nicht beurteilbar | single_item · DIANA |
| 25 | 21 | `study_style_control` | Ich konnte den Sprachstil der Beratung an meine persönlichen Vorstellungen anpassen. | 1–7 + nicht beurteilbar | single_item · DIANA |
| 26 | 22 | `personality_customized` | Hast du die angebotenen Einstellungen der KI-Beratung selbst verändert? | Ja / Nein; nur C | single_item · DIANA |
| 27 | 23 | `feedback` | Was hat dir bei deiner Suche geholfen, und was hat dir gefehlt? | Freitext (freiwillig) | single_item · DIANA |

## Auswertung und Interpretation

Nutzen, Kontrolle und Nachvollziehbarkeit: jeweils Mittelwert nur bei drei gültigen numerischen Antworten. Vertrauen: Mittelwert nur bei beiden gültigen Antworten. Fehlendes wird nicht imputiert; keine Umpolung des Aufwanditems und kein Gesamtwert über alle Konstrukte. Das Codebuch benennt Einzelitems, Mehrfachitems, Quellen und Anpassungen explizit.

M1 prüft den wahrgenommenen Charakter in allen Gruppen. Fehlende Evidenz für einen Unterschied ist kein Beleg, dass Personalisierung unwirksam ist, und kein individuelles Ausschlusskriterium. S0 (Ja/Nein/Unsicher) ermöglicht eine Sensitivitätsanalyse; die Hauptanalyse behält Wiederholungs-Selbstauskünfte bei, die zusätzliche Analyse schließt „Ja“ aus. „Unsicher“ bleibt gesondert dokumentiert. C berichtet die eigene Anpassung nur selbst; diese Untergruppen sind nicht randomisiert.

Pretest und Hauptstudie werden bei Einwilligung getrennt zugeordnet. Alte V13-Antworten bleiben historisch erhalten und werden nicht mit V14 zusammengeführt. Alle Rohwerte inklusive M1/T1/T2 erscheinen mit eindeutigen Spaltennamen und Antwortstatus im Export.

Der festgelegte Analyseumfang und noch offene Festlegungen stehen in `STUDY-PROTOCOL.md`; ausführbare Auswertung und unabhängige Rater-Werkzeuge unter `research/v14/`.
