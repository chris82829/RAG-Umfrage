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

Der aktuelle Fragebogen ist ausschließlich **`diana-v14`**, Experiment **`diana-abc-v7`**.
Die Verwaltung bietet keine Auswahl früherer Fragebögen. Auch die Antwort-CSV und
das Codebuch enthalten nur die neuen Fragefelder; alte Antworten werden nicht
migriert. Einträge alter Browserfassungen werden beim Schreiben zurückgewiesen.

| Exportspalte | Bedeutung |
| --- | --- |
| `teilnahme_id` | Verbindung zwischen Antworten und Nutzungsereignissen |
| `teilnahme_status` | `completed` oder `in_progress` |
| `studiengruppe` | A, B oder C |
| `v14_nutzen_passende_stelle` | Nutzenitem zur idealen Stelle |
| `v14_nutzen_einfacher_finden` | Nutzenitem zum einfachen Finden |
| `v14_nutzen_vorschlaege` | Nutzenitem zu guten Vorschlägen |
| `v14_nutzen_mittelwert` | Mittel aus genau drei gültigen Nutzenitems |
| `v14_kontrolle_mittelwert` | Mittel aus genau drei gültigen Suchkontrollitems |
| `v14_transparenz_mittelwert` | Mittel aus genau drei gültigen Transparenzitems |
| `v14_vertrauen_mittelwert` | Mittel aus beiden gültigen Vertrauensitems |
| `v14_manipulationscheck_beratungscharakter` | Wahrgenommener Charakter, eigenes Einzelitem |
| `v14_fruehere_teilnahme_selbstauskunft` | Ja/Nein/Unsicher zur früheren Studienteilnahme |
| `v14_zusatz_suchaufwand` | Gesamter subjektiver Nutzungsaufwand; hoch = mehr Aufwand |
| `v14_zusatz_beratungsstil_steuerbarkeit` | Wahrgenommene Gestaltbarkeit des Sprachstils |

Alle Bewertungen verwenden **1–7**. „Kann ich nicht beurteilen“ bleibt leer und
wird durch die zugehörige `_antwortstatus`-Spalte erklärt. Mittelwerte werden nur
bei vollständigen numerischen Antworten berechnet: Nutzen/Kontrolle/Transparenz je drei, Vertrauen beide Items. Niemals aus weniger Items. Die drei Dialogeinzelitems bilden keine gemeinsame Skala; es gibt keinen
Gesamtscore über den Fragebogen. Das Codebuch kennzeichnet Framework, Konstrukt,
Fundstelle, DOI, Anpassung, Wertebereich, Antwortcodes und Richtung. Hoher Aufwand
wird nicht automatisch umgepolt. Die rechnerischen Konstruktmittelwerte sind keine
Bestätigung psychometrischer Validität.

A/B sehen 26 Fragen, C 27, inklusive freiwilliger Fachrichtung und Feedback.
Gemeinsame Fragen sind in allen Gruppen identisch. Nur die Selbstauskunft zur
Veränderung der Beratungseinstellungen erscheint in C. Alter und Geschlecht
werden nicht erhoben. Die Zuordnung bleibt A/B/C, auch wenn C nichts verändert.
[Fragenkatalog und Quellen](QUESTIONNAIRE.md), [Auswertungsplan](STUDY-PROTOCOL.md).

Die technischen Spaltennamen sind mit `columns=technical` verfügbar; Standard
ist `columns=readable`. Beide Exporte enthalten dieselben Werte. Die
`spaltenzuordnung.csv` liefert die genaue Zuordnung der Namen. CSV nutzt UTF-8/BOM
und Semikolon. Formelähnlicher Freitext wird beim Export mit Apostroph abgesichert.

`survey_migrations.py` ergänzt generierte INTEGER-Spalten für die neuen
V14-Bewertungen aus dem Antwort-JSON. Der Bereich 1–7 wird geprüft; fehlende oder
nicht beurteilbare Werte bleiben NULL. Wiederholter Start ist möglich; die
Migration selbst ist keine Datenlöschung. Beim Wechsel zu V14 bleiben vorhandene historische Antworten und Entwürfe getrennt erhalten.

### Aggregierte Nutzung und Laufzeiten

Seit V9 werden abgeschlossene Serveroperationen als Summen erfasst. Für diese Summen werden keine Rohtexte, IP-Adressen oder Gerätekennungen gespeichert.
V12 ergänzt davon getrennte Interaktionsereignisse, wie unten beschrieben.

| Spalten | Bedeutung |
| --- | --- |
| `nutzung_erfassungsversion` | 0 = nicht erfasst; 1 = historische Summen; 2 = Summen plus separate Operationsdiagnostik |
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
Die Operationszähler belegen nicht zuverlässig, ob Suchwünsche inhaltlich geändert wurden; solche Änderungen nicht allein aus der Nachrichtenanzahl ableiten.

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

### Teilnahmefluss und Konstrukte in V14

`teilnahmefluss.csv` enthält ungefilterte aggregierte Zahlen des aktiven V14-
Studienbestands. Zuordnungen, Abschlüsse und vollständige Nutzen-, Kontroll- und
Transparenzwerte bleiben getrennt. Das ist ein Bestandsbericht, kein vollständiger
Rekrutierungsverlauf nach Löschungen/Widerrufen.

