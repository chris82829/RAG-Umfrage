# DIANA: Studienprotokoll für den Konferenzbeitrag

Stand: 21. September 2026. Experiment `diana-abc-v5`, Fragebogen `diana-v12`.
Dies ist ein vor der neuen Erhebung erstellter, versionierter **Protokollentwurf**. Er ist noch keine extern registrierte Präregistrierung, kein Ethikvotum und keine Bestätigung einer validierten Skala. Vor der Haupterhebung kognitiv vorprüfen und den endgültigen Stand mit Datum festschreiben.

## Forschungsfrage und Beitrag

Welchen zusätzlichen wahrgenommenen Nutzen und Aufwand verursacht eine **selbst gestaltbare KI-Suchpersönlichkeit** gegenüber einem fest eingestellten Top-Berufsberater?

Primärer Vergleich: **C gegen B**. Sekundär: B gegen A als Vergleich des vollständigen RAG-Berufsberaterprompts mit dem Basissystem ohne wählbare KI-Suchpersönlichkeit. Im freigegebenen Ausgangsstand ist das A-Promptfeld leer. Wird es administrativ geändert, muss diese Promptrevision als eigene Behandlungsfassung ausgewertet werden. Dieser sekundäre Vergleich isoliert keinen Persönlichkeitseffekt: Aufgabenanweisung, Gesprächsinitiative und Rollenprofil unterscheiden sich gemeinsam. Nicht behaupten, diese Erhebung belege Chat gegenüber klassischer Filter-/Stichwortsuche.

Der angestrebte Beitrag ist die selbst gestaltete Gesprächsführung und Erklärung von Empfehlungen in einer Jobsuche, einschließlich beobachteter Nutzung der Gestaltungsmöglichkeit. Seit V12 verwenden A, B und C dieselbe feste ausgewogene Bewertungsformel. Neuheit gegenüber verwandten Conversational-Recommender-Arbeiten muss im Paper ausgearbeitet werden; allein der Einsatz eines LLM oder eine große Stichprobe ist kein Neuheitsnachweis.

## Bedingungen

| Bedingung | Beratung | Verfügbare Änderung |
| --- | --- | --- |
| A | Basissystem; standardmäßig kein Systemprompt, optional separat versionierter A-Prompt | Suchprofil und Suchwünsche; keine wählbare Persönlichkeit |
| B | Fester Top-Berufsberater mit RAG-Auftrag | Suchprofil und Suchwünsche; Beratung nicht veränderbar |
| C | Selbst gestaltete Beratung auf derselben Berufsberater-Basis; Suchfokus fest ausgewogen | Name, Gesprächseigenschaften und Hinweise selbst gestalten; keine Auswahl des Suchfokus |

B verwendet ausschließlich den Top-Berufsberater; C beginnt mit dessen fachlichem RAG-Auftrag und gestaltet die sichtbare KI-Konfiguration selbst. Alle Gruppen verwenden dasselbe Modell-Snapshot, denselben Denkaufwand, Datenbestand, BM25/E5/RRF und Top-20-Pool. Scores, Begründungen und Score-Sortierung sind überall vorhanden. Zunächst erscheinen die ersten zehn Stellen; die übrigen bis zu 20 lassen sich mit „Weitere Stellen anzeigen“ öffnen. Es gibt keine Mindestscore-Schwelle. In der vorgesehenen Ausgangsfassung ist A bewusst leer und erhält damit keine Rollen- oder Beratungsanweisung; eine administrativ geänderte A-Fassung bildet eine getrennt zu berichtende Promptrevision. Daraus entstehende Qualitäts- und Fehlerratenunterschiede gehören zum sekundär untersuchten Gesamtpaket.

### Aktueller V12-Stand: gemeinsame Gewichte

`fixed-balanced-v4` verwendet für A/B/C genau dieselben sechs Gewichte:
Fachpassung 60 %, Profilpräferenzen 15 %, fachliche Tiefe 7 %, Lernen/Entwicklung
6 %, Gestaltung/Innovation 6 % und Klarheit der Aufgaben 6 %. Es gibt keine
B-spezifische Lernpotenzial-Gewichtung mehr. Die inhaltlichen Systemprompts werden
durch diese Änderung nicht umgeschrieben.

