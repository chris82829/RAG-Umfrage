# DIANA – Prüfauftrag für Claude und vollständiger Fragenkatalog

Stand: 21. September 2026. Grundlage ist der gelesene lokale Quellcode einschließlich der noch nicht veröffentlichten Änderung „C sucht immer ausgewogen“. Der Stand der beiden Server und ihrer administrativ gespeicherten Prompts wurde hierfür nicht überprüft. Die nachfolgenden Promptbeschreibungen beziehen sich auf die vorgesehenen Ausgangskonfigurationen. Es wurden für dieses Briefing keine Anwendungseinstellungen geändert oder neuen Modelltests durchgeführt.

## Kopiervorlage für Claude

Du bist ein kritischer wissenschaftlicher Gesprächspartner mit Erfahrung in Information Retrieval, Conversational Search, Recommender Systems und empirischer Informatikforschung. Beurteile mein nachfolgend beschriebenes Promotionsprojekt und Studiendesign. Ich möchte eine ehrliche Einschätzung der Neuheit, Aussagekraft und Eignung für einen Konferenzbeitrag, insbesondere für ACM CHIIR 2027: https://chiir2027.github.io/ . Recherchiere für Aussagen über Konferenzanforderungen und verwandte Arbeiten die jeweiligen Originalquellen. Trenne nachgewiesene Tatsachen, methodische Annahmen und deine Vorschläge. Implementiere nichts und stelle keine Annahmezusage in Aussicht.

### Projekt und Forschungsinteresse

Ich promoviere in Informatik an der TH Nürnberg. Mein System heißt DIANA. Es erforscht, wie sich Such- und Empfehlungssysteme an Ziele, Fähigkeiten und Wünsche einzelner Menschen anpassen lassen. Am Beispiel der Jobsuche verbindet es persönliche Angaben, Matching, verständliche Begründungen und die Möglichkeit, Empfehlungen im Dialog nachzuvollziehen und mitzugestalten.

Mein übergeordnetes Interesse ist der Mehrwert von dialogbasierter und personalisierter Suche. Eine frühere Umfrage zu Filter- und Stichwortsuche ist bereits vorhanden. Diese Vorarbeit dient der Motivation; sie ist keine gleichzeitig randomisierte Kontrollgruppe der aktuellen Studie. Die aktuelle Studie vergleicht drei dialogbasierte Varianten. Damit lässt sich kein unmittelbarer kausaler Vorteil gegenüber einer klassischen Jobbörse nachweisen.

Ich möchte mehr untersuchen als die Bedienbarkeit einer Oberfläche. Zugleich befürchte ich, dass drei unterschiedlich konfigurierte LLM-Berater allein noch keinen hinreichenden wissenschaftlichen Neuheitsbeitrag ergeben. Bitte prüfe, ob mein sinnvollster Beitrag im Gesamtsystem, in der Selbstgestaltung der Beratung oder in deren Wirkung auf den Such- und Entscheidungsprozess liegt.

### Tatsächlich implementierte Sucharchitektur

Die Webanwendung verwendet React, Flask und SQLite. Sie bietet ein Suchprofil, Stellenkarten mit Score und Begründungen sowie einen streamenden Chat. Der dokumentierte Originalbestand des technischen Piloten umfasst 8.537 Stellenanzeigen; der tatsächlich eingesetzte Bestand wird über Anzahl und Prüfsumme im Release dokumentiert.

Das Profil enthält Suchziel, Fähigkeiten, Wünsche, Stellenart und optional Lebenslaufinformationen. Die Stellenart ist ein harter Vorfilter. Ort, Arbeitsmodell und gewünschte Stunden werden als weiche Präferenzen berücksichtigt. Demografische Umfrageangaben sind davon getrennt und werden nicht für das Matching an das LLM gegeben.

