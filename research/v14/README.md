# V14: Auswertung und separate Belegtreueprüfung

Diese Werkzeuge lesen ausschließlich ausdrücklich angegebene Dateien. Sie starten keine API-Anfragen, lesen keine Live-Datenbank und erzeugen keine menschlichen Urteile. Statistische Resultate sind **vorläufig/explorativ**, solange der Plan nicht vor der Haupterhebung eingefroren ist. Der technische Testdatensatz ist kein Studienergebnis.

## Fragebogen auswerten

In der Verwaltung den CSV-Export mit **technischen Spaltennamen**, **einschließlich unvollständiger Teilnahmen**, auswählen. Nur `diana-v14` und `study_wave=main` werden ausgewertet. Fehlende oder anders versionierte Werte werden nicht umgedeutet. Ein vollständiger Nutzenwert darf auch aus einem später abgebrochenen Fragebogen stammen.

```sh
python -m pip install -r research/requirements.txt
python -m research.v14.analyze /sicherer/pfad/antworten.csv --output /sicherer/pfad/v14-auswertung
```

Optional: `--operations /sicherer/pfad/operationen.csv` ergänzt Fehlerhäufigkeiten, jedoch keine automatischen Ausschlüsse. Die beiden Ausgabedateien sind JSON (vollständige Statistiken) und Markdown (lesbarer Kurzbericht). Die Eingabedatei erhält eine SHA-256-Prüfsumme; Antworten werden nicht verändert. Teilnahme-IDs werden im aggregierten Bericht nicht ausgegeben.

`analyze_rows(rows)` kann außerdem explizit von der Verwaltung aufgerufen werden. Jede Zeile enthält `survey_version`, `study_arm`, `study_wave` sowie `answers` als Objekt oder technische `v14_*`-Spalten. Die vier Mittelwerte werden erneut aus den Rohantworten gebildet, nicht aus vorberechneten Exportwerten. Wahlantworten werden als Originalcode (`yes`/`no`/`unsure`) oder technische numerische Codierung verarbeitet.

Ein tatsächlich nicht wiederhergestellter technischer Abbruch kann **vor Entblindung** in einer gesonderten Arbeitskopie mit `technical_exclusion=1` und `technical_exclusion_reason` dokumentiert werden. Ein leerer Grund ist ein Fehler. Erfolgreich wiederholte Operationen bleiben eingeschlossen; eine einzelne fehlgeschlagene Anfrage ist kein Ausschlussgrund. Jede identische Teilnahme-ID darf nur einmal vorkommen. Die unabhängigen Serverbestände müssen vor der Analyse ausdrücklich zusammengeführt und auf Dopplungen geprüft werden.

H1 ist der zweiseitige Welch-Test C−B beim dreiteiligen Nutzenwert. Die Holm-Familie umfasst genau drei sekundäre Tests (Kontrolle C−B, Transparenz C−B, Nutzen B−A). Mann–Whitney wird immer als Sensitivität ausgewiesen, nicht erst nach einem Normalitätstest. Das rankbasierte Verfahren prüft Verteilungsunterschiede und ist nicht automatisch ein Test gleicher Mediane. Hedges g und dessen unabhängiger Perzentil-Bootstrap (5.000 Wiederholungen, deterministischer Seed) ergänzen den Welch-Mittelwertunterschied mit t-Konfidenzintervall. Bei mehr als 1 % degenerierten Bootstrap-Ziehungen wird das g-Intervall nicht ausgegeben. Keine Mindestfallzahl ersetzt eine Powerplanung; sehr kleine Stichproben sind vorsichtig zu interpretieren.

Vier Reliabilitätsberichte: Nutzen, Kontrolle, Transparenz (je drei Items), Vertrauen (zwei). Zusätzlich bei Vertrauen Interitemkorrelation und Spearman–Brown. α wird nicht auf 0 begrenzt; negative Werte bleiben sichtbar. Gepoolte und gruppenspezifische Werte werden getrennt berichtet, weil Gruppenunterschiede gepoolte Reliabilität beeinflussen können. Ein hoher Koeffizient bestätigt keine Validität.

## Menschliche Prüfung der Belegtreue

Dies ist ein **zusätzliches Offline-Modul** und ersetzt nicht die vorhandenen Relevanzskripte. Bewertet wird, ob eine konkrete Begründung durch die Angaben im Profil und in der Anzeige gedeckt ist; nicht ob die Stelle im Ranking gefallen sollte.