**Gleiche Gewichte garantieren keine identischen Einzelbewertungen oder Rankings.**
Die LLM-Bewertung kann weiterhin durch den jeweiligen Prompt und durch generative
Variation beeinflusst werden. Eine vollständig personaunabhängige Bewertungsstufe
ist mit dieser Vereinheitlichung nicht nachgewiesen. Neue ausdrückliche Angaben
im Chat können das Profil und damit spätere Rangfolgen verändern. Deshalb nicht
behaupten, sämtliche verbleibenden Unterschiede seien ausschließlich Sprachstil.
Release-Hash, Scoring-Version, Promptrevision, Experiment und Fragebogenversion
zusammen auswerten; V11 und V12 nicht ungeprüft zusammenführen.

### Historische Entwicklungsänderung vom 21. September 2026 vor V12: C sucht fest ausgewogen

Die Auswahl des zusätzlichen Suchziels entfällt in C beim Einrichten und Bearbeiten.
Der Server setzt für `custom_career` immer `focus=ausgewogen`, auch bei alten
Voreinstellungen oder abweichenden Client-Eingaben. Name, Gesprächseigenschaften
und eigene Hinweise bleiben gestaltbar. Die Gewichte lauten 60 % Fachpassung,
15 % Profilpräferenzen und 7/6/6/6 % für fachliche Tiefe, Lernen, Innovation und
Klarheit. Suchwünsche im Profil oder Gespräch werden weiterhin berücksichtigt.

B bleibt beim festen Berufsberater mit Lernpotenzial-Gewichtung. C–B vergleicht
damit weiterhin unterschiedliche Beratungspakete, nicht ausschließlich einen
Gesprächsstil. Der neue Release-Hash und `personality_focus_policy` dokumentieren
die Änderung; frühere Teilnahmen mit frei wählbarem C-Fokus nicht ungeprüft poolen.
Der Fragebogen wird durch diese Änderung nicht automatisch angepasst.

### Historische Entwicklungsänderung vom 14. September 2026: Beratung v2

`evidence-advisory-v2` konkretisiert die Entscheidungshilfe in B/C: Verknüpfung von Profil und Anzeigenbelegen, wichtigste offene Voraussetzung, situationsbezogener nächster Schritt und Vergleich anhand derselben Kriterien. C ergänzt diese Berufsberater-Basis durch die selbst gestaltete Konfiguration. Mit `explicit-priority-v3` steuert ausschließlich der explizite Suchfokus die ergänzenden Gewichte; Gesprächseigenschaften beeinflussen den Ton. Fachpassung (60 %) und Profilpräferenzen (15 %) bleiben vorrangig, die übrigen 25 % bilden den gewählten Schwerpunkt ab.

Gemeinsame Fehlerkorrekturen gelten für alle aktuellen Gruppen: kein 600-Zeichen-Limit im Ausgabeschema, serverseitige Schutzgrenze von 6.000 Zeichen und Zurückweisung von Fehlerobjekten als Beratungsantwort. Modell-Snapshot, Denkaufwand und Tokenbudgets bleiben gleich. Dies garantiert weder vollständige Modellantworten noch bessere Ergebnisse; die technische Prüfung verwendet simulierte API-Antworten.

Diese Änderungen wurden nach Einsicht in den bisherigen technischen Pilotversuch entwickelt. Dessen Ergebnisse sind Entwicklungsdaten und kein unabhängiger Wirksamkeitsnachweis der neuen Version. Originaldateien bleiben erhalten. Vor einer neuen Erhebung den endgültigen Release festschreiben; Teilnahmen vor und nach diesem Wechsel anhand der gespeicherten `release_id` getrennt auswerten. Gleiche Experiment-/Fragebogennamen allein erlauben kein Pooling über geänderte Interventionen. `advisory_version` und `scoring_version` stehen zusätzlich im Release-Manifest. Details: `research/development/2026-09-14-advisory-v2/README.md`.

### Historische Entwicklungsänderung vom 18. September 2026: gezielte Rückfragen