Für den geplanten primären C–B-Vergleich auch unvollständige Teilnahmen mit drei
vollständigen Nutzenantworten exportieren. Der Statusfilter gilt für Diagramme,
Einzelantworten und die Antwort-/Nutzungsdownloads. Fehlende Antworten bleiben
fehlend; keine Daten anderer Fragebogenversionen hinzunehmen.

`research/analyze_primary.py` ist ein historisches Werkzeug, kein V14-Analysetool.
Der neue Export liefert alle Einzelitems und die drei vollständigen Skalenmittel.
Pretest, psychometrische Prüfung, Fallzahl und inferenzstatistischer Analyseplan
sind vor der Haupterhebung festzulegen; siehe [STUDY-PROTOCOL.md](STUDY-PROTOCOL.md).

### Automatische Herkunft der KI-Persönlichkeit

Diese Metadaten ergänzen die Selbstauskunft, ohne sie zu überschreiben.
`custom` kennzeichnet den tatsächlich angewendeten Selbstgestaltungsweg auch dann,
wenn dessen Werte zufällig einer Vorlage entsprechen. Es beweist nicht, dass
Eigenschaften oder Gewichte inhaltlich verändert wurden. Die weiterhin erhobene
Ja/Nein-Selbstauskunft zur Anpassung ist daher kein identisches Duplikat dieser Daten:

In V14 ist für B regulär `template`/`career` und für C `custom` zu erwarten; der
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

## Diagramme und Einzelantworten

Unter **Diagramme** zeigt die Verwaltung Häufigkeiten und Prozentwerte je Frage,
bei den Bewertungen 1–7 außerdem Mittelwert, Median und gültige Fallzahl. A/B/C werden
farblich unterschieden; der Kategorienfilter begrenzt die Darstellung. Alle
Tabellenseiten gehen in die Berechnung ein. Die Vorauswahl ist V14/abgeschlossen. Es gibt keinen Fragebogenfilter.
Nutzen, Suchkontrolle und Transparenz zeigen zusätzlich getrennte Mittelwerte aus jeweils drei gültigen Items.
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

## V14: Studienmetadaten und Analyseplan

Unter **Studienphase und Rekrutierung** wird die Zuordnung neuer Einwilligungen eingestellt: Pretest (Standard) oder Hauptstudie samt Versandzeitpunkt. Bereits begonnene Teilnahmen werden nicht rückwirkend umklassifiziert. Diagramme und Downloads lassen sich nach dieser Phase filtern.

Unter **Nutzungsverhalten** stehen zusätzlich die weitesten Studienschritte, initiale/letzte Mobil- oder Desktopansicht, standardisierte Fehlercodes und -phasen sowie die protokollierten Gewichtsvektoren je Bewertung. Die Metadatenübersicht enthält auch Teilnahmen ohne gespeicherte Antworten. Sie berücksichtigt Version, Gruppe und Phase; Antwortstatus-, Suchtext- und Promptfilter würden frühe Abbrüche ausschließen und werden in diesem Bereich ausdrücklich nicht angewandt. Ein nicht abgeschlossener Ablauf ist nicht automatisch ein endgültiger Abbruch.

**Studienmetadaten herunterladen** liefert ZIP mit Kontextübersicht, `scoring_calls.csv` und `operation_events.csv`. Der allgemeine Auswertungs-ZIP enthält außerdem `analysis_input.csv` (technische Spalten), Kontext aller Einwilligungen der gewählten Phase und die Operations-/Scoringereignisse der ausgewählten Antwortteilnahmen. Die jeweiligen Denominator/Filter sind angegeben. T1/T2/M1 werden als Rohwerte mit Antwortstatus und eindeutigen deutschen Spalten exportiert. Das Vertrauensmittel benötigt beide gültigen Items, die übrigen Konstrukte je drei.

**Studienanalyse** wird nur auf ausdrücklichen Klick berechnet. Hier gilt der vorab beschriebene Analyseumfang, unabhängig von den Beschreibungsfiltern: V14, `study_wave=main`, je Endpunkt vollständige Itemgruppe, auch aus später abgebrochenen Fragebögen. Neben Welch und Holm zeigt die Analyse Hedges g/95%-Intervalle, Cronbachs Alpha, den Manipulationscheck und Sensitivitäten zu Wiederholungsangaben. Bereinigte technische Ausfälle werden nicht aus beliebigen früheren Timeouts erraten; ein begründeter Ausschluss wird in einer separaten Analysearbeitskopie dokumentiert.

Der Planstatus bleibt Entwurf, solange SESOI, Ausfallreserve und festes Rekrutierungsfenster nicht vor der Hauptstudie festgelegt und versioniert sind. Keine Rekrutierungsstopps aufgrund laufender p-Werte. Der Quellcode `research/v14/analyze.py` erzeugt denselben Bericht offline aus dem technischen CSV; `research/v14/faithfulness.py` unterstützt die getrennte, tatsächlich von zwei Menschen vorzunehmende Belegtreueprüfung.
