# Konferenzeinordnung DIANA · 14. September 2026

DIANA ist aus meiner Einschätzung ein geeigneter Ausgangspunkt für einen wissenschaftlichen Demo- oder Posterbeitrag. Für ein Full Paper sind ein klar abgegrenzter neuer Beitrag, eine nachvollziehbare Evaluation und die Einordnung gegenüber verwandten Systemen entscheidend. Ein funktionsfähiges System oder eine große Teilnehmerzahl allein garantiert keine Annahme.

## Aktueller Vergleich A/B/C

Seit der neuen Experimentversion `diana-abc-v1` werden neue Teilnahmen zufällig mit gleicher Wahrscheinlichkeit einer von drei Bedingungen zugeteilt:

| Gruppe | Verfügbare Beratung | Ergebnisdarstellung |
| --- | --- | --- |
| A | Allgemeiner KI-Assistent ohne wählbare Persönlichkeit | Zufällige Anordnung der bis zu 20 Retrieval-Kandidaten, keine angezeigten Scores oder automatischen Begründungsboxen |
| B | Auswahl zwischen unveränderten Vorlagen Top-Berufsberater und Fachexperte | Persönliche Bewertung und Rangfolge, Scores und Begründungen; zunächst Ergebnisse ab 70 Punkten |
| C | Dieselben Vorlagen plus selbst gestaltbare Persönlichkeit | Dieselbe Bewertungs- und Darstellungslogik wie B; Eigenschaften können die Bewertung beeinflussen |

Modell, Datenquelle, Retrieval, Score-Schwelle und Rankingverfahren sind zwischen B und C gleich. Die durch eigene Eigenschaften beabsichtigte Änderung der Gewichtung ist Teil der Intervention. Beide starten mit dem Top-Berufsberater. B kann Vorlagen wechseln; C kann zusätzlich selbst gestalten. Die freie Gestaltung ist ein Angebot, keine Pflicht.

Für den Vergleich B/C passt die Forschungsfrage:

> Welchen zusätzlichen wahrgenommenen Nutzen bietet die Möglichkeit, eine KI-Suchpersönlichkeit selbst zu gestalten, gegenüber der Auswahl aus festen Beratungsvorlagen hinsichtlich Suchkontrolle, Unterstützung im Gespräch und Nutzbarkeit?

Für den primären Vergleich alle Teilnehmenden gemäß ihrer zufälligen Zuteilung auswerten, auch wenn jemand in C keine Anpassungen vornimmt. Eine Auswertung nur der Personen, die tatsächlich personalisieren, wäre ein selbst selektierter Vergleich. Die erste/letzte verwendete Auswahl und Wechsel ergänzen explorative Nutzungsanalysen. Sie ersetzen nicht die randomisierte Zuteilung.

A/B und A/C vergleichen weiterhin Gesamtpakete. Der Unterschied kann auch durch Sortierung, sichtbare Scores, Begründungen und die Zahl anfangs sichtbarer Stellen entstehen. Die bewusst zufällige Reihenfolge in A ist als Baseline begründungsbedürftig; eine übliche relevanzsortierte Basissuche wäre wissenschaftlich überzeugender. A wurde durch diese Erweiterung nicht verändert. Für den kausalen Mehrwert eines Chatbots gegenüber Filter-/Stichwortsuche wäre weiterhin eine zeitgleiche vergleichbare Filterbedingung nötig; die frühere separate Umfrage ist Kontext, kein gleichwertiger Kontrollarm.

## Historische Daten und ergänzende Messwerte

Die vorherige Experimentversion `diana-ab-v2` hatte nur A/B; das damalige B bot bereits freie Gestaltung. Bestehende Teilnahmen behalten ihre Zuordnung und diesen Funktionsumfang. Historisches B darf deshalb nicht als heutige Vorlagen-Gruppe B ausgewertet werden. Fragebogen V8 und `diana-abc-v1` kennzeichnen die neue Erhebung; V7 und frühere Versionen bleiben getrennt erhalten.

