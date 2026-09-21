# DIANA V12 – Änderungen und Prüfgrenzen

Stand: 21. September 2026. Neue Zuordnungen: `diana-abc-v5`; Fragebogen:
`diana-v12`; Scoring: `fixed-balanced-v4`. Historische Fragebogen-Dateien und
Antworten bleiben erhalten. Dies ist eine technische Änderungsübersicht, keine
Präregistrierung oder Validierungsbescheinigung.

## 1. Gleiche Bewertungsgewichte

`advisor.py` enthält eine gemeinsame `SCORING_WEIGHTS`-Konstante: Fachpassung 60,
Profilpräferenzen 15, fachliche Tiefe 7, Lernen 6, Innovation 6 und Klarheit 6 Prozent.
Die frühere B-spezifische Gewichtung entfällt. `test_scoring_weights_v12.py` prüft
die Gleichheit bei A/B/C und abweichenden Ausgangskonfigurationen.

Die fachlichen Systemprompts werden nicht umgeschrieben. Gleiche Rechengewichte
bedeuten deshalb nicht, dass LLM-Teilbewertungen oder resultierende Rangfolgen
identisch sein müssen. Die Release-Metadaten in `study_release.py` dokumentieren
den Scoringstand. Fortgesetzte alte Teilnahmen können den neuen Softwarestand
verwenden; alte Zuordnungen sind kein Nachweis unveränderter Ausführung.

## 2. Drei erfolgreiche Chatnachrichten

Der Übergang zum Fragebogen verlangt genau drei erfolgreich abgeschlossene eigene
Nachrichten. Das bestehende Maximum bleibt drei. Automatische Begrüßungen und
fehlgeschlagene Anfragen zählen nicht; das Limit gilt über Suchsitzungen und
Neuladen hinweg. Separate Testseiten bleiben unbegrenzt.

- Server: `study_progress.py`, `study_chat_limit.py`, `app.py`.
- Frontend: `frontend/survey.js`, `frontend/survey-progress.js`,
  `frontend/SurveyPage.jsx`, `frontend/main.jsx`.
- Regression: `test_study_progress_v12.py`, `frontend/survey.test.js`.

Der Server prüft auch direkt abgesendete Bewertungsentwürfe und Abschlüsse.
Clientzustand allein berechtigt nicht zum Übergang. Die feste Anzahl ist ein
Interaktionsbudget für die Studie und keine Beobachtung freiwilligen Engagements.

## 3. Ereignisse und sichtbare Betrachtungszeit

`study_telemetry.py` und `migrations/012_study_telemetry.sql` ergänzen
`track_events`. `frontend/telemetry.js` erfasst sichtbare Intervalle und Klicks;
die Einbindung erfolgt in `frontend/main.jsx` und `frontend/SurveyPage.jsx`.
`chat_turn` entsteht serverseitig aus demselben erfolgreichen Chat-Zähler wie
das Nachrichtenlimit. `privacy.py` und die Datenschutzhinweise berücksichtigen
die zusätzliche Erfassung und Löschwege.

`admin.py` stellt `/api/admin/telemetry-export` geschützt bereit;
`frontend/AdminPage.jsx` bietet **Nutzungsereignisse als CSV** mit denselben
Teilnahmefiltern wie der Antwortexport. `test_study_telemetry.py` und
`frontend/telemetry.test.js` prüfen Erfassung, Sichtbarkeit, Zuordnung und Grenzen.
Die vollständige Messdefinition steht in [STUDY-TELEMETRY.md](STUDY-TELEMETRY.md).
Es werden keine Chat-, Profil- oder Persönlichkeitstexte als Ereignisse gespeichert.

## 4. Fragebogen, Speicherung und Verwaltung

`survey_definition_v12.json` ist die gemeinsame verbindliche Quelle. A/B/C sehen
17/21/22 Fragen. Die sechs Hintergrundfragen erscheinen vor Systembeginn.
Die drei neuen Nutzenitems verwenden fünf beschriftete Zustimmungsstufen plus
„Kann ich nicht beurteilen“. Übrige Bewertungen bleiben 1–10. Die Frage zur
Formulierung der Begründungen erhält den neuen Schlüssel
`personality_clarity_explanations`; die Bewertungsschwerpunktfrage entfällt.

- Daten und Migration: `survey_store.py`, `survey_migrations.py`.
- Fragebogen und Darstellung: `frontend/survey.js`, `frontend/SurveyPage.jsx`,
  `frontend/survey.css`.
- Verwaltung und Auswertung: `admin.py`, `admin_store.py`, `survey_analytics.py`,
  `export_columns.py`, `frontend/AdminPage.jsx`, `frontend/AdminAnalytics.jsx`,
  `frontend/AdminAnswerEditor.jsx`, `frontend/admin-answer-editor.js`,
  `frontend/admin-prompt-labels.js`.
- Versionszuordnung und Nachweis: `study_assignment.py`, `study_release.py`,
  `test_study_versioning.py`, `test_survey_v12.py`, `test_prompt_exposure.py`,
  `frontend/survey.test.js`, `frontend/admin-prompt-labels.test.js`.

Die wiederholbare Startmigration ergänzt drei generierte INTEGER-Spalten
`usefulness_effective`, `usefulness_speed` und `usefulness_overall` in Antworten
und Entwürfen. Sie folgen der jeweiligen JSON-Quelle automatisch; historische
Antworten werden weder gelöscht noch auf die neue Skala umgerechnet. Standalone:

```sh
python survey_migrations.py /pfad/zur/datenbank.sqlite3
```

Protokollentwurf: Mittelwert der drei Nutzenitems nur bei **drei** numerischen
Antworten 1–5; andernfalls fehlender Endpunkt. Die Verwaltung zeigt Einzelitems,
keine automatisch validierte Gesamtskala. Die Formulierungen sind eine noch zu
prüfende Anpassung. `research/analyze_primary.py` unterstützt nur historische
V9–V11-Einzelitems und ist **nicht** für V12 freigegeben.

## 5. Vorbereitung menschlicher Relevanzurteile

`research/human_relevance/sample.py` exportiert 40 geschichtete Paare und
verblindete Bewertungsbögen aus ausdrücklich bereitgestellten aktuellen
Systemausgaben. `evaluate.py` berechnet nach Rückgabe Kappa und Spearman;
Rankingmetriken werden nur bei ausreichend vollständig beurteilten Listen
beziehungsweise Kandidatenpools ausgegeben. `common.py` enthält die gemeinsam
geprüften Datenverträge; `test_human_relevance.py` und `example.py` nutzen
synthetische Software-Testdaten.

[Anleitung und Grenzen](research/human_relevance/README.md): Aktuelle echte
V12-Ranglisten und menschliche Urteile liegen noch nicht vor. Es wurden dafür
keine neuen kostenpflichtigen Modellläufe gestartet. Synthetische Testkennzahlen
sind keine Forschungsergebnisse. Die 40 geschichteten Einzelpaare ersetzen keine
vollständig beurteilten Top-10-Listen für nDCG@10 oder Precision@10.

Weitere Dokumentation: [README](README.md), [Verwaltung](ADMIN.md),
[Protokollentwurf](STUDY-PROTOCOL.md), [historische Forschung](research/README.md).
