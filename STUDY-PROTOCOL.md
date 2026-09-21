# DIANA: Studienprotokoll für den Konferenzbeitrag

Stand: 21. September 2026. Experiment `diana-abc-v4`, Fragebogen `diana-v11`.
Dies ist ein vor der neuen Erhebung erstellter, versionierter **Protokollentwurf**. Er ist noch keine extern registrierte Präregistrierung, kein Ethikvotum und keine Bestätigung einer validierten Skala. Vor der Haupterhebung kognitiv vorprüfen und den endgültigen Stand mit Datum festschreiben.

## Forschungsfrage und Beitrag

Welchen zusätzlichen wahrgenommenen Nutzen und Aufwand verursacht eine **selbst gestaltbare KI-Suchpersönlichkeit** gegenüber einem fest eingestellten Top-Berufsberater?

Primärer Vergleich: **C gegen B**. Sekundär: B gegen A als Vergleich des vollständigen RAG-Berufsberaterprompts mit dem Basissystem ohne wählbare KI-Suchpersönlichkeit. Im freigegebenen Ausgangsstand ist das A-Promptfeld leer. Wird es administrativ geändert, muss diese Promptrevision als eigene Behandlungsfassung ausgewertet werden. Dieser sekundäre Vergleich isoliert keinen Persönlichkeitseffekt: Aufgabenanweisung, Gesprächsinitiative und Rollenprofil unterscheiden sich gemeinsam. Nicht behaupten, diese Erhebung belege Chat gegenüber klassischer Filter-/Stichwortsuche.

Der angestrebte Beitrag ist die selbst gestaltete Gesprächsführung und Erklärung von Empfehlungen in einer Jobsuche, einschließlich beobachteter Nutzung der Gestaltungsmöglichkeit. C sucht seit der Änderung vom 21. September fest ausgewogen. Neuheit gegenüber verwandten Conversational-Recommender-Arbeiten muss im Paper ausgearbeitet werden; allein der Einsatz eines LLM oder eine große Stichprobe ist kein Neuheitsnachweis.

## Bedingungen

| Bedingung | Beratung | Verfügbare Änderung |
| --- | --- | --- |
| A | Basissystem; standardmäßig kein Systemprompt, optional separat versionierter A-Prompt | Suchprofil und Suchwünsche; keine wählbare Persönlichkeit |
| B | Fester Top-Berufsberater mit RAG-Auftrag | Suchprofil und Suchwünsche; Beratung nicht veränderbar |
| C | Selbst gestaltete Beratung auf derselben Berufsberater-Basis; Suchfokus fest ausgewogen | Name, Gesprächseigenschaften und Hinweise selbst gestalten; keine Auswahl des Suchfokus |

B verwendet ausschließlich den Top-Berufsberater; C beginnt mit dessen fachlichem RAG-Auftrag und gestaltet die sichtbare KI-Konfiguration selbst. Alle Gruppen verwenden dasselbe Modell-Snapshot, denselben Denkaufwand, Datenbestand, BM25/E5/RRF und Top-20-Pool. Scores, Begründungen und Score-Sortierung sind überall vorhanden. Zunächst erscheinen die ersten zehn Stellen; die übrigen bis zu 20 lassen sich mit „Weitere Stellen anzeigen“ öffnen. Es gibt keine Mindestscore-Schwelle. In der vorgesehenen Ausgangsfassung ist A bewusst leer und erhält damit keine Rollen- oder Beratungsanweisung; eine administrativ geänderte A-Fassung bildet eine getrennt zu berichtende Promptrevision. Daraus entstehende Qualitäts- und Fehlerratenunterschiede gehören zum sekundär untersuchten Gesamtpaket.

### Entwicklungsänderung vom 21. September 2026: C sucht fest ausgewogen

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

### Entwicklungsänderung vom 14. September 2026: Beratung v2

`evidence-advisory-v2` konkretisiert die Entscheidungshilfe in B/C: Verknüpfung von Profil und Anzeigenbelegen, wichtigste offene Voraussetzung, situationsbezogener nächster Schritt und Vergleich anhand derselben Kriterien. C ergänzt diese Berufsberater-Basis durch die selbst gestaltete Konfiguration. Mit `explicit-priority-v3` steuert ausschließlich der explizite Suchfokus die ergänzenden Gewichte; Gesprächseigenschaften beeinflussen den Ton. Fachpassung (60 %) und Profilpräferenzen (15 %) bleiben vorrangig, die übrigen 25 % bilden den gewählten Schwerpunkt ab.