Nach dem Vorfilter laufen lexikalische BM25-Suche und semantische Suche mit `intfloat/multilingual-e5-large-instruct`. Die Ranglisten werden mit Reciprocal Rank Fusion (k=60) verbunden. Beide Suchzweige liefern bis zu 20 Treffer; aus der Fusion gehen höchstens 20 Kandidaten in die LLM-Bewertung. Bei identischem Profil teilen A/B/C diese Retrievalgrundlage. Im weiteren Gespräch können unterschiedliche Profiländerungen auch zu unterschiedlichen Suchergebnissen führen.

Das LLM ist im Code auf `gpt-5.4-2026-03-05` mit `reasoning_effort=none` festgelegt. Es bewertet die vorausgewählten Kandidaten und erzeugt Begründungen. Es liest und bewertet nicht sämtliche über 8.000 Anzeigen einzeln. Der Server berechnet aus sechs LLM-Teilbewertungen einen gewichteten Score von 1 bis 100 und sortiert die Ergebnisse. Diese Scores sind keine kalibrierten Einstellungswahrscheinlichkeiten und keine unabhängig validierten Relevanzurteile.

Alle aktuellen Gruppen erhalten Scores, Begründungen und eine nach Score sortierte Liste. Zunächst werden zehn Stellen angezeigt, über „Weitere Stellen anzeigen“ bis zu 20. Es gibt keine Mindestscore-Schwelle für die Anzeige. Die früher einmal zufällige Ergebnisreihenfolge von A gehört nicht zum aktuellen Stand.

Im Chat kann das System Fragen beantworten, den vorhandenen Kandidatenpool neu bewerten oder bei einem veränderten Suchziel bzw. relevanten Profiländerungen neu suchen. B/C sollen anhand tatsächlicher Stellenunterschiede konkrete Rückfragen stellen, deren Antworten die nächste Sortierung unterstützen. Eine reine Frage soll nicht automatisch eine neue Suche auslösen.

### Aktuelle drei Bedingungen

**A – Basissystem:** Standardmäßig wird keine Systemnachricht an das LLM geschickt. Es erhält dennoch Nutzerprofil, Stellenanzeigen, Chatkontext und ein strukturiertes Antwortschema. A ist daher weder eine klassische Stichwortsuche noch vollständig unpersonalisiert: Das Nutzerprofil beeinflusst bereits Retrieval und Bewertung. Es gibt keine wählbare KI-Persönlichkeit und keine explizite Pflicht zur proaktiven Berufsberatung. Ein eigener A-Systemprompt kann in der Verwaltung hinterlegt werden; sein Ausgangswert ist leer.

**B – fester Top-Berufsberater:** Ein eigener Systemprompt erklärt den RAG-Auftrag, möglichst passende Stellen zu finden. Der Berater soll kurze, präzise, beleggestützte und proaktive Antworten geben, normalerweise zwei bis vier kurze Sätze und bei Vergleichen ungefähr höchstens 80 Wörter. Wo sinnvoll, stellt er eine konkrete offene Rückfrage zum Gruppieren oder Neusortieren der Stellen. Profil und Suchwünsche sind veränderbar, die Persönlichkeit ist fest. Die frühere Auswahl eines Fachexperten existiert in der aktuellen Bedingung nicht mehr.

**C – selbst gestaltbare Beratung:** Die fachliche Berufsberater-/RAG-Basis bleibt bestehen. Nutzer können einen Namen, ein bis vier Gesprächseigenschaften und eigene Freitexthinweise festlegen. Die Eigenschaften sind analytisch, direkt, ermutigend, empathisch, neugierig, kreativ, strukturiert und kritisch. Die Konfiguration wird dem C-Systemprompt zur Laufzeit hinzugefügt. Es gibt keine Auswahl zwischen fertigen Berater-Vorlagen. Sofern nicht anders gewünscht, sollen auch die Antworten in C kurz, präzise und proaktiv sein.

