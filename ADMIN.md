# Umfrageverwaltung und Numiqo

Die lokale Verwaltung ist unter http://127.0.0.1:5050/verwaltung erreichbar.
Sie ist vom Teilnehmerbereich getrennt und benötigt ein eigenes Passwort.
Die lokal erzeugten Zugangsdaten liegen außerhalb des Repositorys in
`../DIANA-Verwaltung-Zugang.txt` (nur für den lokalen Benutzer lesbar).
Diese Datei und `.env` gehören nicht in Git oder in ein Quellcodearchiv.

## Systemprompts

Der Tab **Systemprompts** verwaltet die drei Varianten getrennt. A darf leer
bleiben; dann wird technisch keine Systemnachricht an das Modell gesendet. Ein
eingetragener Text wird ausschließlich für A verwendet. B enthält den festen
Top-Berufsberater, C die fachliche Basis für die anschließend serverseitig
ergänzte eigene Gestaltung.

Speichern erzeugt eine neue Revision und SHA-256-Prüfsumme. Reguläre Teilnehmende
behalten die beim ersten Assignment gebundene Fassung, auch wenn der Prompt später
geändert wird. Neue Teilnahmen und neue Sitzungen unter `/test/a`, `/test/b` oder
`/test/c` verwenden den dann aktuellen Stand. Der Export enthält nur Policy,
Revision und Prüfsumme, niemals den Prompttext.

Der Filter **Exakte Promptfassung** grenzt Einzelantworten, Diagramme und Exporte
auf genau eine Kombination aus Policy, Revision und Basis-SHA-256 ein. Ohne diese
Auswahl stellt die Verwaltung mehrere Promptfassungen innerhalb derselben Gruppe
in den Diagrammen getrennt dar und weist sichtbar auf gemischte Fassungen hin.

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

- Die Übersicht verwendet automatisch den aktuellen Fragebogen. Eine Auswahl
  historischer Fragebogenversionen wird nicht mehr angeboten.
- Suche anhand der vom Teilnehmer zugesandten ID oder filtere nach Studienvariante,
  Abschlussstatus und exakter Promptfassung.
- Öffne eine Antwort, um alle Angaben und den zugeordneten Modellstand zu sehen.
- **Antworten bearbeiten** öffnet die Eingabefelder der ursprünglichen
  Fragebogenversion. Einen Korrekturgrund angeben und **Korrektur speichern**
  wählen. Tippen allein speichert nichts; **Änderungen verwerfen** verwirft den
  lokalen Bearbeitungsstand. Pflichtfelder und Filterfragen werden geprüft.
- Teilnahme-ID, Studienzuordnung, Einwilligung, Fragebogenversion und ursprünglicher
  Abschlusszeitpunkt bleiben erhalten. Unvollständige Antworten bleiben Entwürfe.
  Gleichzeitige Änderungen durch andere Verwaltungsfenster oder Teilnehmer werden
  mit einer Konfliktmeldung geschützt; dann die Einzelantwort neu öffnen und prüfen.
- Der **Änderungsverlauf** zeigt Zeitpunkt, Grund sowie vorherige und gespeicherte
  Werte. Da der Zugang ein gemeinsames Passwort nutzt, lautet die Bearbeiterkennung
  `admin`; eine persönliche Bearbeiteridentität wird nicht behauptet.
- Zum Löschen muss die vollständige Teilnahme-ID eingegeben werden. Die angezeigte
  Anzahl umfasst alle Antworten dieser Teilnahme. Die Teilnahme wird zugleich
  widerrufen; weitere Schreibversuche mit ihrem Zugangscode sind gesperrt.
- Alte Antworten ohne Einwilligungszuordnung können einzeln gelöscht werden.
- Bereits heruntergeladene Kopien und Backups müssen separat bearbeitet werden.

