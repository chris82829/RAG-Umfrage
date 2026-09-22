# DIANA: Studien- und Analyseprotokoll V14

Stand: 22. September 2026. Fragebogen `diana-v14`. **Präregistrierungsvorstufe / Entwurf**, noch nicht als vor der Haupterhebung eingefroren ausgeben. Maßgeblich sind [survey_definition_v14.json](survey_definition_v14.json), [QUESTIONNAIRE.md](QUESTIONNAIRE.md) und der unten beschriebene Analysecode. Die bisherige Version bleibt in Git nachvollziehbar.

## Forschungsfrage und Behandlungen

Welchen zusätzlichen wahrgenommenen Nutzen und Aufwand verursacht eine selbst gestaltbare KI-Beratung gegenüber einem fest eingestellten Top-Berufsberater bei einer dialogischen Jobsuche?

| Gruppe | Angebot |
| --- | --- |
| A | Basissystem ohne wählbare Persönlichkeit; standardmäßig leerer, administrativ versionierbarer Systemprompt |
| B | Fester Top-Berufsberater mit RAG-Auftrag und konkreten Rückfragen |
| C | Derselbe fachliche Berufsberater-Auftrag mit selbst gestaltbarem Namen, Gesprächseigenschaften und Freitexthinweisen; Suchfokus fest ausgewogen |

Alle Gruppen verwenden denselben Modell-Snapshot, Stellenbestand, BM25/E5/RRF-Retrieval, Top-20-Pool und dieselbe numerische Bewertungsformel (60/15/7/6/6/6 Prozent: fachliche Passung, Profilpräferenzen, fachliche Tiefe, Lernen/Entwicklung, Gestaltung/Innovation, Klarheit). Scores und Begründungen werden in allen Gruppen gezeigt; zuerst zehn Stellen, anschließend auf Wunsch bis zu 20. Keine Mindestscore-Schwelle.

Seit dem 22.09.2026 ist der aktive Snapshot `gpt-5.4-nano-2026-03-17`, weiterhin mit
`reasoning.effort=none`. Dies gilt für A/B/C und die separaten Testseiten. Der vorherige
Stand mit `gpt-5.4-2026-03-05` bleibt in Git und historischen Release-Metadaten erhalten;
seine Messwerte sind kein Qualitäts- oder Laufzeitnachweis für Nano. Der Modellwechsel
erzeugt einen neuen Systemstand und muss bei der späteren Auswertung berücksichtigt werden.

Gleiche numerische Gewichte erzwingen keine identischen Teilbewertungen, Rankings oder Antwortzeiten. Die Prompts beeinflussen die generative Bewertung; aktualisierte Suchangaben können den Pool oder dessen Reihenfolge verändern. B gegen A ist ein **Paketvergleich** aus Berufsberatungsauftrag, RAG-Instruktion und Gesprächsinitiative. C gegen B untersucht das Angebot zusätzlicher Selbstgestaltung. Wer C zugeteilt wurde, bleibt C, auch wenn nichts geändert wurde. Ein Vergleich innerhalb C nach tatsächlich berichteter Anpassung ist durch Selbstselektion verzerrt. Die frühere Filter-/Stichwortsuchbefragung ist Kontext, kein zeitgleich randomisierter Kontrollarm.

Die tatsächlichen numerischen Gewichte werden je Bewertung separat vom Prompttext protokolliert. Ein bekannter überholter B-Prompt mit abweichenden Prozentzahlen wird für neue Promptfassungen bereinigt; alte unveränderliche Teilnahmesnapshots bleiben historische Fassungen. Das Erfassungsfeld allein beweist keine richtige Promptfassung: zusätzlich werden Promptrevision und -Hash dokumentiert und der aktive Prompt auf widersprüchliche Gewichtung geprüft.

## Ablauf und Stichprobe

Neue Einwilligungskennungen werden serverseitig mit Wahrscheinlichkeit 1/3 einer Gruppe zugewiesen; Wiederaufruf erhält dieselbe transaktional gespeicherte Zuteilung. Eine genau gleiche Gruppengröße wird nicht garantiert. Getrennte Testseiten erzeugen keine Studienantworten und haben kein Nachrichtenlimit.