Die Quelldatei ist JSONL mit `pair_id`, `study_arm`, `profile`, `job_id`, `job_text`, `explanation`. Alle Texte müssen bereits synthetisch oder für diese gesonderte Forschung rechtmäßig verfügbar sein. Das Live-System archiviert deshalb **nicht automatisch** Profile, Chats oder komplette Anzeigen-Begründungs-Paare. Der Modus `consented_research` ist eine Herkunftskennzeichnung des übergebenen Materials, kein Nachweis einer Einwilligung. Direkte Identifikatoren vor Weitergabe entfernen.

```sh
python -m research.v14.faithfulness sample /sicherer/pfad/paare.jsonl \
  --dataset-kind synthetic --count 60 --seed 20260922 \
  --output-dir /sicherer/pfad/belegtreue
python -m research.v14.faithfulness analyze \
  /sicherer/pfad/belegtreue/annotations.csv \
  /sicherer/pfad/belegtreue/arm_mapping_private.csv \
  --output /sicherer/pfad/belegtreue/auswertung.json
```

Die Stichprobe enthält 40–80 Paare, zufällig ohne Zurücklegen und zu gleichen Anteilen je Gruppe (±1). `annotations.csv` hat keine Gruppenkennung und enthält **leere** Raterfelder; die private Zuordnung bleibt bei der Studienleitung. Beide Rater erhalten getrennte Kopien mit denselben IDs und bewerten unabhängig. Erst danach werden ihre Spalten ohne nachträgliche Konsensänderung zusammengeführt; eventuelle spätere Adjudikation gesondert speichern. Inhalte können die Variante trotzdem erkennbar machen.

| Wert | Belegtreue | Entscheidungsregel |
| --- | --- | --- |
| 2 | Vollständig belegt | Alle wesentlichen Tatsachenbehauptungen über Profil und Anzeige sind gedeckt; Unbekanntes wird als unbekannt gekennzeichnet. |
| 1 | Teilweise belegt | Mindestens eine wesentliche Behauptung ist unbelegt oder übertrieben, andere wichtige Aussagen sind gedeckt. |
| 0 | Nicht belegt | Die zentrale Passungsbegründung hat keine ausreichende Grundlage oder widerspricht wesentlichen Angaben. |

Keine Aussage über fehlende Angaben als Tatsache akzeptieren (z. B. Mentoring aus einem Werbewort ableiten). Subjektive Empfehlung, klar markierte Vermutung und überprüfbare Behauptung unterscheiden. Vorab an **nicht in die Auswertungsstichprobe aufgenommenen** Trainingsbeispielen die Regeln abstimmen. Fehlende Bewertung bleibt leer, nicht 0.

Ausgabe: ungewichtetes Cohen-κ, beobachtete/erwartete Übereinstimmung, fehlende Paare sowie Verteilungen und Uneinigkeiten je Gruppe. Zweimal bewertete Paare sind keine zwei unabhängigen Beobachtungen. Bei nur einer identischen Kategorie ist κ mathematisch undefiniert und wird nicht als 1 ausgegeben. Rankingmetriken wie nDCG sind für diesen Belegtreue-Endpunkt ungeeignet und werden hier nicht vermischt.

## Plan einfrieren und unterschiedliche Behandlungsfassungen erkennen

`analysis_plan.json` ist die maschinenlesbare Ergänzung zum Protokoll. Sie steht zunächst auf `draft`; SESOI, Ausfallreserve, Zielzahl und Rekrutierungsfenster sind `null`. Vor der Hauptstudie die Entscheidungen und UTC-Zeitpunkte dokumentieren, den zugehörigen Git-Stand nachvollziehbar festhalten und erst dann `status` auf `frozen_before_main` setzen. Der Code prüft erforderliche Werte und die Reihenfolge Freeze < Beginn < Ende. Er verifiziert weder rückwirkend die Git-Zeitachse noch eine externe Präregistrierung; kein Datum rückdatieren. Die Datei schließt die Erhebung nicht automatisch und erzeugt keine zusätzliche Verwaltungsfreigabe.

Jeder Analysebericht enthält Dateiinhalt und SHA-256. Änderungen an Hypothesen/Testfamilie erfordern eine neue Analysefassung statt einer stillschweigenden Planänderung. Gemischte Promptrevisionen, Basisprompt-Hashes oder Systemrelease-IDs innerhalb einer Gruppe werden getrennt je Arm dokumentiert und als vorläufig gepoolte Behandlungen markiert. Fehlende Versionsangaben bleiben unbekannt. Die Statistik wirft keine Personen eigenmächtig weg und behauptet bei gemischten Versionen keinen einheitlichen konfirmatorischen Treatment-Effekt; Unterschiede und passende, vorab begründete Sensitivitäten müssen berichtet werden.
