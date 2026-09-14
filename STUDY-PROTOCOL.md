# DIANA: Studienprotokoll für den Konferenzbeitrag

Stand: 14. September 2026. Experiment `diana-abc-v3`, Fragebogen `diana-v10`.
Dies ist ein vor der neuen Erhebung erstellter, versionierter **Protokollentwurf**. Er ist noch keine extern registrierte Präregistrierung, kein Ethikvotum und keine Bestätigung einer validierten Skala. Vor der Haupterhebung kognitiv vorprüfen und den endgültigen Stand mit Datum festschreiben.

## Forschungsfrage und Beitrag

Welchen zusätzlichen wahrgenommenen Nutzen und Aufwand verursacht das **Angebot einer frei gestaltbaren KI-Suchpersönlichkeit** gegenüber der Auswahl aus festen Beratungsvorlagen?

Primärer Vergleich: **C gegen B**. Sekundär: B gegen A als Vergleich des Angebots einer Vorlagenauswahl mit einer festen Standardberatung. Nicht behaupten, diese Erhebung belege Chat gegenüber klassischer Filter-/Stichwortsuche oder einen isolierten Effekt des Sprachstils. Vorlagenwahl, Gesprächsstil und Bewertungsgewichtung sind Bestandteile des jeweiligen Beratungsangebots.

Der angestrebte Beitrag ist die Verbindung benutzerdefinierter Bewertungsschwerpunkte und Gesprächsführung in einer Jobsuche, einschließlich beobachteter Nutzung der Gestaltungsmöglichkeit. Neuheit gegenüber verwandten Conversational-Recommender-Arbeiten muss im Paper ausgearbeitet werden; allein der Einsatz eines LLM oder eine große Stichprobe ist kein Neuheitsnachweis.

## Bedingungen

| Bedingung | Beratung | Verfügbare Änderung |
| --- | --- | --- |
| A | Kompetenzbezogene, sachliche Standardberatung mit ausgewogener Gewichtung | Suchprofil und Suchwünsche; keine Persönlichkeitswahl |
| B | Top-Berufsberater oder Fachexperte | Zwischen den unveränderten Vorlagen wechseln |
| C | Dieselben Vorlagen wie B | Zusätzlich Name, Eigenschaften, Bewertungsschwerpunkt und Hinweise selbst gestalten |

B und C starten mit dem Top-Berufsberater. Freie Gestaltung ist in C freiwillig. Alle Gruppen verwenden dasselbe Modell-Snapshot, Denkaufwand, technische Antwortbudgets, den gleichen Datenbestand, BM25/E5/RRF, Top-20-Pool und Bewertungsablauf. Scores, Begründungen, Score-Sortierung und anfängliche 70er-Anzeigeschwelle sind überall vorhanden. Neue A-Sitzungen werden nicht zufällig sortiert oder durch einen fachfremden Prompt eingeschränkt. Unterschiedliche resultierende Scores oder Reihenfolgen durch die Beratungsgewichtung sind beabsichtigt; der Algorithmus und die Anzeige sind vergleichbar.

## Zuteilung und Ablauf

- Zwischenpersonenvergleich; neue Einwilligungskennungen erhalten serverseitig mit Wahrscheinlichkeit 1/3 A, B oder C. Transaktion und eindeutiger Schlüssel sichern eine stabile Zuteilung auch bei parallelen Anfragen. Das ist einfache Randomisierung, keine garantierte exakte Drittelung.
- Dieselbe knappe Aufgabe für alle: Suchprofil angeben, Stellen ansehen und mindestens eine eigene inhaltliche Frage im Chat stellen bzw. einen Suchwunsch präzisieren. Keine Pflicht, positive Rückmeldungen zu geben oder in C selbst zu gestalten.
- Vor Systembeginn: Nutzung von Jobportalen und KI-Chats in den letzten sechs Monaten. Antwortbereiche: nie, seltener als wöchentlich, wöchentlich aber nicht täglich, täglich; zusätzlich keine Angabe.
- Während einer Suche nur Fakten: demografische Angaben und Suchvorhaben. Bewertungen des Systems, Chats und der Persönlichkeitswirkung werden erst nach der Nutzung gestellt.
- Gemeinsame Ergebnisfragen stehen vor bedingungsspezifischen Fragen. Antworten werden fortlaufend gespeichert. Mindestens eine erfolgreich beantwortete eigene Chatnachricht öffnet die nachfolgenden Bewertungsseiten; eine automatische Begrüßung zählt nicht.
- `/test/a`, `/test/b` und `/test/c` sind getrennte Demonstrationszugänge. Sie liefern keine Studienzuweisungen, Umfrageantworten oder Nutzungsmetriken der Studie.

