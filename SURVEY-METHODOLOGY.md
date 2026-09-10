# Randomisierter B/C-Vergleich · diana-v6 · 10. September 2026

Experiment: `diana-bc-v1`. Die Zuordnung erfolgt serverseitig bei Beginn des Systemtests nach Einwilligung, unabhängig mit Wahrscheinlichkeit 0,5 für B bzw. C. Das garantiert keine exakt gleichen Gruppengrößen. Pro Einwilligungskennung bleibt die Zuordnung unverändert, auch bei Neuladen oder parallelen Anfragen. Es gibt keine Auswahl der Gruppe im Frontend.

- B: sachlicher Chatbot ohne wählbare KI-Persönlichkeit. Feste Bewertungsgewichte: Fachpassung 60, ausdrückliche Suchwünsche 15, fachliche Tiefe 7, Lernen 6, Innovation 6, Aufgabenklarheit 6 Prozent.
- C: dieselbe Suche mit gestaltbarer KI-Persönlichkeit, die Sprachstil und ergänzende Bewertungsgewichte beeinflusst. Fachpassung und ausdrückliche Suchwünsche behalten dieselben Gewichte wie in B.
- Beide Varianten: gleiches GPT-Modell, Denkaufwand, Retrieval, Stellenbestand, Ergebnislimit, Scoreschwelle, Begründungen und Chat-Funktionen. Das persönliche Suchprofil bleibt auch in B verfügbar. Die Persönlichkeitskonfiguration entfällt in B; ihr zusätzlicher Aufwand gehört damit zur Behandlung in C.

Der Vergleich C gegen B untersucht den zusätzlichen Effekt des gesamten Personalisierungspakets. Er trennt nicht Chat-Stil und Sortierpersonalisierung voneinander und belegt keinen kausalen Effekt gegenüber klassischer Stichwortsuche. Eine vorhandene frühere Befragung zu klassischer Suche bleibt eine gesonderte historische Vergleichserhebung.

## Fragebogen

Beide Gruppen beantworten zuerst sechs gemeinsame Ergebnisfragen (Bedienbarkeit, Suchwünsche ausdrücken, Suchwünsche anpassen, Aufwand, Systemnützlichkeit, Wiederverwendungsabsicht), dann Fragen zu Chat, Score und Begründungen. Nur C erhält sieben Persönlichkeitsfragen. B: 16 sichtbare Fragen; C: 23. Die Studienvariante ist ein vom Server bestimmtes Metadatum, keine Teilnehmerfrage. Bewertungen 1–10; search_effort ist gegenläufig (10 = sehr aufwendig). Fehlende Beurteilbarkeit bleibt separat.

Während der Wartezeit werden nur Demografie, Suchvorhaben und in C Angaben zur Einrichtung angeboten. Gemeinsame Ergebnisfragen werden erst nach Suche und eigener Chatnachricht freigegeben. Bereits in der Wartezeit beantwortete Fragen werden später übersprungen. Vor Haupterhebung primäre Zielgröße, Stichprobenumfang, Auswertung und Umgang mit Abbrüchen festlegen; nicht alle Items zu einem Gesamtwert addieren.

## Nachvollziehbarkeit und bestehende Daten

Gespeichert werden Studienvariante, Experimentkennung, Zuordnungszeitpunkt und `prior_exposure`. Letzteres zeigt eine bereits vorhandene DIANA-Sitzungskennung unter derselben Einwilligung vor Zuteilung an; es erkennt keine Nutzung unter anderen Kennungen. Nach Löschung des Browserspeichers oder auf einem anderen Gerät kann eine Person eine neue Teilnahme beginnen; es findet keine personenübergreifende Identitätsprüfung statt.

Bei Wiederaufnahme eines offenen älteren Entwurfs bleiben Demografie und Suchvorhaben erhalten; Systemtest und Ergebnisbewertungen beginnen neu. Alte Suchsitzungen lassen sich nicht als Test der neuen Variante fortsetzen. Abgeschlossene historische Antworten bleiben unverändert. Archive und eigene Spalten existieren für V4, V5 und V6. Unvollständige Teilnahmen sind separat filterbar, ebenso B/C. Die Zuordnung wird bei Widerruf/administrativer Löschung mitgelöscht.