**Neuester Stand:** C sucht immer ausgewogen. Die Auswahl zwischen „Ausgewogen suchen“, „Fachwissen vertiefen“, „Lernen mit Unterstützung“ und „Eigene Ideen umsetzen“ wurde entfernt; der Server erzwingt den ausgewogenen Fokus. Name, Eigenschaften und Freitext dürfen die Bewertungsgewichte nicht verändern. Fachliche Wünsche aus Profil und Gespräch werden weiterhin berücksichtigt.

Die tatsächlich festgelegten Gewichte sind:

| Bewertungsdimension | A | B | C |
|---|---:|---:|---:|
| Fachliche Passung | 60 % | 60 % | 60 % |
| Profilpräferenzen | 15 % | 15 % | 15 % |
| Fachliche Tiefe | 7 % | 3 % | 7 % |
| Lernen/Entwicklung | 6 % | 17 % | 6 % |
| Gestaltung/Innovation | 6 % | 3 % | 6 % |
| Klarheit der Aufgaben | 6 % | 2 % | 6 % |

Damit unterscheidet sich C von B weiterhin auch in der Ranggewichtung. C–B ist aktuell kein isolierter Test der Selbstgestaltung. Außerdem werden die Teilbewertungen vom LLM unter dem jeweiligen Prompt erzeugt: Selbst gleiche feste Gewichte würden noch keine identischen Scores garantieren. Weitere technische Unterschiede sind getrennte Gesprächsinstruktionen, Antwortlängensteuerung und die Wiederverwendung von Teilbewertungen in B/C. Bitte prüfe, welche Unterschiede für meine konkrete Forschungsfrage kontrolliert werden müssen.

Es gibt keinen gemeinsamen zusätzlichen Beratungs-Systemprompt für A/B/C; B und C haben jeweils eigene administrativ bearbeitbare Basisprompts. Die fachliche Aufgabe ähnelt sich bewusst. Promptrevisionen und Prüfsummen werden dokumentiert, der Basisprompt wird für reguläre Teilnahmen bei Zuteilung eingefroren. Persönlichkeitskonfigurationen werden mit einem projektspezifischen versionierten MLDS-Schema dargestellt. Das schafft Nachvollziehbarkeit, ist allein aber kein nachgewiesener Forschungsbeitrag.

### Geplanter Ablauf und Datenerhebung

Der Studienplan ist ein randomisierter Zwischenpersonenvergleich. Neue Teilnahme-IDs werden serverseitig mit jeweils 1/3 Wahrscheinlichkeit A/B/C zugeordnet; die Zuteilung bleibt erhalten. Das garantiert keine exakt gleich großen Gruppen und verhindert nicht sämtliche Mehrfachteilnahmen in verschiedenen Browsern.

Nach Einwilligung beantworten die Teilnehmenden Fragen zur bisherigen Nutzung von Jobportalen und KI-Chats. Sie erstellen ein realistisches Suchprofil, betrachten Stellen und Begründungen und stellen mindestens eine eigene inhaltliche Chatfrage. C durchläuft zusätzlich die Selbstgestaltung. Demografie und Suchvorhaben können während der Suchwartezeit beantwortet werden. Bewertungen folgen erst nach der Nutzung. Bereits beantwortete Angaben werden später übersprungen.

In der Umfrage sind höchstens drei erfolgreich beantwortete eigene Chatnachrichten pro Teilnahme erlaubt. Das Weitergehen setzt mindestens eine solche Antwort voraus. Automatische Begrüßungen und fehlgeschlagene Anfragen zählen nicht. Die unabhängigen Demonstrationsseiten `/test/a`, `/test/b` und `/test/c` haben kein Nachrichtenlimit und erzeugen keine Studienantworten. Bitte beurteile ausdrücklich, ob ein bis drei Nachrichten ausreichen, um den postulierten Mehrwert der proaktiven Beratung zu untersuchen.