Vor der Haupterhebung ein kleiner kognitiver Pretest, beispielsweise 6–10 Personen mit unterschiedlichen Fachrichtungen und Endgeräten: Aufgabenverständnis, Bedeutung der Vorlagen und Selbstgestaltung, Skalenanker und Warte-/Fragenführung prüfen. Diese Zahl ist ein Vorschlag für den Pretest, keine statistische Fallzahl für den Gruppenvergleich. Pretestdaten nicht als reguläre Hauptstudiendaten zusammenfassen.

## Fragebogenkürzung und Versionsgrenze

V10 enthält 15/20/21 sichtbare Fragen für A/B/C, einschließlich der beiden
optionalen Felder Fachrichtung und Feedback. Gegenüber dem vorherigen V9 entfallen
**ausschließlich** `search_ease`, `express_search_needs`, `adapt_search_ease`,
`template_selection_ease` und `personality_setup`. Diese Nebenmaße wurden zur
Verringerung der Befragungslänge entfernt; sie sind nicht als identische Konstrukte
zu den verbleibenden Fragen zu verstehen.

Das primäre Einzelitem sowie Nutzen von Chat, Score, Begründungen, Gesprächsstil
und Bewertungsschwerpunkten bleiben unverändert. Suchaufwand, zukünftige
Nutzungsabsicht, berichtete Suchwunschänderung, Verständnis/Wahrnehmung der
Persönlichkeit und die Anpassungs-Selbstauskunft in C bleiben ebenfalls erhalten.
Die Selbstgestaltungsmetadaten ersetzen die Selbstauskunft nicht: `custom` kann
auch bei vorlagenidentischen Werten erfasst sein. Operationszähler ersetzen
keine Selbstauskunft darüber, ob Suchwünsche verändert wurden.

Die vorherige faire Kohorte `diana-abc-v2` / `diana-v9` behält Fragebogen und
Systembedingungen. Neue Teilnahmen erhalten `diana-abc-v3` / `diana-v10`.
Trotz identischem primären Item werden beide Kohorten wegen unterschiedlicher
Befragungskontexte nicht automatisch gepoolt. Das Offline-Skript analysiert
standardmäßig V10; historische V9-Daten müssen ausdrücklich mit `--cohort v9`
getrennt gewählt werden. Noch ältere Stände bleiben ebenfalls separat.

## Primärer Endpunkt

Das vorab gewählte **Einzelitem** `system_usefulness` lautet: „Wie hilfreich war das System für die Durchführung deiner Suche?“ Werte 1–10, mit identischen Endpunkten in A/B/C. Lesbarer Export: `v10_system_nutzen`; technische Spalte: `v10_system_usefulness`.

Primäre Schätzgröße ist der Mittelwertunterschied **C minus B**. Zweiseitiger Welch-t-Test mit α=0,05 und 95%-Konfidenzintervall für die Differenz. Zusätzlich Gruppengrößen, Mittelwert, Standardabweichung, Median und Verteilung sowie Hedges g berichten. Die Interpretation des ordinalen Einzelitems als quasi-metrisch ist eine Analyseannahme. Keine nachträgliche Zusammenrechnung beliebiger Fragen zu einem angeblich validierten Gesamtwert.

Alle Teilnahmen nach ihrer zufälligen Zuteilung auswerten. Eine Person in C gehört auch dann zu C, wenn sie eine Vorlage unverändert verwendet. Nicht anhand der Nutzung, positiver Bewertungen oder technischer Geschwindigkeit nachträglich auswählen.

## Fehlende Antworten und Ausschlüsse

Die primäre Analyse verwendet alle gültigen Primärantworten der neuen Kohorte, **auch aus unvollständigen Umfragen**. Sie ist eine Auswertung nach Zuteilung mit verfügbaren Endpunktdaten, keine vollständige Intention-to-treat-Analyse mit ersetzten fehlenden Ergebnissen. Fehlende Antworten bleiben fehlend; „nicht genutzt“ und „nicht beurteilbar“ sind keine Nullwerte. Ausmaß und Gründe des Fehlens je Gruppe sowie vollständige und unvollständige Teilnahmen getrennt berichten. Ergebnisse bei relevant unterschiedlichem Ausfall zwischen Gruppen vorsichtig interpretieren; eine Sensitivitätsanalyse vorab ergänzen, bevor Schlussfolgerungen aus solchen Daten gezogen werden.

