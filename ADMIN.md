# Umfrageverwaltung und Numiqo

Die lokale Verwaltung ist unter http://127.0.0.1:5050/verwaltung erreichbar.
Sie ist vom Teilnehmerbereich getrennt und benötigt ein eigenes Passwort.
Die lokal erzeugten Zugangsdaten liegen außerhalb des Repositorys in
`../DIANA-Verwaltung-Zugang.txt` (nur für den lokalen Benutzer lesbar).
Diese Datei und `.env` gehören nicht in Git oder in ein Quellcodearchiv.

## Teilnahme freigeben oder pausieren

Oben in der Verwaltung steht der Bereich **Umfrage freigeben**. Der Button
schaltet zwischen **Umfrage freigeben** und **Umfrage pausieren** um. Die Änderung
wirkt sofort und bleibt in SQLite über Containerwechsel und Neustarts erhalten.
Eine Pause sperrt neue Einwilligungen sowie weitere Such-, Chat- und
Umfrageabgaben. Vorhandene Antworten bleiben erhalten; Widerruf und Verwaltung
funktionieren weiter. Nach erneuter Freigabe gelten vorhandene Einwilligungen
weiter, sofern deren Wortlaut nicht geändert wurde. Der Status einer noch
ungeöffneten Teilnahme wird alle 15 Sekunden und beim Zurückwechseln in den Tab
aktualisiert.

`privacy_settings.json: approved` ist nur noch der Anfangswert, solange noch
kein Status in der Verwaltung gesetzt wurde. Die Laufzeiteinstellung ist eine
Betriebsfreigabe, keine rechtliche Bescheinigung. Eine mit `privacy-end-study`
endgültig beendete und bereinigte Studie kann über diesen Schalter nicht
wiederhergestellt werden.

## Ergebnisse bearbeiten

- Die Übersicht zeigt Teilnahme-ID, Abgabezeitpunkt und Fragebogenversion.
- Suche anhand der vom Teilnehmer zugesandten ID oder filtere nach Version.
- Öffne eine Antwort, um alle Angaben und den zugeordneten Modellstand zu sehen.
- Zum Löschen muss die vollständige Teilnahme-ID eingegeben werden. Die angezeigte
  Anzahl umfasst alle Antworten dieser Teilnahme. Die Teilnahme wird zugleich
  widerrufen; weitere Schreibversuche mit ihrem Zugangscode sind gesperrt.
- Alte Antworten ohne Einwilligungszuordnung können einzeln gelöscht werden.
- Bereits heruntergeladene Kopien und Backups müssen separat bearbeitet werden.

Die Anwendung verändert vorhandene Antworten nicht. Auf der lokalen Instanz
sind nur lokale Antworten sichtbar; Serverantworten bleiben in der Serverdatenbank.

## In Numiqo auswerten

1. In der Verwaltung **CSV für Numiqo** oder **Auswertungspaket** wählen.
   Beide berücksichtigen den aktuellen ID- und Versionsfilter, über alle Seiten hinweg.
