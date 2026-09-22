# DIANA: Studienprotokoll für den Konferenzbeitrag

Stand: 21. September 2026. Experiment `diana-abc-v6`, Fragebogen `diana-v13`.
Versionierter Protokollentwurf vor der neuen Erhebung, keine externe Präregistrierung.
Die Auswahl und deutsche Adaptation der Framework-Fragen steht in [QUESTIONNAIRE.md](QUESTIONNAIRE.md), die verbindliche Definition in [survey_definition_v13.json](survey_definition_v13.json).

## Forschungsfrage und Vergleich

Welchen zusätzlichen wahrgenommenen Nutzen und Aufwand verursacht eine selbst gestaltbare KI-Beratung gegenüber einem fest eingestellten Top-Berufsberater?

Primärer Vergleich: **C gegen B**, Endpunkt wahrgenommener Nutzen. Sekundär: **B gegen A** als Vergleich des gesamten RAG-Berufsberaterprompts mit dem Basissystem. C gegen A und Untergruppen nach tatsächlich vorgenommenen Anpassungen bleiben explorativ.

| Gruppe | Angebot |
| --- | --- |
| A | Basissystem ohne wählbare Persönlichkeit; standardmäßig leerer, administrativ versionierbarer Systemprompt |
| B | Fester Top-Berufsberater mit RAG-Auftrag und konkreten Rückfragen |
| C | Derselbe fachliche Berufsberater-Auftrag mit selbst gestaltbarem Namen, Gesprächseigenschaften und Freitexthinweisen; Suchfokus fest ausgewogen |

Alle Gruppen verwenden denselben Modell-Snapshot, Datenbestand, BM25/E5/RRF und Top-20-Pool sowie dieselbe numerische Bewertungsformel `fixed-balanced-v4` (60/15/7/6/6/6 Prozent). Alle zeigen Scores, Begründungen und zunächst zehn Stellen; weitere bis zu 20 sind aufklappbar. Es gibt keine Mindestscore-Schwelle.

**Gleiche Gewichte garantieren keine identischen Bewertungen oder Rankings.** Die jeweiligen Prompts und generative Variation können Teilbewertungen beeinflussen; neue Suchangaben können das Ranking ändern. B–A isoliert keinen reinen Persönlichkeitseffekt, da sich auch RAG-Auftrag und Gesprächsinitiative unterscheiden. Änderungen an administrativen Prompts werden als eigene Behandlungsfassung dokumentiert. Diese Erhebung hat keinen zeitgleichen Filter-/Stichwortsuch-Kontrollarm; eine frühere Bedarfserhebung ersetzt ihn nicht.

## Zuteilung und Ablauf

- Neue Einwilligungskennungen werden serverseitig mit Wahrscheinlichkeit 1/3 A, B oder C zugeteilt; die Zuordnung ist dauerhaft und transaktional gesichert. Keine garantierte exakte Drittelung.
- Vier kurze Kontextangaben vor der Nutzung: aktuelle Studien-/Ausbildungssituation, optionale Fachrichtung, Erfahrung mit Jobportalen und KI-Chatbots. Alter und Geschlecht werden nicht mehr erhoben. Diese Angaben verändern das Matching nicht und werden nicht an das LLM übergeben.
- Dieselbe Aufgabe: ein realistisches Suchprofil erstellen, Stellen und Begründungen betrachten, genau drei erfolgreich beantwortete eigene Nachrichten zu Stellen oder Suchwünschen senden. Keine Pflicht zu positiven Bewertungen. Automatische Begrüßungen und fehlgeschlagene Antworten zählen nicht.
- Das Nachrichtenbudget gilt teilnahmeübergreifend über Suchsitzungen: Neuladen setzt es nicht zurück. Es ist ein fixes Interaktionsbudget, kein Maß freiwilliger Gesprächsintensität. Die separaten Testseiten haben kein Nachrichtenlimit und erzeugen keine Studienantworten/-telemetrie.
- Während der Wartezeit kann ausschließlich das Suchvorhaben beantwortet werden; bereits beantwortete Kontextfragen werden übersprungen. Bewertungsfragen kommen erst nach der Nutzung.
- Alle Gruppen erhalten dieselben 14 Framework-Aussagen und zwei DIANA-Zusatzfragen. Nur C erhält zusätzlich die Selbstauskunft, ob Einstellungen verändert wurden. Gemeinsame Ergebnisfragen stehen zuerst.
- Automatisches Speichern nach jeder Antwort; optionales Freitextfeedback am Ende. A/B sehen 22 Fragen, C 23, einschließlich optionaler Fachrichtung und optionalem Feedback. Die automatisch gesetzte Gruppe zählt nicht dazu.

