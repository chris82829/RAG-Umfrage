# Gezielte Rückfragen – Entwicklungsprüfung vom 18. September 2026

Version `ranking-followup-v3`, Modell `gpt-5.4-2026-03-05`, Denkaufwand `none`.
Diese kleine technische Prüfung verwendet ausschließlich zwei erfundene Stellen
und ein synthetisches Python-/SQL-Profil. Sie ist kein Konferenzbenchmark, kein
Nutzertest und kein Nachweis einer optimalen Rangfolge.

## Änderung

Berufsberater und Fachexperte sollen jede Suchansprache und Beratungsantwort mit
einer konkreten Frage zu einem noch offenen Sortierkriterium abschließen. Die
Auswahl berücksichtigt Profil, Verlauf und belegte Anzeigenunterschiede. Eine
kurze eindeutige Antwort bestätigt die entsprechende Präferenz; bereits bekannte
Angaben werden nicht erneut erfragt. Unentschlossene Antworten ändern kein Profil.
Neue belegte Fähigkeiten bleiben von bloßen Lernwünschen getrennt.

Der Server übergibt `follow_up_allowed` anhand des tatsächlichen verbleibenden
Chatkontingents, einschließlich laufender Reservierungen. Nach der dritten
Studiennachricht soll keine weitere Antwort angefordert werden. Eigenständige
Testseiten bleiben unbegrenzt. Die Rückfrageregel gilt für B/C; A erhält keine
solche Pflicht. Modell, Gewichtung und Fragebogen wurden nicht geändert.

## Prüfung und Grenzen

- 16 Offline-Regressionstests in `test_survey_chat_limit.py` bestanden, darunter
  Rückfragenfreigabe beim Einstieg, in Planung/Neubewertung/neuer Suche, nach
  erschöpftem Kontingent sowie mehr als drei Nachrichten auf Testseiten B/C.
- 7 bestehende Frontendtests zum Nachrichtenlimit bestanden; Vite-Build erfolgreich.
- 8 Modellaufrufe in `smoke_test.py`: beide Vorlagen beim Einstieg, je eine kurze
  Präferenzantwort und Neubewertung, Unentschlossenheit, Abschluss ohne Rückfrage.
  Alle automatischen Kriterien bestanden. Antworten wurden zusätzlich gelesen.
- Dabei fiel eine semantisch schlechte Rückfrage auf: Sie verband eine schon
  entschiedene Betreuungspräferenz mit einer neuen Tätigkeitswahl. Die einfachen
  automatischen Kriterien (u.a. genau ein Fragezeichen) erkennen das nicht.
- Zwei gezielte Aufrufe nach einer Präzisierung lösten den Fall nur teilweise:
  Die Frage bei Unentschlossenheit war nun konsistent; die andere mischte weiterhin
  Dimensionen. `targeted-recheck.json` enthält auch diesen Fehlversuch.
- Ein konkretes korrektes Gesprächsbeispiel wurde ergänzt. Ein weiterer gezielter
  Aufruf stellte danach ausschließlich die offene Tätigkeitsfrage:
  „Möchtest du lieber Datenpipelines entwickeln oder eher Vorhersagemodelle trainieren?“
  Siehe `final-career-recheck.json`. Insgesamt **11 Modellaufrufe**, kein großer Testlauf.

Beide bestätigten Wünsche wurden im Profil gespeichert und die entsprechenden
Stellen erhielten den höheren Teilwert für Präferenzpassung. Das bedeutet nicht
zwangsläufig Platz eins: Fachpassung und der gewählte Beratungsschwerpunkt zählen
weiterhin mit. Die Beispiele belegen die Verkabelung und zeigen einzelne Ausgaben;
weitere Modellantworten können von den Vorgaben abweichen. Frühere Ausgaben sind
unverändert aufbewahrt. Es wurde keine statistische Wirksamkeit geschätzt.

## Wiederholung

Ohne `--live` verweigert das Skript API-Aufrufe. Mit `--live` entstehen Kosten für
acht Aufrufe; die konfigurierte API-Verbindung wird verwendet. Es liest keine
Teilnehmerantworten. `smoke-results.json` wird bei erneutem Aufruf überschrieben,
deshalb für unabhängige Wiederholungen vorher separat archivieren.

```bash
python -m unittest test_survey_chat_limit -q
node --test frontend/chat-limit.test.js
python research/development/2026-09-18-ranking-followups/smoke_test.py --live
```

Die Backend- und Frontend-Vorlagen wurden gemeinsam aktualisiert. Der Release-
Manifest-Mechanismus erfasst die geänderten Quellen und `advisory_version`.