Vor den bisherigen Kontextfragen wird erhoben, ob bereits an dieser Studie teilgenommen wurde (Ja/Nein/Unsicher). Anschließend: Ausbildungs-/Studienstand, optionale Fachrichtung, Jobportal- und KI-Chat-Erfahrung. Das Suchvorhaben kann während der Wartezeit beantwortet und aus der eigenen Suche als Vorschlag übernommen werden. Die Aufgabe lautet: realistisches Suchprofil erstellen, Empfehlungen und Begründungen betrachten, genau drei erfolgreich beantwortete eigene Nachrichten schreiben. Automatische Begrüßungen und fehlgeschlagene Anfragen zählen nicht. Das Budget gilt über Suchsitzungen hinweg. Dies standardisiert Interaktionstiefe; es misst keine freiwillige Gesprächsbereitschaft.

Nach der Nutzung folgt der Fragebogen. Automatisches Speichern nach jeder Antwort ermöglicht Auswertung beantworteter Konstrukte auch bei späterem Abbruch. Ein optionales Freitextfeld schließt ab. **A/B: 26 Fragen; C: 27**, einschließlich optionaler Fachrichtung und optionalem Feedback. Gegenüber V13 kommen zwei Vertrauensitems, ein Charakteritem und ein Screening hinzu. Die im Vorschlag genannten 25/26 ließen das zusätzliche Screening ungezählt. E1 „einfache Bedienung“ bleibt weg, um den Fragebogen kompakt zu halten.

Wellen werden bei Beginn mit `study_wave=pretest` oder `main` festgehalten; Wechsel der aktiven Rekrutierung verändert bestehende Kennungen nicht. Die Rekrutierungswelle erhält eine dokumentierte Kennung/Zeitmarke `recruitment_batch`; sie wird nicht aus der späteren Antwortzeit erfunden. Nur Hauptwellen fließen in die geplanten Hypothesentests ein.

## Messmodell und Quellen

Die bestehenden **14 aus Frameworks adaptierten Aussagen** bleiben unverändert: ResQue-Nutzen (3), CRS-Que-Dialogverständnis, Antwortqualität und Aufmerksamkeit (je 1 aus der Kurzform), CRS-Que-Suchkontrolle (3), CRS-Que-Transparenz (3), ResQue-Zufriedenheit (1), ResQue-Wiedernutzungsabsicht (1). V13 enthielt außerdem zwei eigene DIANA-Ratings zu Aufwand und Stilkontrolle sowie die C-Selbstauskunft zur Anpassung. Die pauschale Bezeichnung „17 Framework-Items“ im Vorschlag wird deshalb nicht übernommen.

Neu nach den drei Nutzenitems stehen:

- T1 / `trust_fit`: „Ich vertraue darauf, dass die von DIANA vorgeschlagenen Stellen wirklich zu mir passen.“
- T2 / `trust_credibility`: „Die Einschätzungen von DIANA zur Passung erschienen mir glaubwürdig.“

Dieses Paar ist an die Dimension Confidence & Trust in ResQue und Trust & Confidence in CRS-Que angelehnt. Die Originalskalen enthalten vier bzw. sechs Items; deren offizielle CRS-Kurzform ein Item. **Diese zwei deutschen Aussagen sind eine eigenständig adaptierte Zweiergruppe, keine vollständig übernommene oder bereits validierte Originalskala.** T1 verbindet Vertrauen und erwartete Passung; T2 erfasst Glaubwürdigkeit. Kognitiver Pretest prüft insbesondere, ob diese Trennung verstanden wird. Die Originaltabellen wurden am 22. September 2026 gelesen und visuell geprüft; Einzelbelege in [V14-METHODS.md](V14-METHODS.md).

Nach den drei Dialogitems folgt für alle Gruppen:

- M1 / `perceived_character`: „Die Beratung im Chat hatte für mich einen erkennbaren eigenen Charakter (z. B. Tonfall, Persönlichkeit).“

M1 ist ein eigenes Manipulationscheck-Einzelitem, keine validierte Humanness-Skala. Erwartet wird A < B und A < C; eine zwingende Ordnung B < C wird nicht vorausgesetzt, weil eine selbst gestaltete Persönlichkeit auch sachlicher ausfallen kann. Alle Aussagen haben dieselbe beschriftete Zustimmungsskala 1–7 plus „Kann ich nicht beurteilen“. Pflichtitems erfordern eine Auswahl, erlauben aber diese Nichtbeurteilbarkeit. ResQue verwendete ursprünglich fünf, CRS-Que sieben Stufen; Sprache, Jobsuchkontext und ResQue-Skalenweite sind dokumentierte Adaptationen.