## Messmodell und Herkunft

ResQue (Pu, Chen & Hu, 2011, Tabelle 2) liefert die drei Nutzenitems sowie Zufriedenheit und Wiederverwendungsabsicht. CRS-Que (Jin et al., 2024, Tabelle 4) liefert je drei Items für User Control und Transparency; seine offizielle Kurzform (Tabelle 5) liefert je ein Item zu Verständnis, Antwortqualität und Aufmerksamkeit im Dialog. So werden die vier Framework-Dimensionen berücksichtigt, ohne den vollständigen Fragebogen beider Arbeiten zu duplizieren.

Alle Aussagen verwenden dieselbe beschriftete Zustimmungsskala **1–7** und zusätzlich „Kann ich nicht beurteilen“. CRS-Que verwendet ursprünglich sieben, ResQue fünf Stufen: ResQue-Skala, deutsche Sprache und Jobsuchkontext sind ausdrücklich Anpassungen. Kein Anspruch einer bereits validierten deutschen Gesamtskala. Jede Frage trägt Framework, Konstrukt und Fundstelle; diese Zuordnung gehört zum Codebuch.

Die beiden DIANA-Zusatzitems erfassen gesamten subjektiven Nutzungsaufwand (einschließlich Warten, Suche und Einrichtung) und die wahrgenommene Gestaltbarkeit des Sprachstils. Sie sind keine validierten Framework-Skalen. Der Suchkontrollwert betrifft Suchwünsche und Empfehlungen, nicht allein die Veränderbarkeit des Sprachstils.

## Auswertung

Drei getrennte Konstrukte: **Nutzen**, **Suchkontrolle**, **Transparenz**. Je Konstrukt wird der Mittelwert nur gebildet, wenn alle drei Antworten numerisch 1–7 vorliegen. Fehlend/nicht beurteilbar bleibt fehlend; keine Nullersetzung oder Mittelung aus weniger Items. Verwaltung und Export liefern Einzelitems, die jeweiligen vollständigen Mittelwerte und gültige Fallzahlen. Diese rechnerische Zusammenfassung ist keine Validierungsbestätigung.

Die drei Gesprächs-Einzelitems werden einzeln ausgewertet; aus ihnen entsteht keine eigene validierte Dialogskala. Zufriedenheit und Wiederverwendung bleiben Einzelitems. Kein Gesamtpunktwert über alle Fragen oder Frameworks. Hoher Aufwand bedeutet mehr Aufwand; er wird nicht stillschweigend umgepolt.

Primärer Endpunkt: vollständiger dreiteiliger Nutzenwert, **C minus B**. Geplant sind Gruppenfallzahlen, Itemverteilungen, Mittelwerte/Streuung, Differenz mit 95%-Konfidenzintervall und Hedges g; ein zweiseitiger Welch-Vergleich ist ein Analyseentwurf. Die quasi-metrische Behandlung des Mittelwerts ist eine Analyseannahme. Vor der Haupterhebung Analyseplan einschließlich Voraussetzungen und Sensitivitätsanalysen festschreiben. `research/analyze_primary.py` bleibt ein historisches Werkzeug für V9–V11 und unterstützt V13 nicht.

Suchkontrolle und Transparenz dienen als sekundäre Wirkungsmaße. Gesprächseindrücke, Zufriedenheit, Wiederverwendung und Aufwand ergänzen sie. Sekundäre Tests als eigene Familie mit vorab festgelegter Korrektur multipler Vergleiche behandeln; keine nachträgliche Auswahl günstiger Items/Endpunkte. Gestaltbarkeit und C-Selbstauskunft sind Manipulations-/Nutzungskontrollen, keine Voraussetzung für Aufnahme in die Analyse. Wer C zugeteilt wurde, bleibt C, auch ohne eigene Änderung.

