# Konferenzeinordnung DIANA · 14. September 2026

DIANA ist aus meiner Einschätzung ein geeigneter Ausgangspunkt für einen wissenschaftlichen Demo- oder Posterbeitrag. Für ein Full Paper sind ein klar abgegrenzter neuer Beitrag, eine nachvollziehbare Evaluation und die Einordnung gegenüber verwandten Systemen entscheidend. Ein funktionsfähiges System oder eine große Teilnehmerzahl allein garantiert keine Annahme.

## Was der derzeitige Vergleich belegen kann

Die aktuelle Implementierung vergleicht zwei Funktionspakete: A hat einen allgemeinen Assistenten, zufällige Anzeigereihenfolge und einfache Stellenkarten. B ergänzt eine konfigurierbare Beratung, persönliche Rangfolge, sichtbare Scores und Begründungen. Beide verwenden intern dieselbe hybride Vorauswahl und LLM-Bewertung; A zeigt die bewerteten Stellen anschließend zufällig an. Auch die Zahl zunächst sichtbarer Karten kann wegen der Score-Schwelle in B abweichen.

Eine passende Forschungsfrage lautet daher:

> Welchen wahrgenommenen Mehrwert bietet ein konfigurierbares KI-Beratungspaket gegenüber einer allgemeinen KI-Jobsuche hinsichtlich Nutzbarkeit, Suchkontrolle und Unterstützung im Gespräch?

Der Effekt der Persönlichkeit allein ist damit nicht identifizierbar. Um diesen zu untersuchen, müssten Rangfolge, Scores, Erklärungen, Aufgaben und übrige Bedingungen gleich sein. Für den kausalen Mehrwert eines Chatbots gegenüber Filter-/Stichwortsuche wäre eine gleichzeitige vergleichbare Filterbedingung nötig. Die frühere separate Umfrage ist hilfreicher Kontext, aber kein gleichwertiger randomisierter Kontrollarm.

Die bewusst zufällige Reihenfolge in A ist als Baseline begründungsbedürftig: Ein Vorteil von B kann bereits aus der Sortierung entstehen. Eine übliche relevanzsortierte Vergleichssuche wäre überzeugender. Diese Bewertung ändert das bestehende Experiment nicht automatisch.

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