Antworten werden fortlaufend gespeichert. Die Verwaltung erlaubt Ansicht, Diagramme und CSV-Export einschließlich Codebuch für Numiqo, wahlweise unter Einbezug unvollständiger Teilnahmen. Berichtigungen einzelner Antworten haben einen Änderungsverlauf. Teilnahme-ID, Einwilligung und Löschanfrage sind vorgesehen. Eigene Such- und Chattexte werden anwendungsseitig für neue Sitzungen nur vorübergehend im Arbeitsspeicher gehalten; gespeichert werden Umfrageantworten und dokumentierte Metadaten. Darunter sind Versionen, Konfigurationsnutzung, erfolgreiche/fehlgeschlagene Operationen und Serverlaufzeiten. Das Umfrage-Freitextfeld zum Suchvorhaben ist selbst eine gespeicherte Antwort. Die vorübergehende Speicherung in DIANA sagt nichts über die Datenhaltung des API-Anbieters aus.

Die Metadaten über eigene Gestaltung beweisen nicht automatisch eine inhaltliche Änderung: Ein Teilnehmer kann C verwenden, ohne die vorgeschlagene Ausgangskonfiguration zu verändern. Deshalb gibt es eine zusätzliche Selbstauskunft. Solche Personen verbleiben für den Hauptvergleich in ihrer randomisiert zugewiesenen Gruppe C.

### Bisheriger Analyseplan

Der lokale Protokollentwurf nennt C–B als primären und B–A als sekundären Vergleich. Primärer Endpunkt ist das Einzelitem „Wie hilfreich war das System für die Durchführung deiner Suche?“ auf einer Skala von 1 bis 10. Geplant sind Mittelwertdifferenz, Welch-t-Test, 95%-Konfidenzintervall und Hedges g; für weitere Inferenztests eine Holm-Korrektur. Die quasi-metrische Behandlung des ordinalen Einzelitems ist eine Annahme. Die selbst formulierten Fragen sind keine bereits validierte Skala.

Das Arbeitsziel sind 100 auswertbare Primärantworten je Gruppe, also rund 300 insgesamt. Bei angenommenen 25 % ohne auswertbaren Endpunkt wären ungefähr 400 Starts erforderlich. Die Planung verwendet d=0,40, 80 % Power und einen zweiseitigen Zweigruppenvergleich bei alpha=0,05; sie garantiert keine ausreichende Power für alle Vergleiche oder kleinere Effekte.

Alle gültigen Primärantworten sollen nach Zuteilung ausgewertet werden, auch aus später abgebrochenen Umfragen. Fehlende Werte sind keine Nullwerte. Das ist keine vollständige Intention-to-treat-Analyse mit Imputation. Stoppregel, Ausfälle und endgültiger Auswertungsplan sind vor der Haupterhebung festzuschreiben. Das vorhandene Protokoll ist ein Entwurf, keine externe Präregistrierung. Bitte prüfe, ob das primäre Maß zu einem Informatik-/CHIIR-Beitrag ausreicht und welche objektiven Maße ergänzend nötig wären.

### Tatsächlich vorhandene technische Vorarbeiten

Im Projekt liegt ein historischer technischer Pilot vom 17. September 2026: zwei fiktive Nutzerinnen, jede in A/B/C, jeweils initiale Suche plus drei Chatnachrichten. Das sind sechs Sitzungen und 24 Ranglisten-Snapshots, nicht 24 unabhängige Nutzer. Es wurden 47 Persona-Stellen-Paare anhand des vollständigen konstanten Bedarfs und der Originalanzeigen durch Codex beurteilt. Verwendet wurden nDCG@10, nDCG@5, Precision@5 und MRR@10. Die nDCG-Referenz kommt aus den gepoolten Treffern, nicht aus einer vollständigen Bewertung aller 8.537 Anzeigen.

Die finalen mittleren nDCG@10-Werte dieses Piloten waren A=0,841, B=0,874 und C=0,808. Es gab keinen über alle Kennzahlen einheitlichen Sieger; MRR zeigte einen Deckeneffekt. Die ersten beiden Nachrichten führten nur zur Neubewertung des bestehenden Pools, die dritte zu einer Antwort ohne Rankingänderung. Ein Durchlauf pro Person/Variante und fehlende menschlich validierte bzw. unabhängige Referenzurteile erlauben keinen belastbaren allgemeinen Wirksamkeitsnachweis.