`ranking-followup-v3` ergänzt B/C um eine konkrete Rückfrage am Ende der Suchansprache und jeder Beratungsantwort. Der Berufsberater klärt offene berufliche Prioritäten, um Stellen zu gruppieren oder neu zu sortieren. Die Frage orientiert sich an belegten Unterschieden der Stellen und bereits genannten Wünschen. Eindeutige kurze Antworten werden im Gesprächskontext als Profilpräferenz oder ausdrücklich belegte Fähigkeit übernommen; Unentschlossenheit und Gegenfragen ändern das Profil nicht. Präferenzen führen zur Neubewertung, neue vorhandene Fähigkeiten zur erneuten Suche. Persönlichkeitsgewichte werden dadurch nicht verändert.

Nach Ausschöpfung der drei Studiennachrichten wird keine weitere Rückfrage verlangt; auf den eigenständigen Testseiten gilt dieses Limit nicht. Bereits beantwortete Fragen, ausdrücklich abgelehnte Rückfragen und künstliche Fragen ohne Entscheidungshilfe sollen entfallen. Dies sind Modellinstruktionen und keine Garantie jeder einzelnen Ausgabe. A erhält keine Pflicht zur proaktiven Rückfrage. B gegen A vergleicht damit auch unterschiedliche Gesprächsinitiative; der primäre Vergleich C gegen B bietet in beiden Gruppen dieselbe Rückfragelogik. Modell, Denkaufwand, Bewertungsformel und Fragebogen bleiben unverändert. Der Release speichert die neue `advisory_version` und die geänderten Prompt-/Vorlagen-Hashes. Vorherige Teilnahmen nicht ungeprüft mit diesem Stand zusammenfassen. Technische Stichproben sind Entwicklungsprüfungen, kein Nachweis einer optimalen Rangfolge.

## Zuteilung und Ablauf

- Zwischenpersonenvergleich; neue Einwilligungskennungen erhalten serverseitig mit Wahrscheinlichkeit 1/3 A, B oder C. Transaktion und eindeutiger Schlüssel sichern eine stabile Zuteilung auch bei parallelen Anfragen. Das ist einfache Randomisierung, keine garantierte exakte Drittelung.
- Dieselbe knappe Aufgabe für alle: Suchprofil angeben, Stellen ansehen und ein kurzes Gespräch mit genau drei erfolgreich beantworteten eigenen Nachrichten führen, um Anforderungen zu klären und Suchwünsche zu präzisieren. Keine Pflicht, positive Rückmeldungen zu geben. C durchläuft den Selbstgestaltungsweg; eine inhaltliche Veränderung der vorgeschlagenen Ausgangskonfiguration wird gesondert erfragt.
- Vor Systembeginn: alle sechs Hintergrundfragen zu Alter, Geschlecht, aktueller Situation, optionaler Fachrichtung sowie Nutzung von Jobportalen und KI-Chats in den letzten sechs Monaten. Bei den vorgesehenen Fragen ist „Keine Angabe“ möglich. Diese Angaben werden nicht als Matchingprofil an das LLM geschickt.
- Während einer Suche nur das noch offene Suchvorhaben; bereits beantwortete Hintergrundfragen werden übersprungen. Bewertungen des Systems, Chats und der Persönlichkeitswirkung werden erst nach der Nutzung gestellt.
- Gemeinsame Ergebnisfragen stehen vor bedingungsspezifischen Fragen. Antworten werden fortlaufend gespeichert. Erst drei erfolgreich beantwortete eigene Chatnachrichten öffnen die Bewertungsseiten. Die Prüfung gilt auch serverseitig für Übergang, Bewertungsentwürfe und Abschluss; eine automatische Begrüßung zählt nicht.
- In allen drei Umfragegruppen sind pro Teilnahme genau drei erfolgreich beantwortete eigene Chatnachrichten erforderlich und höchstens drei möglich. Dies ist ein festes Interaktionsbudget, kein Maß für freiwillige Gesprächsintensität. Fehlgeschlagene Anfragen zählen nicht; Neuladen und neue Suchsitzungen setzen den teilnahmebezogenen Zähler nicht zurück. Formularänderungen ohne Nachricht zählen nicht als Chatnachricht. Das Limit wird serverseitig geprüft und im Release-Manifest dokumentiert; historische Teilnahmen mit anderem Interaktionsumfang sind entsprechend zu unterscheiden.
- `/test/a`, `/test/b` und `/test/c` sind getrennte Demonstrationszugänge. Sie liefern keine Studienzuweisungen, Umfrageantworten oder Nutzungsmetriken der Studie.
  Auf diesen Testseiten ist die Anzahl eigener Chatnachrichten unbegrenzt.

