## Aktueller Promptstand · 11. September 2026

`random-order-generic-chat-v2`: Der A-Chat erhält ausschließlich den Systemtext
„Du bist ein allgemeiner KI-Assistent.“ Keine weiteren Systemanweisungen, keine
zusätzliche Antwortlängengrenze. Kontextdaten und strukturiertes Ausgabeformat
bleiben erhalten. Zufallsreihenfolge unverändert. Frühere Promptstände bleiben
über die erfassten Systemstände getrennt auswertbar; unten steht die Historie.

# Änderungsstand 11. September 2026: allgemeiner Chat und Zufallsreihenfolge in A

Neue Zuordnungen verwenden `diana-ab-v2`, die Fragen bleiben V7. A erhält jetzt
im Chat einen allgemeinen Assistentenprompt ohne Jobsuche- oder Beratungsrolle.
Die domainspezifischen Systemanweisungen, Beraterkonfiguration und vorab berechneten
Bewertungen werden diesem Chat nicht übergeben. Nutzerprofil, aktuelle Einträge
und bisheriges Gespräch bleiben User-Kontext; daraus kann das Modell den Gegenstand
der Anfrage erkennen. Eine Unkenntnis des Themengebiets wird nicht behauptet.

A hat keine selbst gesetzte Satz-, Wort- oder Zeichengrenze im Chat. Das separate
`GenericChatDecision`-Schema setzt kein maxLength für assistant_message; der API-
Parameter max_output_tokens wird für A-Chat ausgelassen. Modell-/Providergrenzen
bestehen weiterhin. B behält seine bisherigen Vorgaben. Die Ausgabe bleibt
strukturiert, um ausdrücklich gewünschte Änderungen und Suchaktionen zu verarbeiten.

Die bis zu 20 durch BM25/E5 ermittelten Kandidaten werden bei A mit einem frischen
Zufallsseed gemischt, unabhängig von LLM-Gesamtscores und dessen Eingangsreihenfolge.
Die fachliche Retrieval- und interne Bewertungspipeline bleibt erhalten. Der Seed
bleibt im flüchtigen Suchzustand; erneutes Anzeigen, Antworten und Neubewertung
desselben Pools verändern die Reihenfolge nicht. Eine neue Vollsuche mischt neu.
Es wird keine absichtlich schlechteste oder invertierte Reihenfolge gewählt.
B bleibt nach Passung sortiert. Alte A-Sitzungen mit bewertungsbasierter Reihenfolge
müssen eine neue Suche starten, bevor der neue Chat verwendet wird.

Diese Studie vergleicht nun ein Gesamtpaket mit einer bewusst einfachen
Zufallsbasis. Unterschiede können von Reihenfolge, Anleitung, Gesprächsstil,
Antwortlänge, Einrichtung oder Ergebnisdarstellung stammen. Sie belegen nicht
isoliert den Nutzen der Persönlichkeit oder eine Überlegenheit gegenüber üblichen
relevanzsortierten Jobbörsen. A kann trotz dieser Gestaltung hilfreiche Antworten
geben; ein bestimmter Effekt wird nicht vorweggenommen.

Historische Antworten und Zuordnungen werden nicht geändert. Bestehende Kennungen
behalten ihre ursprüngliche experiment_id; erneute Nutzung wird durch die
Systemstände erkennbar. `presentation_versions` enthält die während der Teilnahme
dokumentierten Darstellungsstände (historisch `undocumented`). Dashboard-Kohorten
trennen Version, Experiment und Kombination der Darstellungsstände; gemischte
Teilnahmen werden nicht mit reinen neuen Teilnahmen zusammengefasst. CSV und
Systemmanifest enthalten diese Angaben ebenfalls. Vor einer Hauptauswertung
Erhebungszeitraum und zulässige Stände festlegen; bisherige Tests nicht ungeprüft
zu einer neuen Hauptstudie addieren.

---

# Aktueller Gesamtpaketvergleich A/B · diana-v7 · 10. September 2026