Ausgeschlossen werden ausschließlich getrennte Testzugänge, widerrufene/gelöschte Daten, technische Duplikate und andere Protokoll-/Fragebogenversionen. Technische Fehler und Abbrüche sind zu berichten, nicht pauschal als „schlechte Teilnehmer“ zu entfernen. Eine gültige Primärantwort bleibt trotz eines späteren Abbruchs analysierbar. Mehrfachteilnahmen in unterschiedlichen Browsern werden durch die zufällige Teilnahme-ID nicht zuverlässig erkannt; dafür werden keine zusätzlichen Identifikatoren erfunden.

Korrekturen von Einzelantworten nur als belegbare Berichtigungen mit Grund und Änderungsverlauf. Rohstand sichern; keine inhaltliche Anpassung zur Erzielung günstiger Ergebnisse.

## Sekundäre und explorative Analysen

B–A ist der geplante sekundäre Vergleich. Suchaufwand, Chatnutzen, Wiederverwendungsabsicht sowie Score-/Begründungsnutzen sind sekundäre Maße. Berichtete Suchwunschänderung und die Verständlichkeit bzw. Wahrnehmung der Persönlichkeitswirkung beschreiben die Nutzung und Intervention. Die Einfachheit der Bedienung, Vorlagenauswahl und Selbstgestaltung wird in V10 nicht mehr durch eigene Items bewertet. Sekundäre Inferenztests als eigene Familie mit Holm-Korrektur auswerten; unbereinigte Einzel-p-Werte nicht als weitere bestätigte Haupthypothesen präsentieren. C–A und Vorlagen-/Selbstgestaltungs-Untergruppen sind explorativ.

Die erste tatsächlich angewendete Auswahl und spätere Wechsel werden separat erfasst. Tatsächlich selbst gestaltende Personen bilden keine zusätzliche randomisierte Gruppe. Zusammenhänge zwischen Gestaltung, Laufzeit, Fehlern und Bewertungen explorativ berichten; daraus keine kausale Wirkung der tatsächlichen Nutzung ableiten.

## Stichprobenplanung

Planungsannahme: unabhängiger zweiseitiger Zweigruppenvergleich, α=0,05, Power 80%, gleiche Gruppengröße und ähnliche Varianzen. Die Rechnung verwendet den nichtzentralen t-Test; sie ist eine Näherung für die geplante Welch-Analyse. Sie ist **nicht** aus den Effektangaben der früheren Folien abgeleitet.

| Angenommener standardisierter Unterschied d | Pro Gruppe | Insgesamt A/B/C | Starts bei angenommenen 25% ohne auswertbaren Endpunkt |
| --- | ---: | ---: | ---: |
| 0,30 | 176 | 528 | 704 |
| 0,40 | 100 | 300 | 400 |
| 0,50 | 64 | 192 | 256 |

Arbeitsziel: **100 auswertbare Primärantworten je Gruppe**, insgesamt etwa 300; dafür zunächst ungefähr 400 Starts einplanen. d=0,40 ist eine transparente Planungsannahme, kein bereits nachgewiesener Effekt. Kleinere tatsächliche Unterschiede erfordern mehr Personen. Ein Unterschied von d=0,40 entspräche beispielsweise 0,8 Skalenpunkten bei einer SD von 2; auch das ist nur eine Illustration.

Vorgeschlagene, vor Beginn festzuschreibende Stoppregel: Rekrutierung nach mindestens 100 gültigen Primärantworten je Gruppe beenden; alle bis zum festgelegten Rekrutierungsende eingegangenen gültigen Antworten einschließen. Nach Fallzahlen und Ausfällen steuern, niemals nach zwischenzeitlichen Signifikanztests. Dies ist ein Planungsdokument, keine automatische Begrenzung im Server. Eine Abweichung wegen einer festen Frist oder unerwarteter Ausfälle im Paper offenlegen.

## Erfasste Betriebsdaten und Reproduzierbarkeit