Vier getrennte Mittelwerte: Nutzen, Kontrolle, Transparenz mit **je drei** gültigen ganzzahligen Antworten 1–7; Vertrauen mit **beiden** gültigen Antworten 1–7. Fehlend oder nicht beurteilbar bleibt fehlend. Keine Nullersetzung, keine Mittelung aus weniger Items, keine gemeinsame Summe aller Frameworks. Die drei Dialogratings, Zufriedenheit, Wiedernutzung, Aufwand, Stilkontrolle und M1 bleiben Einzelitems. Hoher Aufwand bedeutet mehr Aufwand, keine automatische Umkehrung.

## Fallzahl und Stoppregel – vor Hauptrekrutierung zu vervollständigen

Geplante Irrtumswahrscheinlichkeit 0,05 zweiseitig und Power 0,80 für H1. Der angemessene minimal relevante Effekt (SESOI), eine begründete Ausfallreserve und konkrete Start-/Endzeit der Rekrutierung sind noch **offen** und werden nicht nachträglich als festgelegt dargestellt.

Rechenbeispiel: d = 0,35 benötigt bei balancierten Gruppen 130 auswertbare Personen **je B und C**. Bei gleich großer Gruppe A ergibt das etwa 390 auswertbare Teilnahmen insgesamt; 400 begonnene Teilnahmen garantieren dies wegen Ausfällen und zufälliger Zuteilung nicht. Das nichtzentrale t-Modell entspricht `statsmodels.stats.power.TTestIndPower`; es ist eine Planung unter Gleichvarianz und kein exakter Powernachweis für jede mögliche Welch-Varianzkonstellation. Die Näherung 16/d² wird nicht als exakte Berechnung ausgegeben. `power_plan()` liefert kontinuierliche und aufgerundete Fallzahlen sowie den detektierbaren Effekt bei n = 130. Keine nachträgliche beobachtete Power aus gefundenen Effektgrößen.

**Stoppregel:** ein vor Versand festgelegtes Zeitfenster, unabhängig von Zwischen-p-Werten. „72 Stunden nach Versand“ ist bislang ein Beispiel, kein bereits bestätigter Termin. Keine automatische Schließung ohne gesetztes Datum. Vor Hauptrekrutierung SESOI, Ausfallreserve, Versand-/Endzeit, Analysecode, Systemstand und Promptstände gemeinsam versionieren; der freigegebene Git-Hash bzw. eine zeitlich nachvollziehbare OSF-Registrierung dokumentiert den Freeze. Ein heutiger Commit allein ist kein Beleg einer bereits extern präregistrierten Studie.

## Analysepopulation und Ausschlüsse

Ausgewertet werden ausschließlich V14-Hauptwellen. Prätest, getrennte Testzugänge, widerrufene Daten, technische Duplikate und andere Fragebogenversionen werden ausgeschlossen. Die Herkunft jeder Welle muss vorhanden sein; fehlende Wellenangabe wird nicht stillschweigend als Hauptstudie behandelt. Kein Zusammenführen alter und neuer Skalen.

Der Hauptvergleich nutzt alle verfügbaren vollständigen Nutzenwerte, auch bei später unvollständigem Fragebogen. Das ist ein Available-Case-Vergleich nach zugewiesener Gruppe, keine vollständige Intention-to-treat-Analyse mit Imputation. Pro weiterem Endpunkt wird dessen eigene vollständige Itemgruppe genutzt. Fehlende Werte und Abbruchraten werden nach Gruppe dokumentiert.

Ein **endgültig nicht wiederhergestellter**, dokumentierter technischer Fehlschlag vor angemessener Systemexposition kann gemäß vor Entblindung protokollierter Entscheidung ausgeschlossen werden. Ein einzelner Timeout oder eine später erfolgreich wiederholte Anfrage reicht nicht. Dafür kann die separate Analysearbeitskopie `technical_exclusion=1` mit verpflichtendem `technical_exclusion_reason` enthalten; Produktivantworten bleiben unverändert. Die Anwendung löscht nicht automatisch Teilnahmen aufgrund eines Fehlercodes. Ein unabhängiger, nach Antwortinhalten optimierter Ausschluss ist unzulässig.

Wiederholungsteilnahmen werden zunächst eingeschlossen und zusätzlich sensitiv behandelt. Hauptsensitivität entfernt `previous_participation=yes`, belässt Unsichere; eine weitere Darstellung verwendet nur ausdrücklich erstmalige Teilnahmen (`no`). Selbstbericht ersetzt keine verlässliche technische Duplikaterkennung. Keine IP-Sammlung oder Gerätefingerprints für diesen Zweck.

## Primärer Test, sekundäre Familie und explorative Analysen