Dieser Pilot evaluiert eine ältere Version: A war damals eine feste Standardberatung und C verwendete Lernpotenzial-Gewichtung. Seine Resultate sind kein Wirksamkeitsnachweis für das heutige A ohne Systemprompt oder C mit ausgewogener Gewichtung. Frühere größere Testserien wurden separat archiviert; sie sind nicht ungeprüft mit diesem Piloten zusammenzurechnen. Technische Funktionsprüfungen, synthetische Tests und echte Nutzerstudie sind ausdrücklich verschiedene Evidenzarten.

### Bekannte offene Punkte und noch nicht umgesetzte Idee

Bei Erstellung dieses Briefings wies das Backend der neuen Studie `diana-abc-v4` den Fragebogen `diana-v11` zu, während das Frontend nur bis V10 kannte. Bei der anschließenden Deployment-Vorbereitung am 21. September wurde diese Versionsabweichung behoben: V11 wird einschließlich Vorbereitung und sachlicher Wartezeitfragen unterstützt, ältere Fragebögen bleiben verfügbar. Die Frontend-Regressionstests bestehen. Das ersetzt noch keinen kognitiven Pretest mit Teilnehmenden.

Zwei Fragen zu Persönlichkeit und Rangfolge bzw. Bewertungsschwerpunkten stammen noch aus dem vorherigen Konzept. Da C nun nur Ausdruck und Erklärungen selbst gestaltet, können diese Fragen eine nicht vorhandene frei gestaltbare Rankingwirkung nahelegen. Bitte prüfe sie ausdrücklich, statt sie als schon passend zu behandeln.

Eine bisher nicht implementierte Idee wäre, das LLM eine ideale Stellenbeschreibung aus dem Bedarf erzeugen zu lassen und diese bei Bedarf mit einem Cross-Encoder gegen die Top-20-Kandidaten abzugleichen. Bitte beurteile, ob das eine theoretisch begründete Verbesserung oder nur zusätzliche Komplexität wäre, welche Ablation nötig wäre und welche neuen Störfaktoren entstehen, wenn nur B/C diese Technik erhalten. Ich möchte keine zusätzliche Technik allein für den Anschein größerer Neuheit.

### Mein Auftrag an dich

1. Formuliere die stärkste belastbare Forschungsfrage für den jetzigen Stand und grenze ab, welche Aussagen diese Studie nicht tragen kann.
2. Beurteile die Eignung für CHIIR als Demo, Short Paper oder Full Paper anhand der aktuellen offiziellen Ausschreibung und einschlägiger Originalarbeiten.
3. Prüfe, ob A eine angemessene Baseline ist und ob B/C gleiche Gewichte sowie ansonsten gleiche technische Bedingungen benötigen, um Selbstgestaltung zu isolieren.
4. Unterscheide eine Evaluation des Gesamtsystems von einer Evaluation des Personalisierungsbausteins. Schlage nur notwendige Ergänzungen vor.
5. Prüfe den folgenden Fragenkatalog auf Passung zur Forschungsfrage, Suggestion, Redundanz, fehlende Konstrukte und Aufwand. Gib bei nötigen Änderungen konkrete Ersatzformulierungen an; verlängere ihn nicht pauschal.
6. Schlage objektive Maße für Such-, Auswahl- und Gesprächsqualität vor. Erkläre, welche davon mit vorhandenen Daten messbar sind und welche neue Erhebung oder Referenzurteile erfordern. Reine Rankingänderung ist kein Qualitätsbeleg.
7. Ordne Vorstudie und historischen synthetischen Pilot korrekt ein. Vermische sie nicht mit einer noch ausstehenden Evaluation der heutigen Version.
8. Priorisiere dein Fazit in „vor der Haupterhebung erforderlich“, „für einen stärkeren Beitrag hilfreich“ und „vorerst weglassen“. Begründe Aufwand und Erkenntnisgewinn jeder Empfehlung.