Vor der Haupterhebung ein kleiner kognitiver Pretest, beispielsweise 6–10 Personen mit unterschiedlichen Fachrichtungen und Endgeräten: Aufgabenverständnis, Unterschied zwischen festem Berufsberater und Selbstgestaltung, Skalenanker und Warte-/Fragenführung prüfen. Diese Zahl ist ein Vorschlag für den Pretest, keine statistische Fallzahl für den Gruppenvergleich. Pretestdaten nicht als reguläre Hauptstudiendaten zusammenfassen.

## Fragebogen V12 und Versionsgrenze

Die verbindliche Definition steht in [survey_definition_v12.json](survey_definition_v12.json).
A/B/C sehen **17/21/22 Fragen**, einschließlich der optionalen Fachrichtung und des
optionalen Feedbacks; die automatisch zugewiesene Studiengruppe zählt nicht dazu.
Das bisherige Einzelitem `system_usefulness` wird durch drei Zustimmungsitems
ersetzt. `personality_clarity_explanations` fragt jetzt nach Sprachstil und
Formulierung der Begründungen; die frühere Rangfolgenfrage wird nicht umetikettiert.
Die Frage `personalized_search_usefulness` zu Bewertungsschwerpunkten entfällt
in V12. Historische Definitionen und Antworten bleiben erhalten (deprecated,
keine Datenlöschung).

Neue Teilnahmen erhalten `diana-abc-v5` / `diana-v12`; vorhandene V11/v4- und ältere
Zuordnungen und Fragebögen bleiben separat. Fortgesetzte alte Teilnahmen können
den neuen gemeinsamen Software-/Scoringstand verwenden; mehrere Release-Hashes
sind daher keine unveränderte historische Behandlung. V11 enthielt 15/20/21 Fragen und das 1–10-Einzelitem;
V10/V9 gehören ebenfalls zu historischen Behandlungsfassungen. Skalenwerte und
Interventionen verschiedener Versionen werden nicht zusammengefasst.

## Primärer Endpunkt: vorläufige V12-Operationalisierung

Drei Aussagen, jeweils 1–5: „Stimme gar nicht zu“, „Stimme eher nicht zu“, „Neutral“,
„Stimme eher zu“, „Stimme voll zu“; zusätzlich „Kann ich nicht beurteilen“:

- `usefulness_effective`: Die Nutzung des Systems hat meine Stellensuche effektiver gemacht.
- `usefulness_speed`: Das System hat mir geholfen, passende Stellen schneller zu finden.
- `usefulness_overall`: Insgesamt fand ich das System nützlich für meine Stellensuche.

Vorläufig geplante Zusammenfassung: arithmetisches Mittel **nur wenn alle drei
Antworten numerisch 1–5 vorliegen**. Bei einem fehlenden/nicht beurteilbaren Item
bleibt der zusammengesetzte Wert fehlend; keine Mittelung aus ein oder zwei Items
und keine Imputation mit 0. Die Rohitems bleiben separat erhalten. Die Verwaltung
zeigt sie einzeln und berechnet diesen Forschungsendpunkt nicht automatisch.

Die deutsche Formulierung und die fünfstufige Skala sind eine projektspezifische
Anpassung, **keine bereits validierte ResQue-/CRS-Que-Skala**. Herkunft, Übersetzung,
Pretest und Prüfung von Dimensionalität/Reliabilität sind noch zu dokumentieren.
Die Analyseentscheidung einschließlich Umgang mit unzureichender Skalenqualität
vor Einsicht in Gruppeneffekte festschreiben; keine ergebnisabhängige Itemauswahl.

