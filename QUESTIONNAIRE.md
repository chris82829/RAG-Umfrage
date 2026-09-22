# DIANA-Fragebogen V13

Verbindliche Definition: [survey_definition_v13.json](survey_definition_v13.json), Version `diana-v13`. In Studie und Verwaltung wird ausschließlich dieser Fragebogen verwendet.

## Forschungsfrage und Vergleich

Primär wird **C gegen B** verglichen: Welchen zusätzlichen wahrgenommenen Nutzen bietet eine selbst gestaltbare Gesprächspersönlichkeit gegenüber dem festen Top-Berufsberater, und welcher zusätzliche Nutzungsaufwand entsteht? Sekundär wird **B gegen A** als Vergleich des Beratungspakets mit dem Basissystem untersucht. Die Zuweisung bleibt die Grundlage des Gruppenvergleichs; Teilnehmende aus C, die nichts verändern, werden nicht nachträglich B zugeordnet. Die C-Zusatzfrage unterstützt eine getrennte explorative Untersuchung der tatsächlichen Gestaltung.

Es gibt **keine gleichzeitig randomisierte Gruppe mit klassischer Filter- und Stichwortsuche**. Die frühere Umfrage zu klassischen Jobportalen liefert Kontext, aber keinen gleichwertigen experimentellen Kontrollarm. Die Antworten messen subjektive Wahrnehmungen; sie belegen weder objektive Rankingqualität noch tatsächlichen Bewerbungserfolg. Zusätzliche Telemetrie beschreibt Nutzung und ersetzt diese Qualitätsprüfung nicht.

## Quellen und Anpassungen