**H1:** C hat höheren wahrgenommenen Nutzen als B. Getestet wird die Mittelwertdifferenz **C minus B zweiseitig mit Welch**, α = 0,05. Die gerichtete Erwartung wird nicht nach Datenlage umgedreht; ein signifikanter negativer Effekt bestätigt H1 nicht. Der dreiteilige Mittelwert wird näherungsweise metrisch behandelt.

Der Widerspruch „Welch festlegen, dann mittels Levene zwischen Student und Welch wählen“ wird aufgelöst: **Welch ist unabhängig von Levene fest vorgegeben.** Levene kann rein diagnostisch berichtet werden. Mann–Whitney-U wird immer als Sensitivität berechnet, ohne vorgelagerten Normalitäts- oder Schiefetest zur Auswahl. Er prüft Verteilungsunterschiede; ohne gleiche Verteilungsformen ist dies kein reiner Mediantest.

Die sekundäre Familie enthält **genau drei** zweiseitige Welch-Tests mit Holm-Korrektur über alle drei:

1. Suchkontrolle: C minus B.
2. Transparenz: C minus B.
3. Nutzen: B minus A, ausdrücklich Paketvergleich.

Nicht berechenbare sekundäre Tests reduzieren die vorab definierte Familie nicht. Explorativ und ohne Anspruch einer unabhängigen konfirmatorischen Familie: Nutzen C minus A; Nutzen innerhalb C nach selbstberichteter Anpassung; deskriptive Werte für Zufriedenheit, Wiedernutzung, Aufwand, Stilkontrolle und Dialogeinzelitems. Wiederholungssensitivitäten ersetzen das Hauptergebnis nicht.

Je Vergleich: n, Mittelwert, SD, unstandardisierte Differenz mit 95%-Welch-t-Intervall, exakter numerischer p-Wert und Hedges g mit 95%-Intervall. g verwendet die gepoolte SD und die Gamma-basierte Kleinstichprobenkorrektur; bei ungleichen Varianzen ist der Standardisierungsbezug ausdrücklich zu beachten. Das g-Intervall wird mit 5.000 unabhängigen gruppenweisen Perzentil-Bootstrap-Ziehungen und deterministischem Seed berechnet. Bei mehr als 1 % degenerierten Ziehungen entfällt das Intervall mit Begründung. Bei zu wenig Daten/Nullvarianz werden fehlende Werte statt irreführender 0-Werte oder NaN ausgegeben.

## Manipulationscheck und Reliabilität

M1: Deskriptive Verteilungen und Gruppenmittel/-mediane; ein vorab gewählter **Kruskal–Wallis-Test** über A/B/C, ohne nachträgliche Auswahl des günstigeren ANOVA-Verfahrens. Die asymptotische Berechnung wird erst bei mindestens fünf gültigen Werten je Gruppe ausgegeben. Erwartete Richtung A < B und A < C anhand der Verteilungen einordnen. Keine signifikanzabhängige Entfernung von Personen, kein Austauschen des Primärtests und keine automatische Freigabe/Verwerfung von H1 durch M1. Ein nicht signifikanter Unterschied belegt weder identische Wahrnehmung noch fehlende Persona-Wirkung; geringe Power oder Messfehler sind alternative Erklärungen.

Cronbach-α für Nutzen, Kontrolle, Transparenz und die adaptierte Vertrauenszweiergruppe, gepoolt und je Gruppe. Bei Vertrauen zusätzlich Interitemkorrelation und Spearman–Brown. α < 0,7 wird als Einschränkung diskutiert; Items oder Endpunkte werden deshalb nicht nachträglich ergebnisabhängig entfernt. Einzelitems erhalten keinen Reliabilitätskoeffizienten. Auch hohe interne Konsistenz beweist weder Eindimensionalität noch Konstruktvalidität; das komplette Strukturmodell der Originalframeworks wird nicht als repliziert beansprucht.

## Nutzungsmetadaten und Grenzen

Pro Teilnahme/Welle: `study_wave`, `recruitment_batch`, `viewport_class` (mobile/desktop nach tatsächlichem UI-Breakpoint), `furthest_step_reached` (monoton von Einwilligung über Profil, erste Suche und Chat bis Fragebogenbeginn/-ende). Keine Rückstufung beim Zurücknavigieren. Pro Operation: Erfolg, Dauer, `error_code`, `error_stage`, angewendeter Gewichtsvektor bei Bewertungen. Veränderte Darstellungsbreite ist eine grobe UI-Kategorie, kein Fingerprint.