## Git-Stände

`stand-vor-bc-vergleich` enthält den vollständigen V5-Stand vor dem Experiment, einschließlich Kopierfunktion und E-Mail-Vorlage. `vergleich-b-c` enthält den Vergleich. Datenbank und Zugangsdaten gehören nicht in Git und dürfen beim Wechsel des Codestands nicht durch alte Sicherungen ersetzt werden.

## Historische Fragebogenversionen

# Fragebogen diana-v5 · 10. September 2026

Alle 13 subjektiven Bewertungen verwenden jetzt 1–10 mit fragespezifischen Endpunkten.
Die zusätzliche Frage nach einer eigenen Chatnachricht entfällt. Die bestehende
Nutzungsschranke prüft weiterhin eine tatsächlich abgeschlossene Suche und eine eigene
Chatnachricht; Chatbewertungen werden deshalb allen Teilnehmenden gestellt.
Eigene Anpassung der Persönlichkeit und Änderung der Suchwünsche bleiben Ja/Nein.
Nicht genutzt / nicht beurteilbar bleiben separate Antwortoptionen, wo vorhanden.

V5-Antworten erhalten im Export eigene `v5_`-Spalten und Antwortstatus. Abgeschlossene
ältere Antworten bleiben unverändert; die Definition von V4 ist archiviert.
Bei Wiederaufnahme eines offenen V4-Entwurfs werden nur unveränderte Antworttypen
übernommen. Bereits beantwortete fünfstufige Fragen werden erneut auf 1–10 gestellt,
niemals rechnerisch umskaliert. Änderungen des Instruments bei der Auswertung beachten.

## Historische Version V4

# Fragebogen diana-v4 · 10. September 2026

Die Antwortform richtet sich nach dem Gegenstand: konkrete Nutzung als Ja/Nein,
subjektive Erfahrungen abgestuft und Verbesserungsvorschläge als optionaler Freitext.
Die vier Funktionsbewertungen behalten ihre 1–10-Skala. Chat-Hilfe verwendet dieselbe
Granularität. Sonstige Einschätzungen haben fünf vollständig beschriftete Kategorien.
Suche und Gespräch stehen in getrennten Fragen zur Verständlichkeit der Persönlichkeit.

Drei Angaben sind binär: eigene Anpassung der Eigenschaften, eigene Chatnachricht,
Änderung der Suchwünsche im Chat. Die initiale KI-Begrüßung zählt nicht als eigene
Chatnutzung. Ohne Chatnutzung entfallen Chat-Hilfe, Verfeinerung und Chat-Nützlichkeit.
Es werden keine Nutzungsangaben aus Chatprotokollen abgeleitet.

Nicht genutzt / nicht beurteilbar sind keine niedrigen Bewertungen. Der Export trennt
sie von übersprungenen Fragen, freiwillig fehlenden Angaben und nicht gestellten Fragen
älterer Versionen. Bei Wiederverwendung ist „Unentschieden“ eine inhaltliche Mittelkategorie.

V4 ist ein angepasster, noch nicht psychometrisch validierter Fragebogen. Ein kurzer
kognitiver Pretest mit Zielgruppenmitgliedern sollte prüfen, ob Begriffe, Antwortkategorien
und Filterführung gleich verstanden werden. Aus den Einzelitems entsteht nicht automatisch
eine validierte Gesamtskala. Selbstberichtete Nützlichkeit zeigt keine kausale Überlegenheit
gegenüber einer klassischen Jobbörse ohne entsprechende Vergleichsbedingung.

Methodische Orientierung: [GESIS – Questionnaire Design FAQ](https://www.gesis.org/fileadmin/upload/GESIS_Panel/GESIS_Panel_FAQ_Questionnaire_Design.pdf)
und [GESIS – Cognitive Pretesting](https://www.gesis.org/gesis-guides/generated-guides/049-cognitive-pretesting-2).

Bestehende V1–V3-Antworten werden nicht verändert. V4-Spalten, Codebuch und Begleitstatus
ermöglichen eine getrennte Auswertung. Eine Übernahme in gemeinsame Auswertungen erfordert
eine begründete Prüfung von Frageformulierung, Skalierung und Auswahl durch die Filterführung.