Die aktuelle Forschungsfrage lautet: Bietet die Kombination aus gestaltbarer
KI-Suchpersönlichkeit, Scores und Begründungen einen Mehrwert gegenüber einer
neutralen KI-Jobsuche mit einfachen Stellenkarten? Neue Zuteilungen erfolgen
serverseitig mit Wahrscheinlichkeit 0,5 für A beziehungsweise B (`diana-ab-v1`).

- **A:** sachliche, fachlich hilfreiche Beratung ohne Persönlichkeitskonfiguration,
  angezeigte Scores oder automatische Begründungsboxen. Alle bis zu 20 Ergebnisse
  werden angezeigt. Fragen zu Stellen können weiterhin korrekt beantwortet werden.
- **B:** gestaltbare Persönlichkeit mit beeinflussten ergänzenden Bewertungsgewichten,
  Gesprächsstil, Scores und Begründungen. Ergebnisse unter 70 werden zunächst
  ausgeblendet und können eingeblendet werden.
- Modell-Snapshot, Denkaufwand, Retrieval, Stellenbestand und fachliche
  Bewertungsbasis bleiben gleich. Die internen Bewertungen aus A werden nicht
  mit den öffentlichen Stellenkarten übertragen.

Dies ist ein randomisierter Vergleich des **Gesamtpakets**. Er isoliert weder die
Persönlichkeit noch Score, Begründungen oder Ergebnisdarstellung. Eine absichtlich
falsche oder unzuverlässige Kontrollberatung ist nicht Teil des Designs. Die frühere
Befragung zur Stichwortsuche bleibt eine gesonderte historische Erhebung.
Die methodische Einordnung und Planung mit 200 auswertbaren Teilnahmen stehen in
[STUDY-PLAN-200.md](STUDY-PLAN-200.md). Diese Designentscheidung ist eine Ableitung
aus der Forschungsfrage, keine ausdrückliche Prüfung durch das Buch von Döring.

Die sechs gemeinsamen Haupt-/Ergebnisfragen bleiben gleich. Score- und
Begründungsnützlichkeit sowie sieben Persönlichkeitsfragen erhält nur B.
A hat damit 14, B 23 Fragen (vor zusätzlichen nutzungsabhängigen Ausblendungen).
`system_usefulness` ist als einzige primäre Zielgröße vorgeschlagen; die übrigen
Items sind sekundär beziehungsweise explorativ. Keine ungeprüfte Gesamtskala bilden.

V6 ist vollständig archiviert. Alte Antworten, Gruppencodes und Zuteilungszeitpunkte
werden nicht umgeschrieben. Die Verwaltung zeigt historische B/C-Zuordnungen als
A/B an, der Export dokumentiert die ursprünglichen Codes und trennt v6-/v7-Spalten.
Eine frühere Zuteilung bleibt stabil (altes B → A, altes C → B); sie bekommt kein
neues Auslosungsdatum. Ihre ursprüngliche Experimentkennung bleibt nachvollziehbar.
Bei offenen v6-Entwürfen werden nur Demografie und Suchvorhaben übernommen;
Systemtest und Ergebnisfragen beginnen im neuen Stand erneut. Geänderte
Studienhinweise verlangen eine erneute Einwilligung. Historische und neue
Behandlungsstände nicht ungeprüft gemeinsam auswerten.

## Archivierter Vergleich B/C · diana-v6

Die folgenden Abschnitte dokumentieren den früheren Stand, nicht die aktuelle
Variante A/B. Git-Branch-Namen und archivierte Modelltests behalten ihre historischen
Bezeichnungen, damit der frühere Versuchsaufbau rekonstruierbar bleibt.

Experiment: `diana-bc-v1`. Die Zuordnung erfolgt serverseitig bei Beginn des Systemtests nach Einwilligung, unabhängig mit Wahrscheinlichkeit 0,5 für B bzw. C. Das garantiert keine exakt gleichen Gruppengrößen. Pro Einwilligungskennung bleibt die Zuordnung unverändert, auch bei Neuladen oder parallelen Anfragen. Es gibt keine Auswahl der Gruppe im Frontend.