Der vollständige vorgesehene Fragenkatalog folgt. Beziehe ihn in deine Bewertung ein.

## Fragenkatalog V11 – unveränderter Wortlaut

Alle Skalen reichen von 1 bis 10. Die nachstehenden Endpunkte gelten pro Frage. „Nicht genutzt“, „Kann ich nicht beurteilen“ und „Keine Angabe“ sind keine numerischen Skalenwerte. A erhält 15, B 20 und C 21 Fragen einschließlich der zwei optionalen Freitextfelder. Einwilligung und automatisch gespeicherte Gruppenzuteilung sind darin nicht mitgezählt. Die Reihenfolge der Vorerfahrungsfragen wird im vorgesehenen Ablauf vor die Systemnutzung gezogen; demografische Angaben und Suchvorhaben können während der Wartezeit beantwortet werden.

### Ein paar Angaben zu dir

**1. Wie alt bist du?** (`age_group`)

Antworten: Unter 18 Jahren / 18–20 Jahre / 21–24 Jahre / 25–29 Jahre / 30–39 Jahre / 40 Jahre oder älter / Keine Angabe.

**2. Welchem Geschlecht ordnest du dich zu?** (`gender`)

Antworten: Weiblich / Männlich / Divers / Keine Angabe.

**3. Was beschreibt deine aktuelle Situation am besten?** (`education`)

Antworten: Bachelorstudium / Masterstudium / Anderes Studium / Promotion / Schule oder Ausbildung / Aktuell nicht im Studium oder in Ausbildung / Keine Angabe.

**4. Was ist deine Studien- oder Fachrichtung?** (`study_field`)

Freitext (optional); bis zu 160 Zeichen.
Hinweis: Du kannst dieses Feld auch leer lassen.

**5. Wie häufig hast du in den letzten sechs Monaten Online-Jobportale genutzt?** (`job_portal_experience`)

Antworten: Nie / Seltener als einmal pro Woche / Mindestens wöchentlich, aber nicht täglich / Täglich / Keine Angabe.

**6. Wie häufig hast du in den letzten sechs Monaten KI-Chatbots genutzt?** (`ai_chat_experience`)

Antworten: Nie / Seltener als einmal pro Woche / Mindestens wöchentlich, aber nicht täglich / Täglich / Keine Angabe.


### Dein Suchvorhaben

**7. Wonach hast du mit DIANA gesucht?** (`search_goal`)

Freitext (erforderlich); 3–1000 Zeichen.
Hinweis: Nenne den Tätigkeitsbereich, die gewünschte Stellenart und die Suchwünsche, die für dich wichtig waren. Auch wenn du das Beispielprofil genutzt hast, beschreibe kurz das Suchvorhaben.


### Deine Erfahrung mit der Suche

**8. Wie aufwendig war es, deine Suche durchzuführen?** (`search_effort`)

Skala: 1 = Überhaupt nicht aufwendig; 10 = Sehr aufwendig.
Zusätzlich: Kann ich nicht beurteilen.

**9. Wie hilfreich war das System für die Durchführung deiner Suche?** (`system_usefulness`)

Skala: 1 = Gar nicht hilfreich; 10 = Sehr hilfreich.
Zusätzlich: Kann ich nicht beurteilen.

**10. Wie wahrscheinlich ist es, dass du dieses Suchsystem bei einer zukünftigen Jobsuche nutzen würdest?** (`future_use`)

Skala: 1 = Sehr unwahrscheinlich; 10 = Sehr wahrscheinlich.
Zusätzlich: Kann ich noch nicht einschätzen.


### Suchen im Gespräch

**11. Wie hilfreich war der Chat, um deine Suchwünsche zu konkretisieren?** (`chat_helpfulness`)

