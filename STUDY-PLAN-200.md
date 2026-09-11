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

# DIANA: Planung mit 200 auswertbaren Teilnahmen

Planungsstand: 10. September 2026. Der Stichprobenrahmen von **200 auswertbaren Teilnahmen**, ungefähr 100 in A und 100 in B, wurde vom Studienleiter vorgegeben. Die folgenden Festlegungen zur Zielgröße und Analyse sind ein **Vorschlag für die Abstimmung mit dem Betreuer**, keine bereits erfolgte Präregistrierung. Das Dokument wird nicht rückwirkend als vor der bisherigen Datenerhebung festgelegter Analyseplan dargestellt.

## Forschungsfrage und Hauptzielgröße

Untersucht wird der Mehrwert eines personalisierten Gesamtpakets gegenüber einer einfachen neutralen KI-Jobsuche. A bietet neutrale Beratung und Stellenkarten ohne sichtbare Scores oder automatische Begründungsboxen; B ergänzt die selbst gestaltbare KI-Suchpersönlichkeit, Scores und Begründungen. Beide berücksichtigen das Suchprofil. B verändert damit mehrere Bestandteile zugleich: Gesprächsstil, ergänzende Bewertungsgewichte, Einrichtung und Ergebnisdarstellung. Der Vergleich identifiziert den gemeinsamen Paketunterschied, nicht die isolierte Wirkung eines Bestandteils. Die frühere Befragung zur klassischen Stichwortsuche bleibt eine eigene historische Erhebung.

