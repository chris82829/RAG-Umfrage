# Menschliche Relevanzprüfung für V12

Diese Werkzeuge bereiten eine unabhängige Relevanzprüfung vor. Sie laufen allein
mit Python 3 und dessen Standardbibliothek, ohne Flask, Studiendatenbank, API-Key
oder Modellaufruf. Sie ändern keine Umfrageantworten und verursachen keine
Modellkosten.

**Aktueller Datenstand:** Es liegen hier noch keine neu erfassten V12-Ranglisten
und keine menschlichen Urteile vor. Der historische Pilot vom 17. September
verwendet andere Systembedingungen und wird nicht als aktuelle Untersuchung
umetikettiert. Produktive Suchprofile und Chattexte werden nicht dauerhaft
gespeichert und sind deshalb keine nachträglich abrufbare Quelle für diesen
Export. Die mitgelieferte Demonstration verwendet ausschließlich erfundene
Software-Testdaten. Ihre Kennzahlen sind keine Forschungsresultate.

## 1. Aktuelle Eingaben erfassen

Für eine spätere Prüfung müssen ausdrücklich neue, vollständige Ergebnissnapshots
aus der zu prüfenden Systemversion bereitgestellt werden. Möglich sind vorab
definierte fiktive Profile mit tatsächlich durch das aktuelle System erzeugten
Resultaten. Kein Teilnehmerprofil wird für diese Vorbereitung heimlich geloggt.
Ein neuer Lauf mit echten Modellaufrufen ist nicht Teil dieser Skripte.

Die Eingabe ist eine JSON-Datei mit dieser Struktur (Werte sind Platzhalter):

```json
{
  "schema_version": 1,
  "provenance": {
    "system_git_commit": "vollständiger Commit der tatsächlich ausgeführten Version",
    "questionnaire_version": 12,
    "scoring_version": "Bewertungsrevision des Laufs",
    "corpus_sha256": "SHA-256 des tatsächlich verwendeten Stellenbestands",
    "captured_at": "2026-09-21T12:00:00Z",
    "source_kind": "current_system_capture",
    "model": "tatsächlich verwendeter Modell-Snapshot",
    "prompt_revision": "Revision oder SHA-256 der tatsächlich verwendeten Prompts",
    "ranking_scope": "captured_candidate_pool"
  },
  "pairs": [{
    "pair_id": "profil01-turn0-B-stelle123",
    "query_id": "profil01-turn0",
    "job_id": "stelle123",
    "profile_summary": "Vollständige, festgehaltene Angaben, anhand derer beurteilt werden soll.",
    "job_text": "Vollständige Stellenanzeige, einschließlich Anforderungen und Rahmenbedingungen.",
    "condition": "B",
    "rank": 1,
    "system_score": 82
  }]
}
```

Die eine Beispielzeile reicht nicht zum Sampling. Benötigt werden vollständige
Kandidatenlisten mehrerer Profile für A, B und C mit genügend unterschiedlichen
Scores. `rank` ist die tatsächliche ursprüngliche Position vor dem Sampling.
`query_id` identifiziert ein unverändertes Profil samt Informationsstand. Werden
im Gespräch Wünsche ergänzt, ist dafür eine neue `query_id` nötig. Bei einer
gegebenen `query_id` müssen Profil und Jobtext über Bedingungen hinweg identisch
sein; sonst ist ein gemeinsamer Relevanzmaßstab nicht gegeben. Die Annahme muss
bei der Erfassung geprüft werden. Bewertungen dürfen keine zusätzlichen geheimen
Profilinformationen erhalten, wenn der Effekt solcher Informationen nicht
ausdrücklich Gegenstand eines separaten Protokolls ist.

Die Commit-Prüfung verhindert versehentliches Mischen von Versionen; selbst
deklarierte Metadaten sind kein unabhängiger Nachweis einer tatsächlichen
Ausführung. Zusammen mit der Eingabe sollten deshalb Laufkonfiguration,
Promptrevision und unveränderte Originalausgaben aufbewahrt werden. Keine
Zugangsdaten aufnehmen. Der Code prüft unter anderem Versionsnummer, Commit,
Hashformat, IDs, Ranglücken und Scorebereich.

## 2. Vierzig Paare exportieren

Vom Projektverzeichnis aus:

```sh
python3 research/human_relevance/sample.py \
  --source /pfad/zu/aktuellen-v12-ergebnissen.json \
  --expected-system-commit VOLLSTAENDIGER_COMMIT_DES_LAUFS \
  --out /pfad/zu/neuem-exportverzeichnis \
  --export-pool
```