Erfasst werden Quelle, Vorlagentyp, erste und letzte tatsächlich angewendete Auswahl, Auswahlwechsel und Zeitpunkte. Historische fehlende Werte bleiben unbekannt; abgeschlossene Teilnahmen behalten ihren Abschlussstand. Als zusätzliche, noch nicht neu implementierte Messwerte wären Suchdauer, fehlgeschlagene Suchen, erfolgreiche Chatnachrichten und letzter erreichter Schritt sinnvoll. Dafür reichen Zählwerte und Zeitangaben; Gesprächsinhalte sind nicht erforderlich.

## Vor einer Einreichung

- Einen primären Endpunkt und Hypothesen, Ausschlussregeln, Stichprobenplanung und Auswertungsplan vor der Haupterhebung festlegen. Pilot- und nachträglich veränderte Systemstände getrennt behandeln.
- Effektgrößen und Konfidenzintervalle berichten; mehrere Bewertungen und fehlende Antworten transparent behandeln. Die selbst formulierten Fragen nicht als bereits validierte Skala bezeichnen.
- Baseline und Unterschiede offen beschreiben. Systemqualität nicht absichtlich verringern und anschließend einen isolierten Personalisierungseffekt behaupten.
- Antwortkorrekturen auf nachvollziehbare Berichtigungen beschränken und anhand des Änderungsverlaufs dokumentieren. Keine Antworten für günstigere Ergebnisse umschreiben.
- Modell-Snapshot, Prompts, Vorlagen, Fragebogenversion, Datenstand und Quellcode archivieren. Ohne archivierte individuelle Suchprofile/Chats ist keine vollständige Wiederholung einzelner Sitzungen möglich. Die Datenschutzentscheidung bleibt davon unberührt.
- Den wissenschaftlichen Neuheitsbeitrag gegenüber verwandten Conversational-Recommender- und Job-Matching-Systemen herausarbeiten. Die MLDS-Ablage verbessert die technische Nachvollziehbarkeit, liefert für sich allein noch keinen Wirksamkeitsnachweis.

## Geeignete Ziele

| Konferenz | Einschätzung und aktuelle Frist |
| --- | --- |
| [ACM UMAP 2027](https://um.org/umap2027/) | Beste thematische Passung für Personalisierung und Benutzeradaptation. Chicago, 9.–12. Juni 2027. Abstract: 22. Januar; Full/Short Paper: 29. Januar 2027. LBR/Demo: 22. März 2027. Für einen empirischen Beitrag meine erste Empfehlung. |
| [ACM IUI 2027 · Posters & Demos](https://iui.acm.org/2027/call-for-posters-demos/) | Gute kurzfristige Option für das interaktive System. Frist 10. November 2026; bis zu vier Seiten ohne Literatur. Demo zusätzlich mit Video bis fünf Minuten. Helsinki, 8.–11. Februar 2027. |
| [Mensch und Computer 2027](https://fb-mci.gi.de/veranstaltung/mensch-und-computer-2027) | Gute Alternative für eine Untersuchung von Nutzbarkeit und Suchinteraktion. Oldenburg, 30. August–2. September 2027. Einreichungsfristen 2027 sind hier noch nicht verifiziert. |

Die Empfehlungen sind eine fachliche Einschätzung, keine Annahmezusage. Fristen vor der tatsächlichen Einreichung erneut prüfen.

## MLDS-Bezug

Die [verlinkte Veröffentlichung von Fischer et al.](https://doi.org/10.15439/2025F5613) beschreibt domänenspezifische Meta-Language-defined Structures und deren Spezifikation. DIANA verwendet darauf aufbauend ein eigenes versioniertes Persona-Schema und validierte `.mlds`-Dokumente; es gibt in der Quelle kein vorgefertigtes universelles Persona-Format. Die aktuelle Integration serialisiert Konfigurationen deterministisch. Eine eigene Evaluation LLM-generierter MLDS-Strukturen wurde damit noch nicht durchgeführt. Technische Einzelheiten und Quellen stehen in [MLDS.md](MLDS.md).