- B: sachlicher Chatbot ohne wählbare KI-Persönlichkeit. Feste Bewertungsgewichte: Fachpassung 60, ausdrückliche Suchwünsche 15, fachliche Tiefe 7, Lernen 6, Innovation 6, Aufgabenklarheit 6 Prozent.
- C: dieselbe Suche mit gestaltbarer KI-Persönlichkeit, die Sprachstil und ergänzende Bewertungsgewichte beeinflusst. Fachpassung und ausdrückliche Suchwünsche behalten dieselben Gewichte wie in B.
- Beide Varianten: gleiches GPT-Modell, Denkaufwand, Retrieval, Stellenbestand, Ergebnislimit, Scoreschwelle, Begründungen und Chat-Funktionen. Das persönliche Suchprofil bleibt auch in B verfügbar. Die Persönlichkeitskonfiguration entfällt in B; ihr zusätzlicher Aufwand gehört damit zur Behandlung in C.

Der Vergleich C gegen B untersucht den zusätzlichen Effekt des gesamten Personalisierungspakets. Er trennt nicht Chat-Stil und Sortierpersonalisierung voneinander und belegt keinen kausalen Effekt gegenüber klassischer Stichwortsuche. Eine vorhandene frühere Befragung zu klassischer Suche bleibt eine gesonderte historische Vergleichserhebung.

## Fragebogen

Beide Gruppen beantworten zuerst sechs gemeinsame Ergebnisfragen (Bedienbarkeit, Suchwünsche ausdrücken, Suchwünsche anpassen, Aufwand, Systemnützlichkeit, Wiederverwendungsabsicht), dann Fragen zu Chat, Score und Begründungen. Nur C erhält sieben Persönlichkeitsfragen. B: 16 sichtbare Fragen; C: 23. Die Studienvariante ist ein vom Server bestimmtes Metadatum, keine Teilnehmerfrage. Bewertungen 1–10; search_effort ist gegenläufig (10 = sehr aufwendig). Fehlende Beurteilbarkeit bleibt separat.

Während der Wartezeit werden nur Demografie, Suchvorhaben und in C Angaben zur Einrichtung angeboten. Gemeinsame Ergebnisfragen werden erst nach Suche und eigener Chatnachricht freigegeben. Bereits in der Wartezeit beantwortete Fragen werden später übersprungen. Vor Haupterhebung primäre Zielgröße, Stichprobenumfang, Auswertung und Umgang mit Abbrüchen festlegen; nicht alle Items zu einem Gesamtwert addieren.

## Konkretisierte Planung und Sprachprofil-Update

Der Studienleiter plant nun mit **200 auswertbaren Teilnahmen**, etwa 100 je Gruppe.
Die Sensitivitätsanalyse und der vorgeschlagene Analyseplan stehen in
[STUDY-PLAN-200.md](STUDY-PLAN-200.md). Die Hauptzielgröße und Auswertungsregeln
sind dort als Vorschläge zur Abstimmung gekennzeichnet, nicht als rückwirkende
Präregistrierung. Fragenanzahl und Fragebogenversion bleiben unverändert.

Das Sprachprofil-Update vom 10.09.2026 berücksichtigt jetzt ausdrücklich die
editierbaren Vorlagen: Diese werden technisch als eigene Persönlichkeit gesendet.
Der aus den aktuellen Eigenschaften abgeleitete Ausdrucksplan gilt für Chat,
Suchansprache und Kartenbegründungen. Der Anzeigename wählt keine versteckten
Stilregeln aus; Änderungen der Eigenschaften bleiben wirksam. Der einheitliche
Begrüßungsblock ist gekürzt, die tatsächliche Bewertung bleibt unverändert.
Beide Gruppen erhalten dieselbe neue Begrenzung auf 600 Zeichen für generierte
Chat-/Suchtexte; der serverseitige Hinweis zu Anzahl und Bedienung kommt hinzu.
Modell-Snapshot, Denkaufwand, Scoring-Komponenten, Gewichte und Retrieval bleiben
unverändert. Promptänderungen erzeugen über die vorhandenen Quellhashes eine
neue technische Release-ID. Frühere Ergebnisse nicht ungeprüft damit vermischen.

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