Standardmäßig werden genau **40 verschiedene Zeilen** ohne Zurücklegen gezogen:
14/13/13 über A/B/C; je Score-Stratum vier oder fünf. Die Verteilung der zusätzlichen
Zeilen und die Auswahl erfolgen reproduzierbar mit `--seed 20260921`.
Die Terzile werden anhand aller eingegebenen Scores **innerhalb jeder Bedingung**
bestimmt. `low` = niedrig, `medium` = mittel, `high` = hoch. Quantilgrenzen werden
im Manifest festgehalten. Gleiche Scores bleiben im selben Stratum; dadurch
können die Strata ungleich groß oder leer werden. Reichen einzelne Strata nicht
aus, bricht das Skript ab, statt Werte aufzuteilen, Zeilen zu duplizieren oder
die angekündigte Schichtung stillschweigend zu ändern. Dann braucht es weitere
aktuelle Fälle oder eine vorab dokumentierte Änderung des Samplingplans.

Erzeugte Dateien:

- `sample.csv`: die verlangten acht Spalten `pair_id, profile_summary, job_text,
  condition, score_band, system_score, rater1_relevance, rater2_relevance`.
- `rater1.csv` und `rater2.csv`: unabhängig gemischte, verblindete Bögen; nur
  neutrale IDs, Profil, Stellenanzeige und leere Urteilsspalte.
- `manifest.json`: Quelle und Prüfsumme, Provenienz, Seed, Schichtung,
  Dateiprüfsummen und Zuordnung der verblindeten IDs.
- Mit `--export-pool`: zusätzlich `pool.csv`, `pool-rater1.csv` und
  `pool-rater2.csv` für den **gesamten erfassten Kandidatenpool**. Das ist eine
  zusätzliche Bewertungsmenge und nicht durch die Stichprobe von 40 ersetzt.

Nur die verblindeten Bögen an die jeweiligen Bewertenden geben. `sample.csv`,
Scores und Manifest können sonst die Urteile beeinflussen. Bestehende Exporte
werden nicht überschrieben, damit zurückgegebene Urteile erhalten bleiben.
CSV ist UTF-8 mit BOM; Text, der Tabellenformeln auslösen könnte, wird geschützt.

## 3. Beurteilungsrubrik vorab festlegen

Vorgeschlagene projektspezifische Rubrik; vor den Haupturteilen an einigen
separaten Beispielen gemeinsam klären und anschließend einfrieren:

| Wert | Bedeutung |
|---|---|
| 0 | Nicht passend: wesentliche ausdrücklich genannte Anforderungen widersprechen dem Profil/Suchbedarf. |
| 1 | Eingeschränkt passend: nur Teilpassung; erhebliche fachliche oder praktische Lücken. |
| 2 | Passend: wesentliche Anforderungen und Suchwünsche passen, mit begrenzten offenen Punkten. |
| 3 | Sehr passend: starke belegte Passung zu den zentralen Anforderungen und Suchwünschen. |

Beurteilt wird die Stellenrelevanz für das festgehaltene Profil, nicht die
Formulierung einer KI-Begründung. Anforderungen nicht hinzuerfinden. Bei fehlendem
Text oder nicht beurteilbarem Fall die Zelle leer lassen und separat Rückmeldung
geben; fehlend ist nicht gleich 0. Zwei Bewertende urteilen zunächst unabhängig.
Diese Rubrik ist eine transparente Operationalisierung, keine Behauptung einer
extern validierten Skala. Verwandte Profile oder dieselbe Stelle in mehreren
Bedingungen sind keine unabhängigen Studienteilnehmenden.

## 4. Rückgaben auswerten

```sh
python3 research/human_relevance/evaluate.py \
  --source /pfad/zu/aktuellen-v12-ergebnissen.json \
  --expected-system-commit VOLLSTAENDIGER_COMMIT_DES_LAUFS \
  --manifest /pfad/zu/export/manifest.json \
  --rater1 /pfad/zu/rueckgabe/rater1.csv \
  --rater2 /pfad/zu/rueckgabe/rater2.csv \
  --out /pfad/zu/auswertung-v1.json
```