Diagramme und Downloads verwenden den explizit gespeicherten Korrekturstand.
Die CSV dokumentiert `antwortkorrekturen_anzahl` und `zuletzt_korrigiert_am_utc`; das
Auswertungspaket enthält bei korrigierten Teilnahmen zusätzlich
`answer_corrections.json` mit den vollständigen Vorher-/Nachher-Antwortständen.
Der erste Vorher-Stand bewahrt die ursprünglichen Antworten vor einer
Verwaltungskorrektur. Bei Entwürfen können danach reguläre Teilnehmerantworten
folgen; der Verlauf dokumentiert Verwaltungskorrekturen, nicht jedes Autosave.
Die Historie folgt den gleichen Löschwegen wie die zugehörigen Antworten,
einschließlich Widerruf, Aufbewahrungsbereinigung und Verwaltungslöschung.

Die additive Startmigration legt `survey_answer_corrections`, einen Index und
Löschtrigger an. Vorhandene Antwortzeilen werden dadurch nicht verändert oder
nachträglich als korrigiert markiert. Auf der lokalen Instanz
sind nur lokale Antworten sichtbar; Serverantworten bleiben in der Serverdatenbank.

## In Numiqo auswerten

1. In der Verwaltung **CSV für Numiqo** oder **Auswertungspaket** wählen.
   Beide berücksichtigen den aktuellen ID-, Status-, Varianten- und
   Promptfassungsfilter über alle Seiten hinweg.
2. Unter **Spaltennamen** ist **Deutsch · verständliche Namen** vorausgewählt.
   **Technisch · bisherige Schlüssel** bleibt für vorhandene Auswertungsskripte verfügbar.
   Beide Formate enthalten dieselben Werte in derselben Reihenfolge; gespeichert wird
   weiterhin unter den bisherigen Antwortschlüsseln.