Primärer Vergleich bleibt **C minus B**. Als Analyseentwurf sind Gruppengrößen,
Itemverteilungen, Mittelwerte und Streuungen sowie ein zweiseitiger Welch-Vergleich
mit 95%-Konfidenzintervall und Hedges g vorgesehen. Die Behandlung eines solchen
Mittelwerts als quasi-metrisch ist eine Analyseannahme. Es liegt noch kein
freigegebenes V12-Primäranalyseskript vor: `research/analyze_primary.py` verarbeitet
historische V9–V11-Einzelitems und darf nicht durch Umbenennen von Spalten auf V12
angewendet werden.

Alle Teilnahmen nach ihrer zufälligen Zuteilung auswerten. Eine Person in C bleibt
auch ohne inhaltliche Änderung der Ausgangskonfiguration C. Nicht nach Nutzung,
positiven Bewertungen oder technischer Geschwindigkeit nachträglich auswählen.

## Fehlende Antworten und Ausschlüsse

Die primäre Analyse verwendet alle nach der Drei-Item-Regel gültigen Primärwerte der neuen V12-Kohorte, **auch aus unvollständigen Umfragen**. Sie ist eine Auswertung nach Zuteilung mit verfügbaren Endpunktdaten, keine vollständige Intention-to-treat-Analyse mit ersetzten fehlenden Ergebnissen. Fehlende Antworten bleiben fehlend; „nicht genutzt“ und „nicht beurteilbar“ sind keine Nullwerte. Ausmaß und Gründe des Fehlens je Gruppe sowie vollständige und unvollständige Teilnahmen getrennt berichten. Ergebnisse bei relevant unterschiedlichem Ausfall zwischen Gruppen vorsichtig interpretieren; eine Sensitivitätsanalyse vorab ergänzen, bevor Schlussfolgerungen aus solchen Daten gezogen werden.

Ausgeschlossen werden ausschließlich getrennte Testzugänge, widerrufene/gelöschte Daten, technische Duplikate und andere Protokoll-/Fragebogenversionen. Technische Fehler und Abbrüche sind zu berichten, nicht pauschal als „schlechte Teilnehmer“ zu entfernen. Eine gültige Primärantwort bleibt trotz eines späteren Abbruchs analysierbar. Mehrfachteilnahmen in unterschiedlichen Browsern werden durch die zufällige Teilnahme-ID nicht zuverlässig erkannt; dafür werden keine zusätzlichen Identifikatoren erfunden.

Korrekturen von Einzelantworten nur als belegbare Berichtigungen mit Grund und Änderungsverlauf. Rohstand sichern; keine inhaltliche Anpassung zur Erzielung günstiger Ergebnisse.

## Sekundäre und explorative Analysen

B–A ist der geplante sekundäre Vergleich des gesamten RAG-Berufsberaterprompts mit der separat konfigurierten A-Bedingung. Im Ausgangsstand ist ihr Prompt leer. Falls mehrere A-Revisionen eingesetzt wurden, dürfen sie nicht ungeprüft zu einer Behandlung zusammengefasst werden. Suchaufwand, Chatnutzen, Wiederverwendungsabsicht sowie Score-/Begründungsnutzen sind sekundäre Maße. Berichtete Suchwunschänderung und die Verständlichkeit bzw. Wahrnehmung der Persönlichkeitswirkung beschreiben Nutzung und Intervention. Die Einfachheit der Einrichtung wird in V12 nicht durch ein eigenes Item bewertet. Sekundäre Inferenztests als eigene Familie mit Holm-Korrektur auswerten; unbereinigte Einzel-p-Werte nicht als weitere bestätigte Haupthypothesen präsentieren. C–A und Untergruppen nach tatsächlicher Veränderung sind explorativ.

Der tatsächlich angewendete Weg wird separat erfasst: B als feste `career`-Konfiguration, C als `custom`. Diese Herkunft beweist nicht, dass C sichtbare Felder inhaltlich verändert hat; dafür dient die Selbstauskunft. Zusammenhänge zwischen Veränderung, Laufzeit, Fehlern und Bewertungen nur explorativ berichten.

## Stichprobenplanung: vor V12 neu festzuschreiben

Die folgende Tabelle ist eine **historische Planungsorientierung** aus dem Entwurf
mit einem 1–10-Einzelitem. Sie ist keine aktualisierte Poweranalyse für die
Drei-Item-Operationalisierung. Für V12 müssen relevante Effektgröße, Streuung,
Vollständigkeit aller drei Items, Ausfallannahme und Rekrutierungsfrist vorab
geprüft werden. Die Studie begrenzt Teilnehmerzahlen nicht automatisch.