Gemeinsame Fehlerkorrekturen gelten für alle aktuellen Gruppen: kein 600-Zeichen-Limit im Ausgabeschema, serverseitige Schutzgrenze von 6.000 Zeichen und Zurückweisung von Fehlerobjekten als Beratungsantwort. Modell-Snapshot, Denkaufwand und Tokenbudgets bleiben gleich. Dies garantiert weder vollständige Modellantworten noch bessere Ergebnisse; die technische Prüfung verwendet simulierte API-Antworten.

Diese Änderungen wurden nach Einsicht in den bisherigen technischen Pilotversuch entwickelt. Dessen Ergebnisse sind Entwicklungsdaten und kein unabhängiger Wirksamkeitsnachweis der neuen Version. Originaldateien bleiben erhalten. Vor einer neuen Erhebung den endgültigen Release festschreiben; Teilnahmen vor und nach diesem Wechsel anhand der gespeicherten `release_id` getrennt auswerten. Gleiche Experiment-/Fragebogennamen allein erlauben kein Pooling über geänderte Interventionen. `advisory_version` und `scoring_version` stehen zusätzlich im Release-Manifest. Details: `research/development/2026-09-14-advisory-v2/README.md`.

### Entwicklungsänderung vom 18. September 2026: gezielte Rückfragen

`ranking-followup-v3` ergänzt B/C um eine konkrete Rückfrage am Ende der Suchansprache und jeder Beratungsantwort. Der Berufsberater klärt offene berufliche Prioritäten, um Stellen zu gruppieren oder neu zu sortieren. Die Frage orientiert sich an belegten Unterschieden der Stellen und bereits genannten Wünschen. Eindeutige kurze Antworten werden im Gesprächskontext als Profilpräferenz oder ausdrücklich belegte Fähigkeit übernommen; Unentschlossenheit und Gegenfragen ändern das Profil nicht. Präferenzen führen zur Neubewertung, neue vorhandene Fähigkeiten zur erneuten Suche. Persönlichkeitsgewichte werden dadurch nicht verändert.

Nach Ausschöpfung der drei Studiennachrichten wird keine weitere Rückfrage verlangt; auf den eigenständigen Testseiten gilt dieses Limit nicht. Bereits beantwortete Fragen, ausdrücklich abgelehnte Rückfragen und künstliche Fragen ohne Entscheidungshilfe sollen entfallen. Dies sind Modellinstruktionen und keine Garantie jeder einzelnen Ausgabe. A erhält keine Pflicht zur proaktiven Rückfrage. B gegen A vergleicht damit auch unterschiedliche Gesprächsinitiative; der primäre Vergleich C gegen B bietet in beiden Gruppen dieselbe Rückfragelogik. Modell, Denkaufwand, Bewertungsformel und Fragebogen bleiben unverändert. Der Release speichert die neue `advisory_version` und die geänderten Prompt-/Vorlagen-Hashes. Vorherige Teilnahmen nicht ungeprüft mit diesem Stand zusammenfassen. Technische Stichproben sind Entwicklungsprüfungen, kein Nachweis einer optimalen Rangfolge.

## Zuteilung und Ablauf