3. Das Paket entpacken und in Numiqo über **Import/Export** die Datei
   `diana_numiqo.csv` auswählen: UTF-8, Semikolon als Trennzeichen, erste Zeile als
   Variablennamen. Numiqo unterstützt CSV-Dateien laut
   [offiziellem Handbuch](https://numiqo.com/tutorial/user-manual).
4. Variablentypen und Wertelabels anhand von `codebook.csv` oder `codebook.json`
   einstellen. Das Codebuch wird nicht automatisch in Numiqo geladen.
   `spaltenzuordnung.csv` verbindet jeden Exportnamen mit technischem Originalschlüssel,
   vollständiger Frage und Fragebogenversion. `study_manifest.json` dokumentiert
   zusätzlich die gewählte Spaltenbenennung.

Beispiele für den Standardexport:

| Exportspalte | Bedeutung |
| --- | --- |
| `teilnahme_id` | Pseudonyme Teilnahme-ID |
| `teilnahme_status` | `completed` oder `in_progress` |
| `studiengruppe` | A, B oder C; Bedeutung zusammen mit Version und Experiment auswerten |
| `v12_chat_hilfe_suchwuensche` | Hilfe des Chats beim Konkretisieren der Suchwünsche |
| `v12_score_nutzen` | Nützlichkeit des Scores für den Überblick |
| `v12_begruendungen_nutzen` | Nützlichkeit der Begründungen zum Nachvollziehen |
| `v12_suche_aufwand` | Aufwand: hoher Wert bedeutet **mehr** Aufwand |
| `v12_ki_selbst_angepasst_selbstauskunft` | C-Selbstauskunft zur tatsächlichen Veränderung der vorgeschlagenen Ausgangskonfiguration |
| `v12_system_nutzen_effektivitaet` | Effektivität der Stellensuche, Zustimmung 1–5 |
| `v12_system_nutzen_geschwindigkeit` | Passende Stellen schneller finden, Zustimmung 1–5 |
| `v12_system_nutzen_gesamturteil` | Gesamtnützlichkeit, Zustimmung 1–5 |
| `ki_letzte_verwendung` | Automatisch erfasste Herkunft der angewendeten Persönlichkeit |

Spaltennamen sind eindeutig, klein geschrieben und verwenden ausschließlich
ASCII-Buchstaben, Ziffern und Unterstriche. Die API verwendet standardmäßig
`/api/admin/export?columns=readable`; `columns=technical` erhält die bisherigen
technischen Namen. Das gilt für CSV und ZIP. Der geschützte serverseitige
`survey-export`-Befehl verwendet ebenfalls die verständlichen Spaltennamen;
sein historisches Textformat für Auswahlantworten bleibt erhalten. Für numerische
Numiqo-Auswertungen den Verwaltungsdownload verwenden.

Eine Zeile entspricht einer Teilnahme. Der aktuelle Vergleich ist
**`diana-abc-v5` / `diana-v12`**, mit eigenen `v12_`-Spalten. A/B/C sehen
**17/21/22 Fragen** inklusive optionaler Fachrichtung und Feedback. Die drei
Nutzen-Aussagen haben Werte 1–5 mit den Ankern „Stimme gar nicht zu“ bis „Stimme
voll zu“, die anderen Bewertungsfragen bleiben 1–10. Ja=1 und Nein=0.

A hat keine wählbare Persönlichkeit; sein separates Promptfeld ist standardmäßig
leer. B nutzt den festen Top-Berufsberater, C dessen selbst gestaltbare Variante.
Alle verwenden gleiche Scoring-Gewichte 60/15/7/6/6/6. Unterschiedliche Prompts
können trotzdem unterschiedliche Teilbewertungen und Rankings erzeugen.
`v12_studiengruppe_originalcode` bedeutet **0=A, 1=B, 2=C**; `studiengruppe`
enthält direkt den Buchstaben. Alle zufällig C zugeteilten Teilnahmen bleiben C,
auch ohne inhaltliche Änderung der Ausgangskonfiguration.

V12 erhebt keine Bewertungsschwerpunkte mehr. Die frühere Rangfolgenfrage wird
nicht umbenannt oder überschrieben: die neue Frage zur Formulierung der Begründungen
steht in `v12_ki_wirkung_sprachstil_begruendungen_verstaendnis` (technisch
`v12_personality_clarity_explanations`). Alte Antwortfelder sind seit V12 deprecated
und bleiben in den jeweiligen historischen Versionen erhalten. Nicht gestellte
Fragen bleiben leer mit Status `skipped`.

Die Startmigration `survey_migrations.py` ergänzt drei generierte INTEGER-Spalten
für V12-Nutzenwerte in Antworten und Entwürfen. Sie werden aus den versionierten
JSON-Antworten abgeleitet und folgen damit auch Verwaltungskorrekturen automatisch.
Der Bereich 1–5 wird geprüft; fehlende und nicht beurteilbare Werte bleiben NULL.
Die Migration ist wiederholt ausführbar und löscht keine historischen Daten.
Standalone: `python survey_migrations.py /pfad/zur/datenbank.sqlite3`.

Historische V11-Antworten behalten `v11_`-Spalten und `diana-abc-v4`, einschließlich
des 1–10-Einzelitems `system_usefulness`, der früheren Rangfolgenfrage und der
Bewertungsschwerpunkte. Sie werden nicht in die neue Skala überführt.

Historische V10-Antworten behalten `v10_`-Spalten und `diana-abc-v3`: A war die
feste sachliche Standardberatung, B bot Top-Berufsberater oder Fachexperte und C
zusätzlich Selbstgestaltung. Diese Kohorte nicht mit V11 zusammenführen.

Historische V9-Antworten behalten `v9_`-Spalten und `diana-abc-v2`. Die
Systembedingungen waren bereits fair, der Fragebogen aber länger. V9 und V10
werden getrennt ausgewertet. Die alten Einrichtungsbewertungen bleiben in V9
lesbar; es werden weder Werte gelöscht noch Antworten für V10 ergänzt.

Historische V8-Antworten behalten `v8_`-Spalten und `diana-abc-v1`. A hatte dort einen allgemeinen Chat, Zufallsreihenfolge und keine Scores/Begründungen; diese Daten sind keine Standardberatungs-Baseline aus V10.

Historische V7-Antworten behalten ihre eigenen Spalten und Codes **0=A, 1=B**.
B war dort frei gestaltbar und darf nicht als neue Vorlagengruppe B behandelt werden.

Historischer Fragebogen V4 verwendet eigene `v4_`-Spalten:
Ja=1, Nein=0 (nominal); fünf beschriftete Kategorien (ordinal); Nützlichkeit und Chat-Hilfe
1–10 (ordinal). Demografische Auswahlwerte sind im Codebuch codiert; Freitext bleibt Text.
ID, Modell und Version sind nominal. „Unentschieden“ bei Wiederverwendung ist der gültige
Wert 3. Fehlende Bewertungen sind leer, nicht 0. Die jeweilige `_antwortstatus`-Spalte
(im technischen Format `_status`) erklärt `answered`, `not_used`, `not_assessable`,
`not_specified`, `skipped`, `no_answer`, `not_asked` und `unanswered`.
In V4 bleiben bei `chat_used=no` die drei Folgefragen leer (`skipped`). Diese Frage
entfällt in den neueren Versionen.

Identische historische V2/V3-Fragen stehen in `v2_v3_`-Spalten, die vier zusätzlichen
V3-Nützlichkeitsfragen in `v3_`-Spalten und V1-Antworten in `v1_`-Spalten.
Spätere Versionen bleiben separat in `v4_` bis `v12_`.
Antworten verschiedener Frageformulierungen oder Skalen nicht ungeprüft zusammenfassen.
Das Codebuch enthält den vollständigen Originalwortlaut, Antwortcodes und Originalcodes,
Skalenenden, fehlende Werte, Filterführung und Bewertungsrichtung. Die Aufwandsfrage ist
explizit als gegenläufig markiert (`reverse_direction=true`); die Zahlen werden **nicht**
automatisch umgepolt. Daraus entsteht kein ungeprüfter Gesamtwert.
Formelähnlicher Freitext erhält ein vorangestelltes Apostroph zum Schutz beim
Öffnen in Tabellenprogrammen; dies bei qualitativer Textauswertung berücksichtigen.

### Aggregierte Nutzung und Laufzeiten

Seit V9 werden abgeschlossene Serveroperationen als Summen erfasst. Für diese Summen werden keine Rohtexte, IP-Adressen oder Gerätekennungen gespeichert.
V12 ergänzt davon getrennte Interaktionsereignisse, wie unten beschrieben.

| Spalten | Bedeutung |
| --- | --- |
| `nutzung_erfassungsversion` | 0 = nicht erfasst; 1 = aktuelle Erfassung |
| `suchen_erfolgreich_anzahl`, `suchen_fehlgeschlagen_anzahl` | Tatsächlich abgeschlossene Suchversuche |
| `neusortierungen_erfolgreich_anzahl`, `neusortierungen_fehlgeschlagen_anzahl` | Tatsächliche Neubewertungen bestehender Ergebnisse |
| `chatnachrichten_erfolgreich_anzahl`, `chatnachrichten_fehlgeschlagen_anzahl` | Eigene Nutzeranfragen mit Erfolg oder Fehler |
| `suchen_dauer_gesamt_ms`, `neusortierungen_dauer_gesamt_ms`, `chatnachrichten_dauer_gesamt_ms` | Je Operationstyp aufsummierte Laufzeit in Millisekunden |

Eine Chatnachricht kann eine Suche oder Neusortierung auslösen. Sie zählt dann in
beiden Kategorien; die Chatdauer umfasst den gesamten Aufruf einschließlich der
Aktion. **Zeitspalten deshalb nicht zur Gesamtdauer addieren.** Erfolgreiche und
fehlgeschlagene Versuche fließen in die Dauer desselben Typs ein. Vor Beginn der
Operation abgelehnte Eingaben/fehlende Einwilligungen zählen nicht. Ein erneuter
Versuch ist eine neue Operation. Für historische, nicht erfasste Nutzung bleiben
Zähler und Dauern leer; 0 gilt nur im erfassten Zeitraum. Abgeschlossene Antworten
verwenden den eingefrorenen Stand bei Abgabe, Entwürfe den aktuellen Stand. Die
Einzelansicht zeigt die Metadaten schreibgeschützt. Löschung/Widerruf entfernt auch
diese Messwerte.
Die Operationszähler belegen außerdem nicht zuverlässig, ob Suchwünsche im Chat
verändert wurden. Die entsprechende Ja/Nein-Frage bleibt separat bestehen.

### Einzelereignisse ab V12

**Nutzungsereignisse als CSV** lädt `diana_nutzungsereignisse.csv` herunter.
Der Download verwendet dieselben ID-, Versions-, Status-, Gruppen- und Promptfilter
wie der Antwortexport. Eine Zeile ist ein Ereignis, keine Teilnahme; über
`participation_id` mit `teilnahme_id` aus dem Antwortexport verbinden. Der Endpoint
`/api/admin/telemetry-export` verlangt denselben Verwaltungszugang.

Ereignisse sind sichtbare Begründungsintervalle, Aufklappen, Stellendetails und
erfolgreiche Chatdurchgänge. Nicht sichtbare Tabs/Ansichten pausieren die Messung;
fehlende Ereignisse sind kein sicherer Nichtnutzungsnachweis. Überlappende Intervalle
nicht zur Sitzungsdauer addieren. Details, Metadaten und Löschwege:
[STUDY-TELEMETRY.md](STUDY-TELEMETRY.md). Separate Testseiten schreiben keine
Studienereignisse. Historische Zeiträume werden nicht rückwirkend aufgefüllt.

### Teilnahmefluss und vorläufiger V12-Endpunkt

`teilnahmefluss.csv` enthält **ungefilterte** aggregierte Zahlen des aktiven
Studienbestands, unabhängig vom Filter der Einzelantworten. Eine zugeteilte
Einwilligungskennung zählt höchstens einmal. Experiment, ursprüngliche Gruppe,
zugeteilte/abgeschlossene Teilnahmen und Antwortversionen bleiben getrennt.
Widerrufene/gelöschte Fälle fehlen; dies ist ein Bestandsbericht, kein vollständiger
Rekrutierungsverlauf.

`primaerwert_v12_vollstaendig_anzahl` zählt Personen mit **drei numerischen Antworten
1–5** in den neuen Nutzenitems, auch bei insgesamt unvollständiger Umfrage.
Historische gültige V9/V10/V11-Einzelitems haben eigene Zähler. Für die geplante
V12-Auswertung abgeschlossene und unvollständige Antworten gemeinsam exportieren.
Vorgesehen ist vorläufig das Mittel aus genau drei gültigen Items; bei einem
fehlenden Item bleibt der Endpunkt fehlend. Die Verwaltung zeigt Einzelitems und
berechnet diesen Mittelwert nicht automatisch. Das Instrument ist eine angepasste,
noch nicht validierte Operationalisierung.

**`research/analyze_primary.py` unterstützt V12 nicht.** Es bleibt ein Werkzeug
für die historischen V9–V11-Einzelitems. V12-Items nicht in alte Spalten umbenennen
oder 1–5-Werte als 1–10-Werte behandeln. Analyseentscheidung und Stichprobenplanung
vor der Haupterhebung festschreiben: [STUDY-PROTOCOL.md](STUDY-PROTOCOL.md).
Die separate [Relevanzprüfung](research/human_relevance/README.md) bereitet
menschliche Urteile vor; echte aktuelle Urteile und Forschungsergebnisse liegen
dafür noch nicht vor.

### Automatische Herkunft der KI-Persönlichkeit

Diese Metadaten ergänzen die Selbstauskunft, ohne sie zu überschreiben.
`custom` kennzeichnet den tatsächlich angewendeten Selbstgestaltungsweg auch dann,
wenn dessen Werte zufällig einer Vorlage entsprechen. Es beweist nicht, dass
Eigenschaften oder Gewichte inhaltlich verändert wurden. Die weiterhin erhobene
Ja/Nein-Selbstauskunft zur Anpassung ist daher kein identisches Duplikat dieser Daten:

In V11/V12 ist für B regulär `template`/`career` und für C `custom` zu erwarten; der
Fachexperten-Code bleibt ausschließlich für historische Datensätze lesbar.


- `ki_erste_verwendung` / `ki_letzte_verwendung`: `template` (unveränderte Vorlage),
  `custom` (selbst gestaltet oder Vorlage angepasst), `unknown` (unbekannt) oder
  `not_applicable` (in Variante A nicht anwendbar).
- `ki_erste_vorlage` / `ki_letzte_vorlage`: `career` (Top-Berufsberater) oder `expert`
  (Fachexperte), soweit eine unveränderte Vorlage verwendet wurde.
- `ki_jemals_selbst_gestaltet` / `ki_jemals_vorlage`: 1 = im erfassten Zeitraum
  beobachtet, 0 = im vollständig erfassten Zeitraum nicht beobachtet. Bei unbekannten
  Abschnitten bleibt das Feld leer, sofern die Nutzung nicht positiv beobachtet wurde.
- `ki_auswahlwechsel_anzahl`: Übergänge zwischen Herkunft/Vorlage, einschließlich
  unbekannt → bekannt. Wiederholte Verwendung derselben Auswahl zählt nicht erneut;
  einzelne Textbearbeitungen werden nicht gezählt.
- `ki_nutzung_erfassungsversion`, `ki_erstmals_angewendet_am_utc` und
  `ki_auswahl_geaendert_am_utc`: Erfassungsschema und beobachteter Zeitraum.

Gezählt werden tatsächlich angewendete Auswahlen nach erfolgreichem Such-/Chatlauf,
nicht reine Klicks im Editor. Bei abgeschlossenen Umfragen bleibt der Stand bei
Abgabe erhalten; Entwürfe zeigen den aktuellen erfassten Stand. Vor Einführung der
Erfassung gibt es keine rückwirkend erfundenen Daten: `unknown`, Erfassungsversion 0
und leere Zählwerte. Namen, Eigenschaftstexte und Chats werden hier nicht gespeichert.

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
gilt. `teilnahme_status` und `zuletzt_gespeichert_am_utc` sind im Export enthalten; bei unvollständigen
Teilnahmen ist `abgeschlossen_am_utc` leer. Noch nicht beantwortete Pflichtfragen erhalten
`unanswered` in ihrer Statusspalte. Ein späterer Abschluss ersetzt den Entwurf, ohne eine
zweite Teilnahme anzulegen. Löschung über dieselbe Teilnahme-ID entfernt auch Entwürfe.

## Fragebogen V5

Alle subjektiven Bewertungen verwenden 1–10. Neue Antworten stehen in `v5_`-Spalten, historische V4-Werte unverändert in `v4_`-Spalten. Die Frage nach einer eigenen Chatnachricht entfällt in V5. Filter und Codebuch unterscheiden beide Versionen; Werte verschiedener Skalen nicht ungeprüft zusammenfassen.

## Historischer A/B-Gesamtpaketvergleich (V7)

Der aktuelle Vergleich untersucht das gesamte Funktionspaket:

- **A:** neutrales profilbasiertes Suchsystem mit Chat, ohne angezeigte Scores und
  ohne automatische Begründungsboxen an den Stellenkarten. Alle bis zu 20
  zurückgegebenen Stellen werden angezeigt.
- **B:** Suchsystem mit gestaltbarer KI-Suchpersönlichkeit, angezeigten Scores und
  automatischen Begründungsboxen. Zunächst erscheinen Stellen ab 70 Punkten;
  weitere bewertete Stellen lassen sich einblenden.

A bleibt ein funktionierendes, hilfreiches Suchsystem; es erhält keine absichtlich
falschen oder verschlechterten Antworten. Gemessen wird der zusätzliche Nutzen des
Pakets, nicht der isolierte Effekt der Persönlichkeit, der Scores oder der
Begründungen. Auch die anfängliche Sichtbarkeit der Ergebnisliste gehört zum
verglichenen Paket. Gemeinsame Ergebnisfragen erlauben den Gruppenvergleich;
funktionsbezogene Zusatzfragen werden nur B gestellt.

Die Verwaltung zeigt und filtert einheitlich **A** und **B**. CSV/Numiqo-ZIP enthalten
`studiengruppe`, `experiment_id`, `zugeteilt_am_utc`, `vorherige_systemnutzung` und getrennte
`v7_`-Antwortspalten. Zuordnungen dieses historischen Stands verwendeten `experiment_id=diana-ab-v1`.
Vorhandene Zuordnungen bleiben erhalten; eine fortgesetzte Teilnahme kann deshalb
V7-Antworten mit einer älteren Experiment-ID enthalten. `vorherige_systemnutzung` beschreibt
die Situation vor der ursprünglichen Zuordnung und ist kein vollständiger Nachweis
aller früheren Systemnutzungen. Abbrüche stehen unter **Unvollständig**.

## Historische Vergleichserhebung (V6)

Gespeicherte V6-Antworten und die Definition in `survey_definition_v6.json` bleiben
unverändert. Damals hatten **beide** Gruppen Scores und Begründungen. Die historischen
Originalcodes **B** (neutral) und **C** (personalisiert) erscheinen in der Verwaltung
als **A** beziehungsweise **B**; die Speicherung wird dafür nicht umgeschrieben.

Die Metadatenspalte `studiengruppe` verwendet die einheitliche Anzeige A/B. Die eigene
Spalte `v6_studiengruppe_originalcode` bewahrt die ursprüngliche Codierung numerisch: **0 = originales B**,
**1 = originales C**. Bei V7 bedeutet `v7_studiengruppe_originalcode` dagegen **0 = A**, **1 = B**.
`original_codes` im Codebuch dokumentiert diese Zuordnung. Die historische
Experiment-ID bleibt `diana-bc-v1`; historische Antworten erhalten keine nachträglich
erfundene aktuelle Zuordnung.

**V6 und V7 getrennt auswerten.** Gleiche angezeigte Gruppenbuchstaben bedeuten nicht,
dass die getesteten Funktionspakete gleich waren. Fragebogenversion, Experiment-ID
und erfasste Systemstände gemeinsam prüfen; Ergebnisse nicht ungeprüft zusammenfassen.

## Diagramme und Einzelantworten

Unter **Diagramme** zeigt die Verwaltung Häufigkeiten und Prozentwerte je Frage,
bei numerischen Bewertungen (1–5 beziehungsweise 1–10) außerdem Mittelwert, Median und gültige Fallzahl. A/B/C werden
farblich unterschieden; der Kategorienfilter begrenzt die Darstellung. Alle
Tabellenseiten gehen in die Berechnung ein. Die Vorauswahl ist V12/abgeschlossen;
ältere Antworten lassen sich mit dem Fragebogenfilter auswählen.
Fragebogenversionen und Experimentkennungen werden nicht zusammengefasst.
Nicht beurteilbar, nicht genutzt, offene und durch Filterführung übersprungene
Antworten werden gesondert gezählt und nicht als Null in Mittelwerte gerechnet.
Die Aufwandsfrage bleibt in ihrer ursprünglichen Richtung (hoch = mehr Aufwand).
Dies sind deskriptive Statistiken, keine Signifikanzprüfung. Freitexte lassen sich
aufklappen (bis zu 50 je Frage), sämtliche Texte bleiben im Export verfügbar.
**Ansehen** öffnet die Einzelantwort als fokussierten Dialog mit Schließen-Button.

**Alle Teilnahmen löschen** betrifft unabhängig von Filtern alle gespeicherten
Antworten, Entwürfe, Gruppenzuordnungen und verknüpften Suchsitzungen. Ein Dialog
zeigt die Zahlen und verlangt `ALLE TEILNAHMEN LÖSCHEN`. Ändern sich die Daten
zwischen Vorschau und Bestätigung, wird die Löschung abgelehnt und eine neue
Vorschau verlangt. Die Datenbanklöschung erfolgt in einer Transaktion. Bisherige
Einwilligungen werden widerrufen und als gesperrte Kennungen erhalten, damit alte
Sitzungen keine Antworten nachliefern. Die Studie wird dadurch nicht geschlossen;
neue Teilnahmen sind entsprechend dem Freigabestatus möglich. Exporte und Backups
werden nicht automatisch gelöscht.

## Allgemeiner Chat und zufällige Reihenfolge in A

Vom 11. September 2026 bis zur Einführung von V8 verwendeten neue Zuordnungen `diana-ab-v2`. A hat einen
allgemeinen Chat ohne fachliche Beratungsrolle und ohne zusätzliche Antwortlängen-
grenze. Die bis zu 20 Retrieval-Kandidaten werden zufällig angeordnet; derselbe
Pool bleibt bei Antworten und Neubewertung stabil. `darstellungs_versionen` in
CSV und Diagrammkohorten trennt `random-order-generic-chat-v1` von älteren oder
undokumentierten Ständen. Mehrere während einer Teilnahme genutzte Stände bleiben
gesondert erkennbar. Ursprüngliche Gruppenzuordnungen werden nicht verändert.

## Nutzungsverhalten und Betrachtungszeit

Unter **Verwaltung → Nutzungsverhalten** (`/verwaltung#nutzungsverhalten`) stehen
Kennzahlen und ein deskriptiver A/B/C-Vergleich. Eine aufklappbare Teilnahme zeigt
pro Stellen-ID die sichtbare Begründungszeit in Sekunden, geöffnete Details,
aufgeklappte Begründungen und beobachtete Rangpositionen. Chatnachrichten kommen
vom selben erfolgreichen Server-Zähler wie das Drei-Nachrichten-Limit.

Die oben gewählte Auswahl **Nur abgeschlossene / alle / nur unvollständige** gilt
auch für diese Ansicht und ihre Downloads. Fehlende Messungen erscheinen als
„Nicht erfasst“, nicht als Nullwert. Eine gemessene sichtbare Begründungsdauer
belegt keine Aufmerksamkeit. Mehrere zugleich sichtbare Karten können sich
zeitlich überschneiden; ihre Summe ist keine gesamte Sitzungsdauer.

- **Nutzungsverhalten pro Teilnahme:** Bereits zusammengefasste CSV, eine Zeile je
  Teilnahme, Sekunden statt Millisekunden. Über `teilnahme_id` mit dem deutschen
  Antwortexport verknüpfen. Leer bedeutet nicht erfasst.
- **Nutzungsereignisse als CSV:** Rohereignisse mit UTC-Zeitpunkt, Stellenkennung,
  Rang und `duration_ms`; über `participation_id` verknüpfen. Für eigene
  Aggregationen und die Prüfung einzelner Ereignisse.

Die APIs `/api/admin/usage-analytics` und `/api/admin/usage-export` benötigen den
bestehenden Verwaltungslogin. Starts ohne gespeicherten Antwortentwurf erscheinen
nicht in der Antwortauswahl. Der Rohdownload enthält keine Chat- oder Profiltexte.

**Alle Teilnahmen löschen** entfernt auch Nutzungsereignisse, Korrekturverläufe
und offene Chatreservierungen. Gesperrte Einwilligungskennungen verhindern, dass
alte Browserstände die gelöschten Antworten erneut übertragen. Exporte und
Datenbanksicherungen müssen zusätzlich bereinigt werden.