2. Das Paket entpacken und in Numiqo über **Import/Export** die Datei
   `diana_numiqo.csv` auswählen: UTF-8, Semikolon als Trennzeichen, erste Zeile als
   Variablennamen. Numiqo unterstützt CSV-Dateien laut
   [offiziellem Handbuch](https://numiqo.com/tutorial/user-manual).
3. Die Variablentypen und Wertelabels anhand von `codebook.csv` oder
   `codebook.json` einstellen. Das Codebuch wird nicht automatisch in Numiqo geladen.

Eine Zeile entspricht einer abgegebenen Teilnahme. V4 verwendet eigene `v4_`-Spalten:
Ja=1, Nein=0 (nominal); fünf beschriftete Kategorien (ordinal); Nützlichkeit und Chat-Hilfe
1–10 (ordinal). Demografische Auswahlwerte sind im Codebuch codiert; Freitext bleibt Text.
ID, Modell und Version sind nominal. „Unentschieden“ bei Wiederverwendung ist der gültige
Wert 3. Fehlende Bewertungen sind leer, nicht 0. Die jeweilige `_status`-Spalte erklärt:
`answered`, `not_used`, `not_assessable`, `not_specified`, `skipped`, `no_answer`, `not_asked`.
Bei `chat_used=no` bleiben die drei Folgefragen leer (`skipped`).

Historische V2/V3-Antworten bleiben in den bisherigen Spalten, V1 bleibt in `v1_`-Spalten.
Antworten verschiedener Frageformulierungen oder Skalen nicht ungeprüft zusammenfassen.
Versionsfilter, Detailansicht und Codebuch berücksichtigen V4; die Detailansicht zeigt
für alte Antworten weiterhin deren ursprüngliche Frageformulierungen.
Formelähnlicher Freitext erhält ein vorangestelltes Apostroph zum Schutz beim
Öffnen in Tabellenprogrammen; dies bei qualitativer Textauswertung berücksichtigen.

Es erfolgt kein automatischer Upload an Numiqo. Ein Import im dortigen Konto
ist eine eigene Datenweitergabe; die Dateien enthalten pseudonyme Einzelantworten
und Freitext, keine anonymen Statistiken.

## Modellstand für die Veröffentlichung

Alle OpenAI-Aufrufe verwenden **`gpt-5.4-2026-03-05`** mit
**`reasoning.effort=none`** und `store=False`. Dieser feste Snapshot ist in der
[OpenAI-Modellübersicht](https://developers.openai.com/api/docs/models/gpt-5.4)
dokumentiert und wurde über die Modellabfrage im verwendeten API-Projekt bestätigt.
Es gibt keinen automatischen Rückfall auf einen Alias oder ein anderes Modell.

`study_manifest.json` im Auswertungspaket enthält die für exportierte Teilnahmen
erfassten Systemstände: OpenAI-Snapshot, Denkaufwand, Ausgabelimits,
E5-Modell samt Revision, Retrieval-Parameter, Paketversionen und SHA-256-Prüfsummen
der zentralen Quelldateien und der normalisierten Stellenbasis. Neue
Such-/Chataktionen ordnen den aktuellen Systemstand der Teilnahme zu. Bei Abgabe
werden diese Zuordnungen festgehalten. Mehrere genutzte Stände bleiben sichtbar.
Historische Antworten ohne diese Erfassung erhalten keine rückwirkend erfundene
Modellzuordnung. Die aktuelle Konfiguration steht im Manifest separat.

Für eine Konferenz zusätzlich den passenden Quellcode, Abhängigkeiten und eine
rechtlich nutzbare Stellenbasis archivieren: Prüfsummen allein rekonstruieren
keine Dateien. Ein fester Snapshot erhöht die Nachvollziehbarkeit, garantiert aber
keine identischen generierten Antworten. Individuelle Prompts und Chatverläufe
werden weiterhin nicht dauerhaft gespeichert; einzelne Teilnehmersuchen lassen
sich deshalb nicht vollständig nachspielen.

## Zugang einrichten oder ändern

`DIANA_ADMIN_PASSWORD_HASH` in `.env` enthält ausschließlich einen Werkzeug-Hash.
Es gibt kein Standardpasswort. Einen Hash über eine verdeckte Eingabe erzeugen:

```bash
.venv/bin/python -c 'from getpass import getpass; from werkzeug.security import generate_password_hash; print(generate_password_hash(getpass("Neues Verwaltungspasswort: ")))'
```

Den ausgegebenen Hash als `DIANA_ADMIN_PASSWORD_HASH` in `.env` eintragen,
die Datei auf Dateimodus 600 beschränken und den Dienst neu starten.
Admin-Anmeldungen liegen nur im RAM, verfallen nach acht Stunden und enden bei
Neustart. Wie die Suchsitzungen setzt die Verwaltung den vorhandenen Betrieb mit
einem Gunicorn-Worker und mehreren Threads voraus.

Anmeldung ist gegen wiederholte Fehlversuche begrenzt. Der Sitzungscookie ist
HttpOnly und SameSite=Strict; über HTTPS zusätzlich Secure. Schreibaktionen
benötigen einen CSRF-Token. Betrieb auf dem Server erfordert konfigurierte
Zugangsdaten und einen geschützten Transport. Diese lokale Änderung schaltet
die noch ausstehende Studienfreigabe in `privacy_settings.json` nicht frei.

## Automatisch gespeicherte Teilantworten

Seit diesem Stand werden Entwürfe nach jeder Antwort gespeichert. Die Verwaltung
zeigt `Unvollständig` und `Abgeschlossen` mit einem Statusfilter, der auch für Downloads
gilt. `response_status` und `last_saved_at_utc` sind im Export enthalten; bei unvollständigen
Teilnahmen ist `submitted_at_utc` leer. Noch nicht beantwortete Pflichtfragen erhalten
`unanswered` in ihrer Statusspalte. Ein späterer Abschluss ersetzt den Entwurf, ohne eine
zweite Teilnahme anzulegen. Löschung über dieselbe Teilnahme-ID entfernt auch Entwürfe.

## Fragebogen V5

Alle subjektiven Bewertungen verwenden 1–10. Neue Antworten stehen in `v5_`-Spalten, historische V4-Werte unverändert in `v4_`-Spalten. Die Frage nach einer eigenen Chatnachricht entfällt in V5. Filter und Codebuch unterscheiden beide Versionen; Werte verschiedener Skalen nicht ungeprüft zusammenfassen.

## B/C-Vergleich (V6)

In der Verwaltung lassen sich B und C separat filtern; die Tabelle zeigt die Variante. CSV/Numiqo-ZIP enthalten `study_arm`, `experiment_id`, `assigned_at_utc`, `prior_exposure` sowie die v6_-Antwortspalten. Nur V6-Teilnahmen erhalten diese Experimentmetadaten. Persönlichkeitsfragen sind bei B als `skipped` gekennzeichnet. Abbrüche können unter `Unvollständig` betrachtet werden.