Ein kognitiver Pretest prüft Formulierungen und Skalenverständnis. Reliabilität und Dimensionalität der drei adaptierten Mehr-Item-Konstrukte müssen vor inhaltlicher Interpretation untersucht werden; schlechte Skalenqualität darf nicht durch ergebnisabhängiges Löschen einzelner Items kaschiert werden. Kein Reliabilitätskoeffizient für ein Einzelitem. Keine Behauptung, das vollständige Strukturmodell der Originalarbeiten repliziert zu haben.

## Fehlende Antworten, Datenreset und Versionen

Der geplante Hauptvergleich verwendet alle verfügbaren vollständigen Nutzenwerte der neuen Kohorte, auch bei später abgebrochenem Fragebogen. Das ist keine vollständige Intention-to-treat-Analyse mit ersetzten fehlenden Werten. Abbrüche, technische Fehler und fehlende Antworten je Gruppe berichten, nicht pauschal ausschließen. Fehlende Messungen bleiben unbekannt.

V13 ersetzt den bisherigen Fragebogen vollständig im Live-System. Alte Antworten und Entwürfe werden auf ausdrücklichen Nutzerwunsch gelöscht, alte Einwilligungskennungen gesperrt. Es gibt keine Fragebogenauswahl, keine Übernahme alter Bewertungen und keine gemeinsame Auswertung mit V12. Historische Definitionen dienen nur offline der Nachvollziehbarkeit in Git; öffentliche Schreibzugriffe akzeptieren ausschließlich V13. Ein Browser mit altem Stand muss neu beginnen.

Ausgeschlossen sind getrennte Testzugänge, widerrufene Daten, technische Duplikate und fremde Kohorten. Die Teilnahme-ID verhindert nicht jede Mehrfachteilnahme über verschiedene Browser. Korrekturen nur als belegbare Berichtigung mit dokumentiertem Grund und Verlauf.

## Fallzahl und Reproduzierbarkeit

Die frühere Planung für andere Einzelitems/Skalen gilt nicht automatisch. Effektgröße, Streuung, Ausfallreserve, relevante Mindestdifferenz und Stoppregel für den neuen Nutzenwert müssen vor Rekrutierung begründet festgelegt werden. Nicht nach zwischenzeitlichen Signifikanzen rekrutieren oder stoppen. Ein technischer Testdatensatz ist keine Evidenz für eine Effektgröße.

Release-Hash, Modell-Snapshot, Experiment, Fragebogenversion, Scoringversion und unveränderliche Promptrevision werden zur Teilnahme dokumentiert. Die neue Fragebogenfassung verändert keine Ranking-, Modell- oder Promptlogik. Die beiden Server sind getrennte Installationen; neue Teilnahmen werden nicht synchronisiert.

Nutzungsverhalten ergänzt den Fragebogen: sichtbare Begründungsintervalle pro Stelle, geöffnete Details, aufgeklappte Karten und erfolgreiche Chatoperationen. Sichtbarkeit ist keine Aufmerksamkeit; sich überlappende Kartenzeiten sind keine Sitzungsdauer. Der Chat-Erfolgszähler ist die gemeinsame Quelle für Gate und Telemetrie; bei genau drei vorgeschriebenen Nachrichten ist er vor allem ein Ablauf-/Fehlermaß. [STUDY-TELEMETRY.md](STUDY-TELEMETRY.md) beschreibt Grenzen und Exporte.

Die separate [Relevanzprüfung](research/human_relevance/README.md) ist ein Offline-Werkzeug. Ohne vollständige Relevanzurteile liefert sie keinen aktuellen Qualitätsnachweis der Rankings. Es werden für diesen Fragebogenumbau keine kostenpflichtigen Modelltests gestartet.

## Quellen und verbleibende Schritte

- Pu, Chen & Hu (2011): [ResQue](https://doi.org/10.1145/2043932.2043962), Tabelle 2, Abschnitt 5.1.
- Jin, Chen, Cai & Zhao (2024): [CRS-Que](https://doi.org/10.1145/3631534), Tabellen 4/5, Abschnitt 5.3 und Appendix A/B.
- [Fragenkatalog, Zuordnung und Adaptation](QUESTIONNAIRE.md).

Vor der Haupterhebung: kognitiver Pretest, endgültiger Auswertungs-/Fallzahlplan und erforderliche institutionelle Freigaben. Der Umbau sichert Quellenbezug und technische Umsetzung, nicht die wissenschaftliche Validierung oder Annahme bei einer Konferenz.