Skala: 1 = Gar nicht hilfreich; 10 = Sehr hilfreich.
Zusätzlich: Kann ich nicht beurteilen.

**12. Hast du deine Suchwünsche im Chat ergänzt oder verändert?** (`search_refinement`)

Antworten: Ja / Nein.


### Score und Begründungen

**13. Wie nützlich war der Score, um dir einen Überblick über die Stellen zu verschaffen?** (`score_usefulness`)

Skala: 1 = Gar nicht nützlich; 10 = Sehr nützlich.
Zusätzlich: Nicht genutzt / Kann ich nicht beurteilen.

**14. Wie nützlich waren die Stichpunkte „Warum das passen könnte“, um die Empfehlung nachzuvollziehen?** (`match_reasons_usefulness`)

Skala: 1 = Gar nicht nützlich; 10 = Sehr nützlich.
Zusätzlich: Nicht genutzt / Kann ich nicht beurteilen.


### Deine KI-Suchpersönlichkeit

**15. Hast du die vorgeschlagene Ausgangskonfiguration deiner KI-Suchpersönlichkeit tatsächlich verändert?** (`personality_customized`)

Nur Gruppe C.

Antworten: Ja / Nein.

**16. Wie klar war dir, wie deine KI-Suchpersönlichkeit die Reihenfolge der Stellen beeinflusst?** (`personality_clarity_search`)

Nur Gruppe B und C.

Skala: 1 = Überhaupt nicht klar; 10 = Völlig klar.
Zusätzlich: Kann ich nicht beurteilen.

**17. Wie klar war dir, wie deine KI-Suchpersönlichkeit die Antworten im Chat beeinflusst?** (`personality_clarity_chat`)

Nur Gruppe B und C.

Skala: 1 = Überhaupt nicht klar; 10 = Völlig klar.
Zusätzlich: Kann ich nicht beurteilen.

**18. Wie deutlich hast du die Eigenschaften deiner KI-Suchpersönlichkeit in den Antworten des Chatbots wiedererkannt?** (`personality_consistency`)

Nur Gruppe B und C.

Skala: 1 = Überhaupt nicht; 10 = Sehr deutlich.
Zusätzlich: Kann ich nicht beurteilen.

**19. Wie nützlich war der Gesprächsstil deiner KI-Suchpersönlichkeit für deine Suche?** (`personalized_chat_usefulness`)

Nur Gruppe B und C.

Skala: 1 = Gar nicht nützlich; 10 = Sehr nützlich.
Zusätzlich: Nicht genutzt / Kann ich nicht beurteilen.

**20. Wie hilfreich waren die Bewertungsschwerpunkte deiner KI-Suchpersönlichkeit für deine Suche?** (`personalized_search_usefulness`)

Nur Gruppe B und C.

Skala: 1 = Gar nicht hilfreich; 10 = Sehr hilfreich.
Zusätzlich: Nicht genutzt / Kann ich nicht beurteilen.


### Dein Feedback

**21. Was würdest du an diesem Suchsystem verbessern?** (`feedback`)

Freitext (optional); bis zu 4000 Zeichen.
Hinweis: Bitte nenne keine Namen oder anderen personenbezogenen Angaben.


## Grundlage dieses Briefings

Lokale Quellen: `app.py`, `llm_service.py`, `advisor.py`, `study_assignment.py`, `system_prompt_store.py`, `study_release.py`, `frontend/AdvisorPicker.jsx`, `frontend/survey.js`, `survey_definition_v11.json`, `STUDY-PROTOCOL.md` und `research/persona-study-2026-09-17/RESULTS.md`.

Bei der Aufwandfrage bedeutet ein höherer Wert mehr Aufwand; bei Nutzenfragen mehr Nutzen. Die Fragen zu Rangfolge und Bewertungsschwerpunkten wurden hier bewusst nicht umformuliert: Das Briefing dokumentiert den vorhandenen Wortlaut und kennzeichnet den Überarbeitungsbedarf.