Der Bericht enthält nominales **Cohen's Kappa** mit Übereinstimmungsquote sowie
**Spearman-Korrelation** zwischen dem mittleren Urteil beider Rater und dem
Systemscore, insgesamt und je Bedingung. Bindungen erhalten mittlere Ränge.
Es werden ausschließlich gemeinsam bewertete Zeilen verwendet. Konstante
Variablen oder fehlende Urteile ergeben `not_estimable` und `null`, keinen
erfundenen Nullwert. Der Bericht enthält Fallzahlen und Quelldigests. Die
Schichtung verändert die Scoreverteilung; die Korrelation beschreibt diese
Stichprobe, keine ungewichtete Gesamtpopulation. Es werden keine Signifikanztests
aus voneinander abhängigen Paaren abgeleitet.

Daneben entsteht `auswertung-v1.ratings.csv`. Für Rankingmetriken dürfen
unterschiedliche Einzelurteile **nicht einfach als Konsens gemittelt werden**.
Bei identischen Urteilen wird deren Wert als Konsens verwendet. Bei Differenzen
kann nach einer getrennten Abstimmung die Spalte `consensus_relevance` ergänzt
werden. Die beiden Originalurteile bleiben für Kappa unverändert. Eine gemeinsame
Profil-Stellen-Kombination muss über die Bedingungen hinweg dasselbe Konsensurteil
haben; Widersprüche werden als nicht auswertbar gemeldet.

Nach einer solchen Ergänzung ist eine neue Auswertung möglich:

```sh
python3 research/human_relevance/evaluate.py \
  --source /pfad/zu/aktuellen-v12-ergebnissen.json \
  --expected-system-commit VOLLSTAENDIGER_COMMIT_DES_LAUFS \
  --ratings /pfad/zu/konsens-ratings.csv \
  --out /pfad/zu/auswertung-v2.json
```

### Grenzen von nDCG@10 und Precision@10

Die 40 über Bedingungen und Score-Terzile verteilten Paare bilden normalerweise
**keine vollständig beurteilten Top-10-Listen**. Daher sind diese Metriken allein
daraus nicht bestimmbar. Das Skript meldet den Grund je Liste ausdrücklich.

- **Precision@10:** benötigt zehn tatsächlich gerankte Stellen mit Konsensurteil;
  Relevanzschwelle ist vorab auf **mindestens 2** gesetzt, Nenner ist 10.
- **nDCG@10:** benötigt zusätzlich den vollständigen menschlich beurteilten Pool
  der für dieselbe `query_id` in A/B/C erfassten Kandidaten. Aus dessen besten zehn
  Konsensurteilen wird IDCG berechnet. Gain = `2^Urteil − 1`, Diskontierung =
  `log2(Rang + 1)`. Sind alle Urteile 0, ist nDCG nicht definiert.
- Die Normalisierung bezieht sich auf diesen dokumentierten Kandidatenpool,
  **nicht auf einen vollständig menschlich beurteilten Korpus von rund 8.000 Stellen**.
- Gruppenmittel enthalten nur auswertbare Ranglisten und weisen deren Anzahl aus.
  Nicht vollständig auswertbare Gruppen nicht als vollständig bewerteten
  Systemvergleich präsentieren. Die Kennzahlen belegen keine kausale Wirkung der
  Persönlichkeit; dafür bleibt die separat geplante Nutzerstudie erforderlich.

Für diese Metriken die zusätzlichen Pool-Bögen beurteilen lassen. Der Export
macht den höheren Bewertungsaufwand sichtbar; er ersetzt ihn nicht durch
LLM-Urteile. Es werden weder unbewertete Stellen als irrelevant behandelt noch
die Stichprobe nachträglich zu neuen Pseudo-Ranglisten sortiert.

## 5. Offline-Demonstration und Tests

```sh
python3 research/human_relevance/example.py --out /tmp/diana-relevance-demo
python3 -m unittest discover -s research/human_relevance -p 'test_*.py' -v
```

Die Demonstration baut 180 frei erfundene Software-Testzeilen auf, exportiert
daraus 40 und erzeugt ausdrücklich als `SYNTHETIC` markierte künstliche Urteile.
Sie zeigt sowohl den nicht auswertbaren Stichprobenfall als auch vollständig
beurteilte Test-Ranglisten. Kein Modell und kein Mensch wurde dafür befragt.
Für solche Daten verlangen die beiden regulären CLIs ausdrücklich
`--allow-synthetic`; die Kennzeichnung bleibt in allen Berichten erhalten.

**Vor einer echten Ergebnisdarstellung fehlen weiterhin:** aktuelle dokumentierte
Systemausgaben, unabhängige menschliche Rückgaben, gegebenenfalls Konsensbildung
und vollständige Poolurteile für Rankingmetriken. Keine dieser Tätigkeiten wird
als bereits erledigt ausgegeben.