Diese Gestaltung ist eine methodische Ableitung für die neue Forschungsfrage: Dörings Kapitel [Untersuchungsdesign](https://link.springer.com/chapter/10.1007/978-3-662-64762-2_7) behandelt die Wahl des Designs nach Forschungsproblem, Aufwand und Aussagekraft. Die öffentlich zugängliche Kapitelbeschreibung ist keine Prüfung oder Freigabe dieses konkreten Systems. Die neutrale Beratung wird nicht absichtlich falsch, unzuverlässig oder fachlich schlechter gemacht.

Vorgeschlagene einzige Hauptzielgröße: `system_usefulness`, „Wie hilfreich war das System für die Durchführung deiner Suche?“, von 1 bis 10. Geplant wird ein zweiseitiger Vergleich des Gruppenmittelwerts B minus A, mit 95-%-Konfidenzintervall. Nullhypothese: kein Mittelwertunterschied. Die übrigen Bewertungen werden als sekundär beziehungsweise explorativ ausgewiesen; aus ihnen entsteht kein ungeprüfter Gesamtwert. Hypothesen, endgültiges Analyseverfahren, Ein-/Ausschlussregeln und Umgang mit fehlenden Antworten sind vor Beginn der Haupterhebung festzulegen.

## Was 200 Teilnahmen erkennen können

Sensitivitätsanalyse mit zwei unabhängigen Gruppen à 100, α = 0,05, zweiseitigem t-Test und gemeinsamer Populationsvarianz. Die Berechnung verwendet die nichtzentrale t-Verteilung mit 198 Freiheitsgraden. Normalverteilung und gleiche Varianz sind Planungsannahmen, keine Feststellung über die späteren 1–10-Antworten. Bei einem anderen Haupttest oder mehreren gleichrangigen Hauptzielgrößen ist die Planung zu prüfen.

| Tatsächlicher standardisierter Unterschied d | Power bei insgesamt 200 |
|---|---:|
| 0,20 | 29,1 % |
| 0,30 | 56,0 % |
| 0,40 | 80,4 % |
| 0,50 | 94,0 % |

- Für **80 % Power** beträgt der erkennbare Unterschied **d = 0,398**.
- Für **90 % Power** beträgt er **d = 0,461**.
- Falls die Populationsstandardabweichung beispielsweise 2 Skalenpunkte beträgt, entsprechen diese Unterschiede etwa **0,80 beziehungsweise 0,92 Punkten**. Diese Streuung ist nur ein Beispiel und wurde nicht aus Studiendaten geschätzt.

200 sind damit ein begründbarer, begrenzter Studienrahmen. Ein nicht signifikanter Befund würde kleine oder auch gewisse mittlere Vorteile nicht ausschließen. Power ist keine Wahrscheinlichkeit, dass eine Hypothese wahr ist, und keine Garantie für Validität oder Repräsentativität. Ein kürzerer Fragebogen kann Abbrüche verringern; die erforderliche Fallzahl für dieselbe Hauptzielgröße und dieselbe Wirkung sinkt dadurch nicht automatisch. Die Hauptfragen bleiben gleich. Fragen zu Scores, automatischen Begründungen und Persönlichkeit werden in v7 nur B gestellt, weil nur B diese Funktionen erhält.

## Rekrutierung, Stoppregel und fehlende Daten

- Ziel sind 200 gültige, voneinander unabhängige Teilnahmen mit verfügbarer Hauptantwort in der festgelegten Haupterhebung. **Nicht jede andere Frage muss dafür beantwortet sein.** „Kann ich nicht beurteilen“ ist keine numerische Hauptantwort und kein niedriger Wert. Der endgültige Umgang damit und mit übrigen fehlenden Antworten wird vorab festgelegt.
- Bei angenommenen 20 % Verlusten bis zu einer auswertbaren Hauptantwort werden **250 begonnene Teilnahmen** benötigt: 200 / 0,8. Das ist eine Planungsreserve; höhere Ausfälle erfordern mehr Starts oder führen zu geringerer Präzision. Die Anzahl eingeladener Personen ist damit noch nicht festgelegt.
- Die bestehende unabhängige 50:50-Zuteilung garantiert keine exakt gleichen Gruppengrößen. Analysiert werden die tatsächlich zugeteilten Gruppen, ohne nachträgliche Umbesetzung. Bei 90/110 liegt die Sensitivität für 80 % Power beispielsweise bei d ≈ 0,400.
- Vorgeschlagene organisatorische Stoppregel: weitere Rekrutierung beenden, sobald das Ziel gültiger Hauptantworten erreicht ist; bereits gestartete, berechtigte Teilnahmen innerhalb einer vorher festgelegten Abschlussfrist einbeziehen und mögliche Überschreitungen transparent berichten. Ein Enddatum beziehungsweise eine maximale Rekrutierungsdauer ist vorab zu ergänzen. **Keine Fortsetzung oder vorzeitige Beendigung wegen beobachteter Signifikanz.**
- Zuweisungen, Starts, Hauptantworten, Abschlüsse, Abbrüche und Ausschlüsse nach Gruppe berichten. Auch Teilnehmer mit Hauptantwort und späterem Abbruch nicht allein wegen fehlendem Abschluss entfernen. Ein Vergleich nur verfügbarer Antworten kann bei gruppenabhängigen Ausfällen verzerrt sein und ist nicht automatisch eine vollständige Intention-to-treat-Analyse.
- Die technische Kennung verhindert keine Mehrfachteilnahme derselben Person in anderen Browsern oder nach Löschen des Speichers. Teilnahmebedingungen und vorab begründete Regeln für erkennbare Duplikate festlegen, ohne nachträglich anhand unerwünschter Bewertungen auszuschließen.

## Pilot, Versionsstand und Haupterhebung trennen

Vor dem Hauptstart einen kurzen Verständlichkeits- und Ablaufpretest durchführen. Anhand dieses Tests prüfen, ob B tatsächlich als individuell gestaltete Beratung wahrgenommen wird und A als sachlich hilfreiche Basisvariante funktioniert. Zusätzlich dokumentieren: die Einrichtungszeit von B, nur in B verfügbare Ergebnisbewertungen sowie Unterschiede in der sichtbaren Ergebniszahl (A zeigt alle bis zu 20 Karten, B blendet Werte unter 70 zunächst aus). Diese Unterschiede gehören zum untersuchten Gesamtpaket.

Bereits vorhandene Antworten, Testteilnahmen und die ältere Erhebung zählen **nicht automatisch zu den 200**. Vor der Auswertung schriftlich festlegen, welche Teilnahmezeiträume und `study_release_ids` den Pilot beziehungsweise die Haupterhebung bilden. Unterschiede in Modell-, Prompt-, Fragebogen- oder Funktionsversionen prüfen, getrennt dokumentieren und nicht ungeprüft zusammenlegen. Neue Promptänderungen benötigen einen nachvollziehbaren Versionsstand. Der Haupterhebungsplan sollte vor deren Start eingefroren oder registriert werden.

## Reproduzierbare Berechnung

Im Projektverzeichnis ausführen:

```sh
.venv/bin/python tools/power_plan.py
```

Das Skript liest keine Teilnehmerdaten und gibt Methode, SciPy-Version, Annahmen, Powerwerte und Sensitivitätsgrenzen als JSON aus. Es ergänzt keine Laufzeitabhängigkeiten und ändert keine Umfrage.

Methodische Referenz zur verwendeten Standardplanung: [statsmodels – TTestIndPower](https://www.statsmodels.org/stable/generated/statsmodels.stats.power.TTestIndPower.html). Die eigene Berechnung nutzt SciPys zentrale und nichtzentrale t-Verteilung, nicht eine Normalapproximation.
