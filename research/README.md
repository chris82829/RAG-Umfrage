# Forschungsauswertung von DIANA

## Aktueller Stand V12

Die folgenden Pilotberichte bleiben historische Entwicklungsdaten und wurden
nicht unter `diana-abc-v5` / `diana-v12` erhoben. Die neue
[menschliche Relevanzprüfung](human_relevance/README.md) besteht derzeit aus
Export-/Auswertungswerkzeugen ohne aktuelle Systemausgaben und ohne menschliche
Ratergebnisse. Ihre mitgelieferten Demonstrationswerte sind synthetische Testdaten.

**`analyze_primary.py` ist nicht für V12 geeignet:** Das Skript unterstützt nur
V9/V10/V11 und deren 1–10-Einzelitem `system_usefulness`; sein Standard bleibt die
historische V11-Kohorte. Nicht durch Umbenennen von V12-Spalten umgehen.
Für den vorläufigen V12-Mittelwert aus drei vollständigen 1–5-Items ist ein separat
zu prüfendes Auswerteskript erforderlich. [Protokollentwurf](../STUDY-PROTOCOL.md)
und [V12-Änderungen](../V12-CHANGES.md) beschreiben den neuen Stand.

## Historische Forschungsläufe

Der vollständige Lauf und die erste Übersicht für **0, 1, 2 und 3 Nachrichten**
stehen im [Ergebnisbericht](persona-study-2026-09-17/RESULTS.md), mit
[Einzelwerten](persona-study-2026-09-17/run/analysis/report.md) und
[Grafik](persona-study-2026-09-17/run/analysis/ranking-verlauf.png).
Alle Zeitpunkte werden gegen das vollständige, unveränderte Persona-Wissen bewertet.

Der neue [deskriptive Zwei-Personen-Pilot](persona-study-2026-09-17/PROTOCOL.md)
führt **dieselben zwei fiktiven Nutzerinnen Mara Seidel und Nora Peters in
A, B und C** durch das System. Je Person und Variante entstehen eine initiale
Suche und drei adaptive Nachrichten: **sechs vollständig ausgeführte Sitzungen, 24
Ranglistensnapshots, zwei Personen**.

Die kanonischen Eingaben stehen in
`persona-study-2026-09-17/selected-personas.json`. A nutzt die feste
Standardberatung. B nutzt für beide Personen unverändert den Top-Berufsberater.
C verwendet den vorab entworfenen Einstiegscoach für Mara beziehungsweise
die Umstiegsberatung für Nora. Mara sucht in der Webentwicklung; Nora in
der nichttechnischen Personaladministration. Innerhalb jeder Person erhalten alle Varianten dasselbe
initiale Profil und dieselben drei Informationsetappen. Codex passt die
tatsächliche Formulierung an reale Antworten an und protokolliert sie;
zusätzliche Fakten sind nicht erlaubt.

Codex beurteilt je Person einen gemeinsamen Pool ihrer gefundenen Stellen selbst,
ohne zusätzliche Simulator- oder Bewertungs-API. nDCG@10, nDCG@5, Precision@5 und
RR@10 werden je Person/Variante/Zeitpunkt berechnet. MRR@10 mittelt die beiden
RR@10-Werte je Variante und Zeitpunkt; 24 Snapshots sind keine 24 unabhängigen
Teilnehmer. Fallzahlen und fehlende Ergebnisse werden offengelegt.
Die zunächst auf **3 USD** gesetzte Obergrenze wurde nach T1 ausdrücklich vom
Nutzer auf **4,50 USD insgesamt** angehoben. Originaldateien und Genehmigung
sind im Lauf unter `amendments/01-budget-authorization` erhalten. Alle 42
Systemaufrufe sind erfolgreich abgeschlossen; die konservativ nach Standardpreisen
berechneten Tokenkosten betragen **3,6641125 USD**. Weitere API-Aufrufe sind
nicht nötig. Die Ergebnisse sind deskriptive
Hinweise, kein Nachweis allgemeiner Überlegenheit einer Variante.

Zwölf Personen und größere Laufpläne wurden zunächst vorbereitet. Diese Umfänge
sowie zwischenzeitliche kleinere Entwürfe wurden vor bezahlten Aufrufen dieses
Piloten auf Nutzerwunsch ersetzt. Die Dateien unter
`persona-study-2026-09-17/personas/` bleiben als **Vorbereitung** erhalten; nur P01
und P06 werden tatsächlich in den drei Varianten ausgeführt. Die zwei finalen
Personendokumente, Systemverläufe, Einzelurteile und Metriken werden gemeinsam
unter `persona-study-2026-09-17/` gespeichert.

Alle bisherigen Forschungs-Evaluationen sowie die bisherigen automatisierten
Funktionstests wurden am 17.09.2026 auf ausdrücklichen Wunsch aus dem Projekt
entfernt. Die geprüfte Sicherung liegt außerhalb des Projekts in
`../DIANA-Archiv/alte-tests-2026-09-17.tar.gz` (bezogen auf das Projektverzeichnis).
Der unveränderte Entfernungsnachweis steht in
`persona-study-2026-09-17/old-tests-removed.json`. Historische Resultate werden
nicht mit dem neuen Lauf vermischt.

Die separaten Werkzeuge für echte Umfrageantworten bleiben erhalten:
`analyze_primary.py` berechnet den historischen V9–V11-Nutzerstudienvergleich,
`plan_sample_size.py` unterstützt die Stichprobenplanung. Abhängigkeiten stehen
in `requirements.txt`. Beide Skripte arbeiten lokal und führen keine KI-Aufrufe aus.