Planungsannahme: unabhängiger zweiseitiger Zweigruppenvergleich, α=0,05, Power 80%, gleiche Gruppengröße und ähnliche Varianzen. Die Rechnung verwendet den nichtzentralen t-Test; sie ist eine Näherung für die geplante Welch-Analyse. Sie ist **nicht** aus den Effektangaben der früheren Folien abgeleitet.

| Angenommener standardisierter Unterschied d | Pro Gruppe | Insgesamt A/B/C | Starts bei angenommenen 25% ohne auswertbaren Endpunkt |
| --- | ---: | ---: | ---: |
| 0,30 | 176 | 528 | 704 |
| 0,40 | 100 | 300 | 400 |
| 0,50 | 64 | 192 | 256 |

Historisches Arbeitsziel: **100 auswertbare Primärantworten je Gruppe**, insgesamt etwa 300; dafür zunächst ungefähr 400 Starts einplanen. d=0,40 ist eine transparente Planungsannahme, kein bereits nachgewiesener Effekt. Kleinere tatsächliche Unterschiede erfordern mehr Personen. Ein Unterschied von d=0,40 entspräche beispielsweise 0,8 Skalenpunkten bei einer SD von 2; dies war nur eine Illustration auf der alten 1–10-Skala und darf nicht als relevante Punktdifferenz der V12-Skala übernommen werden.

Historisch vorgeschlagene, für V12 noch zu prüfende Stoppregel: Rekrutierung nach mindestens 100 gültigen Primärantworten je Gruppe beenden; alle bis zum festgelegten Rekrutierungsende eingegangenen gültigen Antworten einschließen. Nach Fallzahlen und Ausfällen steuern, niemals nach zwischenzeitlichen Signifikanztests. Dies ist ein Planungsdokument, keine automatische Begrenzung im Server. Eine Abweichung wegen einer festen Frist oder unerwarteter Ausfälle im Paper offenlegen.

## Erfasste Betriebsdaten und Reproduzierbarkeit

V12 ergänzt datensparsame Einzelereignisse: Sichtbarkeitsintervalle von Begründungen,
Aufklappen, Stellendetails und erfolgreiche Chatdurchgänge. Die Definition,
Messgrenzen und Löschwege stehen in [STUDY-TELEMETRY.md](STUDY-TELEMETRY.md).
Die Verwaltung exportiert sie separat als CSV mit Teilnahme-ID für die Zuordnung.
Sichtbarkeit ist kein Lesebeweis, Klicks und Verweildauer sind keine Qualitätsurteile.
Fehlende Ereignisse können technische Ursachen haben; historische Nutzung wird
nicht rückwirkend rekonstruiert. Die vorgeschriebenen drei Nachrichten sind kein
variierendes Engagementmaß.


Serverseitig werden aggregierte erfolgreiche und fehlgeschlagene Such-, Neusortierungs- und Chatoperationen sowie ihre aufsummierten Laufzeiten erfasst. Ein Chat, der eine Suche auslöst, zählt sowohl als Chat als auch als Suche; die Laufzeiten überlappen und dürfen nicht zu einer Sitzungsdauer addiert werden. Die Dauer umfasst Serverarbeit, keine zuverlässig gemessene Bildschirm- oder Wartezeit beim Teilnehmer. Browserabbruch und nie abgesendete Interaktionen sind daraus nicht vollständig rekonstruierbar. Keine Suchtexte, Chattexte, IP-Adressen oder eigenen Persönlichkeitsinhalte werden als neue Metrik gespeichert.

Historisch nicht erfasste Werte sind unbekannt. Bei Abschluss werden die zugehörigen Metadaten eingefroren. Entwürfe zeigen die zuletzt erfassten Werte. Widerruf und Löschung umfassen die neuen Metadaten; externe Exporte und Sicherungen sind gesondert zu berücksichtigen.