- **R – ResQue:** Pu, Chen & Hu (2011), *A User-Centric Evaluation Framework for Recommender Systems*. [DOI](https://doi.org/10.1145/2043932.2043962), [Autorenfassung](https://www.comp.hkbu.edu.hk/~lichen/download/p157-pu.pdf). Tabelle 2, S. 161; Kurzfassung in Abschnitt 5.1, S. 163. Ursprünglich fünf Antwortstufen.
- **C – CRS-Que:** Jin, Chen, Cai & Zhao (2024), *CRS-Que: A User-centric Evaluation Framework for Conversational Recommender Systems*. [DOI](https://doi.org/10.1145/3631534), [Autorenfassung](https://yucheng.gold/file/tors23.pdf). Tabelle 4, S. 2:20; Kurzform Tabelle 5, S. 2:27; Anwendungshinweise Abschnitt 5.3, S. 2:23. Ursprünglich sieben Antwortstufen.

Die Auswahl kombiniert **14 Framework-Items** mit eigenen Studienfragen. Drei vollständige Skalen erfassen Nutzen, Kontrolle und Nachvollziehbarkeit; einzelne Dialogmerkmale, Zufriedenheit und Wiederverwendungsabsicht ergänzen sie. So werden die vier Dimensionen der Frameworks berücksichtigt, ohne Bedienoberfläche, Vermenschlichung oder Kaufabsichten umfassend abzufragen.

Dies ist eine **deutsche, auf Jobsuche angepasste Auswahl**, keine vollständig übernommene oder bereits validierte deutsche Gesamtskala. Auch die Vereinheitlichung der ResQue-Antworten von fünf auf sieben Stufen sowie die zusätzliche Nichtbeurteilbar-Antwort sind Anpassungen. Kognitive Pretests, Prüfung der Übersetzung und empirische Prüfung von Reliabilität/Faktorstruktur der Dreier-Skalen stehen noch aus. Einzelitems erlauben keine interne Reliabilitätsschätzung. Die Quellenpositionen unten sind lokale Fundstellen, keine offiziellen Item-IDs.

## Antwortformat und Umfang

Alle 16 Bewertungsaussagen verwenden dieselbe Zustimmungsskala:

1. Stimme überhaupt nicht zu
2. Stimme nicht zu
3. Stimme eher nicht zu
4. Weder noch
5. Stimme eher zu
6. Stimme zu
7. Stimme voll und ganz zu

Zusätzlich ist **„Kann ich nicht beurteilen“** möglich; dies ist ein fehlender Messwert, weder 0 noch die neutrale Mitte. Es gibt 22 sichtbare Fragen für A/B und 23 für C, einschließlich freiwilliger Fachrichtung und Freitext. Die automatisch zugewiesene Studiengruppe zählt nicht als Frage. Hintergrundangaben können vor bzw. während der Systemnutzung beantwortet werden; Bewertungen beziehen sich auf die durchgeführte Suche.

## Fragenkatalog

Die Nummern sind feste Katalogpositionen. Position 22 erscheint nur in C; deshalb umfasst A/B trotz der letzten Katalognummer 23 genau 22 Fragen. `1–7` bedeutet Zustimmung einschließlich Nichtbeurteilbar-Option.

| Nr. | Datenfeld | Wortlaut | Format | Herkunft |
| --- | --- | --- | --- | --- |
| 1 | `education` | Was beschreibt deine aktuelle Situation am besten? | Einfachauswahl | DIANA: Kontext/Feedback |
| 2 | `study_field` | Was ist deine Studien- oder Fachrichtung? | Freitext (freiwillig) | DIANA: Kontext/Feedback |
| 3 | `job_portal_experience` | Wie häufig hast du in den letzten sechs Monaten Online-Jobportale genutzt? | Einfachauswahl | DIANA: Kontext/Feedback |
| 4 | `ai_chat_experience` | Wie häufig hast du in den letzten sechs Monaten KI-Chatbots genutzt? | Einfachauswahl | DIANA: Kontext/Feedback |
| 5 | `search_goal` | Wonach hast du mit DIANA gesucht? | Freitext | DIANA: Kontext/Feedback |
| 6 | `usefulness_ideal` | DIANA hat mir geholfen, die ideale Stelle für mein Suchvorhaben zu finden. | 1–7 | R, Tab. 2: Perceived Usefulness 1 |
| 7 | `usefulness_find_easy` | Mit DIANA war es einfach, Stellen zu finden, die mir gefallen. | 1–7 | R, Tab. 2: Perceived Usefulness 2 |
| 8 | `usefulness_suggestions` | DIANA hat mir gute Vorschläge gemacht. | 1–7 | R, Tab. 2: Perceived Usefulness 3 |
| 9 | `dialogue_understanding` | Ich hatte den Eindruck, dass der Chatbot verstand, was ich wollte. | 1–7 | C, Tab. 5: CUI Understanding |
| 10 | `dialogue_response_quality` | Die meisten Antworten des Chatbots ergaben für mich Sinn. | 1–7 | C, Tab. 5: CUI Response Quality |
| 11 | `dialogue_attentiveness` | Der Chatbot schenkte meinen Aussagen Aufmerksamkeit. | 1–7 | C, Tab. 5: CUI Attentiveness |
| 12 | `control_preferences` | Ich hatte die Kontrolle darüber, meine Suchwünsche im Chat zu verändern. | 1–7 | C, Tab. 4: User Control 1 |
| 13 | `control_recommendations` | Ich konnte beeinflussen, welche Empfehlungen der Chatbot mir gab. | 1–7 | C, Tab. 4: User Control 2 |
| 14 | `control_adjustment` | Ich hatte die Kontrolle darüber, die Empfehlungen an meine Wünsche anzupassen. | 1–7 | C, Tab. 4: User Control 3 |
| 15 | `transparency_why` | Ich habe verstanden, warum mir die Stellen empfohlen wurden. | 1–7 | C, Tab. 4: Transparency 1 |
| 16 | `transparency_assessment` | Ich habe verstanden, wie DIANA die Eignung der Stellen beurteilt hat. | 1–7 | C, Tab. 4: Transparency 2 |
| 17 | `transparency_fit` | Ich habe verstanden, wie gut die Empfehlungen zu meinen Wünschen passten. | 1–7 | C, Tab. 4: Transparency 3 |
| 18 | `overall_satisfaction` | Insgesamt bin ich mit DIANA zufrieden. | 1–7 | R, Tab. 2: Overall Satisfaction |
| 19 | `intention_reuse` | Ich werde DIANA bei einer weiteren Jobsuche wieder nutzen. | 1–7 | R, Tab. 2: Use Intentions 1; §5.1 |
| 20 | `study_effort` | Die Nutzung von DIANA war für mich aufwendig. | 1–7 | DIANA: eigenes Aufwand-Item |
| 21 | `study_style_control` | Ich konnte den Sprachstil der Beratung an meine persönlichen Vorstellungen anpassen. | 1–7 | DIANA: eigene Gestaltungskontrolle |
| 22 | `personality_customized` | Hast du die angebotenen Einstellungen der KI-Beratung selbst verändert? | Ja/Nein (nur C) | DIANA: Nutzungskontrolle, nur C |
| 23 | `feedback` | Was hat dir bei deiner Suche geholfen, und was hat dir gefehlt? | Freitext (freiwillig) | DIANA: Kontext/Feedback |

Die Statusauswahl umfasst Bachelor, Master, anderes Studium, Promotion, Schule/Ausbildung, aktuell kein Studium/keine Ausbildung sowie „Keine Angabe“. Für beide Erfahrungsfragen gelten: nie, seltener als wöchentlich, mindestens wöchentlich aber nicht täglich, täglich oder keine Angabe. Das Suchvorhaben wird aus dem System vorgeschlagen und kann berichtigt werden. Freitext soll keine weiteren personenbezogenen Angaben enthalten.

## Auswertung

| Ergebnis | Datenfelder | Regel |
| --- | --- | --- |
| Wahrgenommener Nutzen – primärer Endpunkt | `usefulness_ideal`, `usefulness_find_easy`, `usefulness_suggestions` | Arithmetisches Mittel, nur wenn alle drei Werte numerisch und 1–7 sind |
| Kontrolle über die Suche – sekundär | `control_preferences`, `control_recommendations`, `control_adjustment` | Gleiche Vollständigkeitsregel |
| Nachvollziehbarkeit – sekundär | `transparency_why`, `transparency_assessment`, `transparency_fit` | Gleiche Vollständigkeitsregel |

Fehlt ein Wert oder lautet er „Kann ich nicht beurteilen“, bleibt das jeweilige Skalenmittel leer. Keine Nullsetzung, keine Ersetzung durch den Mittelwert anderer Personen und keine Mittelwertbildung nur aus den verbliebenen Items. Anzahl gültiger und fehlender Werte je Gruppe berichten; bei unvollständigen Teilnahmen ausdrücklich den Auswertungsstand angeben.

Die drei Gesprächsfragen werden **jeweils einzeln** ausgewertet. Sie ergeben keine gemeinsame Dialogqualitätsskala. Zufriedenheit, Wiederverwendungsabsicht, Aufwand und wahrgenommene Gestaltung sind ebenfalls Einzelitems. **Kein Gesamtsummenwert über den Fragebogen** und keine Vermischung mit Hintergrundvariablen.

Bei den Framework-Items und der Gestaltungskontrolle bedeutet ein höherer Wert mehr Zustimmung zum positiven Merkmal. Beim eigenen Item `study_effort` bedeutet er **mehr Aufwand**. Dieses Item umfasst die gesamte Nutzung einschließlich Wartezeit und Suche; es misst weder ausschließlich die Konfiguration noch eine validierte mehrdimensionale Belastungsskala.

Primärkontrast C–B, primärer Endpunkt und Umgang mit Ausschlüssen/fehlenden Werten vor dem Feldstart festlegen. Sekundäre Konstrukte und B–A getrennt kennzeichnen, Effektgrößen und Unsicherheit berichten und multiple Tests berücksichtigen. Ein beobachteter Unterschied in den Antworten bestätigt nicht automatisch, dass allein der Sprachstil die Ursache ist.
