# Offline-Auswertung der DIANA-Konferenzstudie

Die Skripte arbeiten ausschließlich mit lokalen Dateien. Sie greifen weder auf
den Server noch auf OpenAI zu. Forschungsabhängigkeiten bleiben von der Anwendung
getrennt. Vom Projektverzeichnis aus:

```bash
python3.12 -m venv research/.venv
research/.venv/bin/python -m pip install -r research/requirements.txt
```

## Primären Vergleich berechnen

In der Verwaltung den Numiqo-CSV-Export **einschließlich unvollständiger Teilnahmen**
herunterladen. Deutsche oder technische Spaltennamen werden erkannt. Beispiel:

```bash
research/.venv/bin/python research/analyze_primary.py /pfad/zur/diana_numiqo.csv --output /pfad/zum/ergebnis.json
```

Ohne `--output` erscheint JSON im Terminal. Bestehende Ausgabedateien werden nie
überschrieben. Die Analyse berücksichtigt ausschließlich `diana-abc-v3` /
`diana-v10` und alle gültigen Primärantworten von 1–10, auch aus Teilantworten.
Die zufällige Zuteilung entscheidet: C bleibt C, auch bei unveränderter Vorlage.

Die frühere faire Kohorte V9 wird nur ausdrücklich und getrennt ausgewertet:

```bash
research/.venv/bin/python research/analyze_primary.py /pfad/zur/diana_numiqo.csv --cohort v9 --output /pfad/zum/ergebnis_v9.json
```

`--cohort v10` ist die Voreinstellung für `diana-abc-v3` / `diana-v10`.
`--cohort v9` wählt ausschließlich `diana-abc-v2` / `diana-v9` und deren
`v9_system_nutzen`- bzw. `v9_system_usefulness`-Spalte. Ein gemeinsamer Export darf
beide enthalten; die Analyse mischt sie niemals. Ohne Daten der ausdrücklich
gewählten Kohorte wird kein Ergebnis geschrieben.

Ausgegeben werden Gruppendeskriptivwerte A/B/C, fehlende und ungültige Primärwerte
sowie **C minus B** für `system_usefulness`: Welch-Test, 95%-Konfidenzintervall und
Hedges g. IDs und Freitexte erscheinen nicht im Ergebnis. Doppelte Teilnahme-IDs
innerhalb der Zielkohorte führen zum Abbruch; bei zu kleinen Gruppen oder beidseitig
fehlender Streuung wird keine künstliche Inferenz ausgegeben. Nicht exportierte,
gelöschte oder widerrufene Daten kann das Skript nicht rekonstruieren.

Die quasi-metrische Behandlung des 1–10-Einzelitems und die zusätzliche
Varianzannahme des standardisierten Effekts sind im Skript dokumentiert.
Analyseplan und Einschränkungen: [STUDY-PROTOCOL.md](../STUDY-PROTOCOL.md).

## Stichprobengröße planen

```bash
research/.venv/bin/python research/plan_sample_size.py
research/.venv/bin/python research/plan_sample_size.py --output /pfad/zum/stichprobenplan.json
```

Die nichtzentrale t-Rechnung verwendet zweiseitig α=0,05, Power 80% und gleiche
Gruppengrößen. Für angenommene Effekte d=0,30/0,40/0,50 ergeben sich
176/100/64 gültige Primärantworten je Gruppe. Die 25%-Ausfallreserve wird sowohl
für die Gesamtzahl als auch separat mit ganzzahliger Rundung je Gruppe ausgewiesen.
Das Skript legt keine Rekrutierung oder Stoppregel im System fest.

## Synthetische Prüfungen

```bash
research/.venv/bin/python -m unittest discover -s research -p 'test_analysis.py' -v
```

Die Tests verwenden ausschließlich künstliche Daten. Ohne Forschungsabhängigkeiten
werden sie übersprungen; die normalen Backendtests benötigen kein SciPy.
Forschungsdaten und Ergebnisse außerhalb des Git-Repositories aufbewahren.

## Technischer Ranking-Check

Der [gesonderte Plan](RANKING-EVALUATION-PLAN.md) beschreibt einen späteren Test
mit konstanten Profilen/Stellen, gezielt geänderten Prioritäten, Wiederholungen
und unabhängiger Inhaltsprüfung. Er wurde nicht ausgeführt oder terminiert.