Archivieren: Commit, Experimentkennung, Fragebogendefinition, Modell-Snapshot, Prompt-/MLDS-Dateien, Dependencyversionen, Datensatzprüfsumme und Auswerteskript. Die vorhandenen Manifestdateien unterstützen dies. Ohne dauerhafte individuelle Such-/Chattexte ist eine einzelne reale Sitzung nicht vollständig reproduzierbar; LLM-Ausgaben sind trotz Snapshot nicht garantiert identisch. Für technische Reproduktion können gesonderte synthetische Beispielprofile verwendet werden.

## Vorbereitung unabhängiger Relevanzurteile

Die eigenständig laufenden Werkzeuge unter
[research/human_relevance/README.md](research/human_relevance/README.md) exportieren
40 geschichtete Profil-Stellen-Paare aus bereitgestellten aktuellen Ergebnissen
und werten später zwei unabhängige menschliche Urteile aus. Sie enthalten keine
aktuellen V12-Systemausgaben oder menschlichen Bewertungen; Software-Testdaten
sind ausdrücklich synthetisch. Es werden keine kostenpflichtigen Modellläufe
für diese Vorbereitung gestartet.

Die 40 Paare genügen normalerweise nicht für vollständige Top-10-Rankingmetriken.
Precision@10 verlangt vollständig beurteilte Top 10; nDCG@10 zusätzlich den
dokumentierten Vergleichspool für die Idealrangfolge. Fehlende Urteile werden
nicht als irrelevant behandelt. Kappa und Score-Relevanz-Korrelation ergänzen,
ersetzen aber nicht die Nutzerstudie. Frühere Pläne zum Wechsel von Bewertungsprioritäten gehören zu älteren
Systemständen und belegen keine ausgeführte V12-Prüfung.

## Vorarbeiten und geeigneter Konferenzbeitrag

Die Bedarfserhebung aus `Vortrag.pptx` und die Systemevaluation aus `Zweite_Umfrage.pptx` sind Motivation und Vorarbeiten. Sie sind kein zeitgleicher Kontrollarm dieser Erhebung. Fallzahlen, vollständige Frageformulierungen und fehlerverdächtige Streuungsangaben zuerst anhand der Originaldaten klären. Die aktuellen Fragen nicht als validierte Fortsetzung der alten Instrumente bezeichnen, solange deren Wortlaut und Skalenanker fehlen.

Aktuelles Einreichungsziel ist ein empirisches Full Paper bei [ACM CHIIR 2027](https://chiir2027.github.io/full-papers.html). Die technische Umsetzung ersetzt weder einen neuen Erkenntnisbeitrag noch eine abgeschlossene Evaluation.

Historische Konferenzeinordnung vom 14. September 2026: Für einen empirischen Beitrag wurde insbesondere [ACM UMAP 2027](https://um.org/umap2027/). Abstractfrist: 22. Januar 2027; Full/Short Paper: 29. Januar 2027; LBR/Demo: 22. März 2027 (Stand 14. September 2026). Ein Demo-/Posterbeitrag kann Systemgestaltung und Pilotbefunde berichten; ein überzeugendes Forschungs-Paper braucht zusätzlich belastbare Ergebnisse und klaren Neuheitsbeitrag.

Methodische Grundlage für gezielte Vergleichsbedingungen und die gemeinsame Betrachtung von Nutzungserfahrung und Verhalten: [Knijnenburg et al., RecSys 2011](https://ics.uci.edu/~kobsa/papers/2011-RecSys-kobsa.pdf). Die vorliegenden DIANA-Einzelitems sind deshalb nicht automatisch validiert. Verwandte Arbeit zu Gesprächsstilen und flexibler Stilauswahl: [Kostric et al., UMAP 2025](https://github.com/iai-group/umap2025-convstyles). Im aktuellen Paper den zusätzlichen Beitrag selbst gestaltbarer Beratung gegenüber fester Beratung herausarbeiten; frei konfigurierbare Bewertungsprioritäten sind kein Merkmal von V12.

Offen vor der Haupterhebung: kognitiver Pretest, endgültiger Auswertungsplan und gegebenenfalls erforderliche institutionelle/ethische Freigaben. Vor externer Registrierung keine Präregistrierung behaupten. Technisch funktionsfähige Software garantiert weder wissenschaftliche Validität noch die Annahme einer Einreichung.