- Zwischenpersonenvergleich; neue Einwilligungskennungen erhalten serverseitig mit Wahrscheinlichkeit 1/3 A, B oder C. Transaktion und eindeutiger Schlüssel sichern eine stabile Zuteilung auch bei parallelen Anfragen. Das ist einfache Randomisierung, keine garantierte exakte Drittelung.
- Dieselbe knappe Aufgabe für alle: Suchprofil angeben, Stellen ansehen und mindestens eine eigene inhaltliche Frage im Chat stellen bzw. einen Suchwunsch präzisieren. Keine Pflicht, positive Rückmeldungen zu geben. C durchläuft den Selbstgestaltungsweg; eine inhaltliche Veränderung der vorgeschlagenen Ausgangskonfiguration wird gesondert erfragt.
- Vor Systembeginn: Nutzung von Jobportalen und KI-Chats in den letzten sechs Monaten. Antwortbereiche: nie, seltener als wöchentlich, wöchentlich aber nicht täglich, täglich; zusätzlich keine Angabe.
- Während einer Suche nur Fakten: demografische Angaben und Suchvorhaben. Bewertungen des Systems, Chats und der Persönlichkeitswirkung werden erst nach der Nutzung gestellt.
- Gemeinsame Ergebnisfragen stehen vor bedingungsspezifischen Fragen. Antworten werden fortlaufend gespeichert. Mindestens eine erfolgreich beantwortete eigene Chatnachricht öffnet die nachfolgenden Bewertungsseiten; eine automatische Begrüßung zählt nicht.
- In allen drei Umfragegruppen sind pro Teilnahme höchstens drei erfolgreich beantwortete eigene Chatnachrichten möglich. Fehlgeschlagene Anfragen zählen nicht; Neuladen und neue Suchsitzungen setzen den teilnahmebezogenen Zähler nicht zurück. Formularänderungen ohne Nachricht zählen nicht als Chatnachricht. Das Limit wird serverseitig geprüft und im Release-Manifest dokumentiert; historische Teilnahmen mit anderem Interaktionsumfang sind entsprechend zu unterscheiden.
- `/test/a`, `/test/b` und `/test/c` sind getrennte Demonstrationszugänge. Sie liefern keine Studienzuweisungen, Umfrageantworten oder Nutzungsmetriken der Studie.
  Auf diesen Testseiten ist die Anzahl eigener Chatnachrichten unbegrenzt.

Vor der Haupterhebung ein kleiner kognitiver Pretest, beispielsweise 6–10 Personen mit unterschiedlichen Fachrichtungen und Endgeräten: Aufgabenverständnis, Unterschied zwischen festem Berufsberater und Selbstgestaltung, Skalenanker und Warte-/Fragenführung prüfen. Diese Zahl ist ein Vorschlag für den Pretest, keine statistische Fallzahl für den Gruppenvergleich. Pretestdaten nicht als reguläre Hauptstudiendaten zusammenfassen.

## Fragebogenkürzung und Versionsgrenze

V11 enthält 15/20/21 sichtbare Fragen für A/B/C, einschließlich der beiden
optionalen Felder Fachrichtung und Feedback. Inhaltlich entspricht er V10; die
Gruppenbezeichnungen und die C-Selbstauskunft wurden an die neue Behandlung angepasst.
Gegenüber V9 entfallen weiterhin
**ausschließlich** `search_ease`, `express_search_needs`, `adapt_search_ease`,
`template_selection_ease` und `personality_setup`. Diese Nebenmaße wurden zur
Verringerung der Befragungslänge entfernt; sie sind nicht als identische Konstrukte
zu den verbleibenden Fragen zu verstehen.

Das primäre Einzelitem sowie Nutzen von Chat, Score, Begründungen, Gesprächsstil
und Bewertungsschwerpunkten bleiben unverändert. Suchaufwand, zukünftige
Nutzungsabsicht, berichtete Suchwunschänderung, Verständnis/Wahrnehmung der
Persönlichkeit und die Selbstauskunft zur tatsächlichen Veränderung der vorgeschlagenen Ausgangskonfiguration in C bleiben ebenfalls erhalten.
Die Selbstgestaltungsmetadaten ersetzen die Selbstauskunft nicht: `custom` kann
auch bei vorlagenidentischen Werten erfasst sein. Operationszähler ersetzen
keine Selbstauskunft darüber, ob Suchwünsche verändert wurden.

Die vorherigen Kohorten behalten ihre Fragebogen und Systembedingungen. Neue Teilnahmen erhalten `diana-abc-v4` / `diana-v11`. Trotz identischem primären Item werden V11 und die historischen V10/V9-Kohorten wegen unterschiedlicher Behandlungen nicht gepoolt. Das Offline-Skript muss V11/V4 ausdrücklich als aktuellen Standard verwenden; ältere Stände bleiben separat.

## Primärer Endpunkt