Bestehende Sichtbarkeitsintervalle für Begründungen, geöffnete Stellendetails und Chatereignisse bleiben ergänzende Prozessmaße. Sichtbarkeit ist keine Aufmerksamkeit; gleichzeitig sichtbare Karten erzeugen überlappende Zeiten. Drei vorgeschriebene erfolgreiche Nachrichten sind ein Ablaufmaß, kein frei gewähltes Engagementmaß. Metadaten können deskriptiv bzw. als ausdrücklich explorative Kovariaten genutzt werden; keine datengetriebene Ersetzung des Primärvergleichs.

Mit Teilnahme-IDs verknüpfte Antworten und Nutzungsmetadaten sind **pseudonymisierte, nicht automatisch anonyme Daten**. Der Vorschlag „keine zusätzlichen personenbezogenen Daten / keine Datenschutzfolgenabschätzung nötig“ wird nicht als rechtliche Feststellung übernommen. Datenschutzhinweise müssen die zusätzlichen Zwecke/Felder verständlich benennen. Einwilligung, Aufbewahrung und institutionelle Voraussetzungen gelten weiterhin. Keine neuen Profile oder Chatvolltexte werden allein für diese Metadaten archiviert.

## Separate menschliche Belegtreueprüfung

40–80 Profil–Anzeige–Begründungs-Paare, zufällig innerhalb A/B/C mit gleichen Quoten (±1), unabhängig vom Live-Fragebogen. Zwei unabhängige Rater bewerten belegte Aussagen in drei Stufen (vollständig/teilweise/nicht belegt). Vorab Training an gesonderten Beispielen, Gruppenkennungen maskieren, Ausgangsurteile vor Konsensbildung erhalten. Ungewichtetes Cohen-κ und gruppenweise Verteilungen berichten; Bewertungen desselben Paares sind keine unabhängigen Einzelbeobachtungen.

Die Quelldaten müssen bereits synthetisch oder für diese separate Forschung verfügbar sein. [research/v14/faithfulness.py](research/v14/faithfulness.py) greift weder auf Live-Sitzungen noch auf APIs zu. Keine automatisch erzeugten LLM-Urteile als menschlich deklarieren. Es gibt noch **keine durchgeführte menschliche Validierung**. Belegtreue beweist keine Rankingrelevanz, Auswahlqualität oder Nutzensteigerung. Die älteren Relevanzskripte bleiben getrennt.

## Reproduzierbarkeit und Umsetzung

Analyse: [research/v14/analyze.py](research/v14/analyze.py), Anleitung und Rater-Rubrik: [research/v14/README.md](research/v14/README.md). Technische Tests nutzen synthetische Fixtures und sind keine Teilnehmenden-Evidenz. JSON/Markdown-Ausgabe dokumentiert Berechnungsverfahren und Eingabeprüfsumme. Die Verwaltung löst Statistik nur auf ausdrücklichen Aufruf aus; solange der Plan Entwurf ist, bleiben Resultate vorläufig/explorativ. Kein wiederholtes Abfragen rechtfertigt einen p-Wert-gesteuerten Studienabbruch.

Die beiden Server haben getrennte Datenbanken; ihr Codegleichstand bedeutet keine synchronisierte Stichprobe. Freigegebenen Release-Hash, Modell-Snapshot, Fragebogenversion, Scoringversion, Promptrevisionen/-Hashes und Datensatzstand berichten. V13 wird nicht mit V14 gepoolt; historische Dateien bleiben als Entwicklungsnachweis erhalten. Es gibt keine Fragebogenauswahl für Teilnehmende oder in der aktuellen Auswertung.

Vor Hauptrekrutierung verbleiben: kognitiver Pretest (einschließlich Vertrauenspaar/M1), begründete SESOI und Ausfallreserve, konkretes Rekrutierungsfenster und nachvollziehbarer Freeze. Der technische Umbau ersetzt diese Entscheidungen oder erforderliche institutionelle Freigaben nicht und garantiert keine Konferenzannahme.

Die maschinenlesbare Planfassung steht in [research/v14/analysis_plan.json](research/v14/analysis_plan.json). Statistikberichte enthalten deren vollständigen Inhalt und SHA-256. Eine spätere dokumentierte Festlegung kann dort ohne Änderung des Analysealgorithmus vorgenommen werden; für den Status `frozen_before_main` müssen SESOI, Ausfallreserve, Zielzahl, Git-Referenz sowie zeitlich geordnete Freeze-/Rekrutierungsdaten vorliegen. Dies prüft Konfigurationskonsistenz, nicht rückwirkend die Wahrheit einer behaupteten Präregistrierung. Unterschiedliche Promptrevisionen oder Systemstände innerhalb eines Arms werden im Bericht offengelegt und verhindern die stillschweigende Interpretation als homogene konfirmatorische Behandlung.