Serverseitig werden aggregierte erfolgreiche und fehlgeschlagene Such-, Neusortierungs- und Chatoperationen sowie ihre aufsummierten Laufzeiten erfasst. Ein Chat, der eine Suche auslöst, zählt sowohl als Chat als auch als Suche; die Laufzeiten überlappen und dürfen nicht zu einer Sitzungsdauer addiert werden. Die Dauer umfasst Serverarbeit, keine zuverlässig gemessene Bildschirm- oder Wartezeit beim Teilnehmer. Browserabbruch und nie abgesendete Interaktionen sind daraus nicht vollständig rekonstruierbar. Keine Suchtexte, Chattexte, IP-Adressen oder eigenen Persönlichkeitsinhalte werden als neue Metrik gespeichert.

Historisch nicht erfasste Werte sind unbekannt. Bei Abschluss werden die zugehörigen Metadaten eingefroren. Entwürfe zeigen die zuletzt erfassten Werte. Widerruf und Löschung umfassen die neuen Metadaten; externe Exporte und Sicherungen sind gesondert zu berücksichtigen.

Archivieren: Commit, Experimentkennung, Fragebogendefinition, Modell-Snapshot, Prompt-/MLDS-Dateien, Dependencyversionen, Datensatzprüfsumme und Auswerteskript. Die vorhandenen Manifestdateien unterstützen dies. Ohne dauerhafte individuelle Such-/Chattexte ist eine einzelne reale Sitzung nicht vollständig reproduzierbar; LLM-Ausgaben sind trotz Snapshot nicht garantiert identisch. Für technische Reproduktion können gesonderte synthetische Beispielprofile verwendet werden.

## Späterer technischer Ranking-Check

Ein ergänzender technischer Test soll prüfen, ob geänderte Prioritäten zu
inhaltlich nachvollziehbaren Rankingänderungen führen und wie groß die Variation
bei unveränderten Eingaben ist. Der gezielte Ablauf steht in
[research/RANKING-EVALUATION-PLAN.md](research/RANKING-EVALUATION-PLAN.md).
Dieser Check ist nur geplant: nicht ausgeführt, nicht automatisiert und nicht
terminiert. Seine Ergebnisse würden die Nutzungsstudie ergänzen, nicht die
subjektive Nützlichkeit oder tatsächliche Bewerbungserfolge ersetzen.

## Vorarbeiten und geeigneter Konferenzbeitrag

Die Bedarfserhebung aus `Vortrag.pptx` und die Systemevaluation aus `Zweite_Umfrage.pptx` sind Motivation und Vorarbeiten. Sie sind kein zeitgleicher Kontrollarm dieser Erhebung. Fallzahlen, vollständige Frageformulierungen und fehlerverdächtige Streuungsangaben zuerst anhand der Originaldaten klären. Die aktuellen Fragen nicht als validierte Fortsetzung der alten Instrumente bezeichnen, solange deren Wortlaut und Skalenanker fehlen.

Für einen empirischen Beitrag passt insbesondere [ACM UMAP 2027](https://um.org/umap2027/). Abstractfrist: 22. Januar 2027; Full/Short Paper: 29. Januar 2027; LBR/Demo: 22. März 2027 (Stand 14. September 2026). Ein Demo-/Posterbeitrag kann Systemgestaltung und Pilotbefunde berichten; ein überzeugendes Forschungs-Paper braucht zusätzlich belastbare Ergebnisse und klaren Neuheitsbeitrag.

Methodische Grundlage für gezielte Vergleichsbedingungen und die gemeinsame Betrachtung von Nutzungserfahrung und Verhalten: [Knijnenburg et al., RecSys 2011](https://ics.uci.edu/~kobsa/papers/2011-RecSys-kobsa.pdf). Die vorliegenden DIANA-Einzelitems sind deshalb nicht automatisch validiert. Verwandte Arbeit zu Gesprächsstilen und flexibler Stilauswahl: [Kostric et al., UMAP 2025](https://github.com/iai-group/umap2025-convstyles). Im Paper insbesondere den zusätzlichen Beitrag konfigurierbarer Bewertungsprioritäten herausarbeiten.

Offen vor der Haupterhebung: kognitiver Pretest, endgültiger Auswertungsplan und gegebenenfalls erforderliche institutionelle/ethische Freigaben. Vor externer Registrierung keine Präregistrierung behaupten. Technisch funktionsfähige Software garantiert weder wissenschaftliche Validität noch die Annahme einer Einreichung.