Das vorab gewählte **Einzelitem** `system_usefulness` lautet: „Wie hilfreich war das System für die Durchführung deiner Suche?“ Werte 1–10, mit identischen Endpunkten in A/B/C. Lesbarer Export: `v11_system_nutzen`; technische Spalte: `v11_system_usefulness`.

Primäre Schätzgröße ist der Mittelwertunterschied **C minus B**. Zweiseitiger Welch-t-Test mit α=0,05 und 95%-Konfidenzintervall für die Differenz. Zusätzlich Gruppengrößen, Mittelwert, Standardabweichung, Median und Verteilung sowie Hedges g berichten. Die Interpretation des ordinalen Einzelitems als quasi-metrisch ist eine Analyseannahme. Keine nachträgliche Zusammenrechnung beliebiger Fragen zu einem angeblich validierten Gesamtwert.

Alle Teilnahmen nach ihrer zufälligen Zuteilung auswerten. Eine Person in C gehört auch dann zu C, wenn sie die vorgeschlagene Ausgangskonfiguration inhaltlich nicht verändert. Nicht anhand der Nutzung, positiver Bewertungen oder technischer Geschwindigkeit nachträglich auswählen.

## Fehlende Antworten und Ausschlüsse

Die primäre Analyse verwendet alle gültigen Primärantworten der neuen Kohorte, **auch aus unvollständigen Umfragen**. Sie ist eine Auswertung nach Zuteilung mit verfügbaren Endpunktdaten, keine vollständige Intention-to-treat-Analyse mit ersetzten fehlenden Ergebnissen. Fehlende Antworten bleiben fehlend; „nicht genutzt“ und „nicht beurteilbar“ sind keine Nullwerte. Ausmaß und Gründe des Fehlens je Gruppe sowie vollständige und unvollständige Teilnahmen getrennt berichten. Ergebnisse bei relevant unterschiedlichem Ausfall zwischen Gruppen vorsichtig interpretieren; eine Sensitivitätsanalyse vorab ergänzen, bevor Schlussfolgerungen aus solchen Daten gezogen werden.

Ausgeschlossen werden ausschließlich getrennte Testzugänge, widerrufene/gelöschte Daten, technische Duplikate und andere Protokoll-/Fragebogenversionen. Technische Fehler und Abbrüche sind zu berichten, nicht pauschal als „schlechte Teilnehmer“ zu entfernen. Eine gültige Primärantwort bleibt trotz eines späteren Abbruchs analysierbar. Mehrfachteilnahmen in unterschiedlichen Browsern werden durch die zufällige Teilnahme-ID nicht zuverlässig erkannt; dafür werden keine zusätzlichen Identifikatoren erfunden.

Korrekturen von Einzelantworten nur als belegbare Berichtigungen mit Grund und Änderungsverlauf. Rohstand sichern; keine inhaltliche Anpassung zur Erzielung günstiger Ergebnisse.

## Sekundäre und explorative Analysen

B–A ist der geplante sekundäre Vergleich des gesamten RAG-Berufsberaterprompts mit der separat konfigurierten A-Bedingung. Im Ausgangsstand ist ihr Prompt leer. Falls mehrere A-Revisionen eingesetzt wurden, dürfen sie nicht ungeprüft zu einer Behandlung zusammengefasst werden. Suchaufwand, Chatnutzen, Wiederverwendungsabsicht sowie Score-/Begründungsnutzen sind sekundäre Maße. Berichtete Suchwunschänderung und die Verständlichkeit bzw. Wahrnehmung der Persönlichkeitswirkung beschreiben Nutzung und Intervention. Die Einfachheit der Einrichtung wird in V11 nicht durch ein eigenes Item bewertet. Sekundäre Inferenztests als eigene Familie mit Holm-Korrektur auswerten; unbereinigte Einzel-p-Werte nicht als weitere bestätigte Haupthypothesen präsentieren. C–A und Untergruppen nach tatsächlicher Veränderung sind explorativ.

Der tatsächlich angewendete Weg wird separat erfasst: B als feste `career`-Konfiguration, C als `custom`. Diese Herkunft beweist nicht, dass C sichtbare Felder inhaltlich verändert hat; dafür dient die Selbstauskunft. Zusammenhänge zwischen Veränderung, Laufzeit, Fehlern und Bewertungen nur explorativ berichten.

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
