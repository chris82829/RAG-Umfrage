# DIANA Jobsuche – React-Webseite und hybrides Job-Matching

Flask-Prototyp mit Anzeigen aus dem bereitgestellten Export,
SQLite-Vorfilter, paralleler BM25-/E5-Suche,
Reciprocal Rank Fusion und GPT-5.4-Reranking mit begründeten Ergebnissen.
Die React-Webseite enthält ein Suchprofil, Jobkarten und einen persistenten Chat.
Im aktuellen Konferenzstand V9 zeigen **alle drei Varianten A/B/C** Scores von
**1 bis 100**, kurze Begründungen und eine nach Score sortierte Ergebnisliste.
Zunächst sind Stellen ab 70 Punkten sichtbar; weitere lassen sich einblenden.
Die Varianten unterscheiden sich im Beratungsangebot: feste Standardberatung,
Vorlagenauswahl oder zusätzliche eigene Gestaltung. Die produktive Konfiguration
verwendet den separat importierten Stellenbestand; dessen Umfang zeigt das System an.

## Aktueller Studienvergleich: A/B/C, Fragebogen V9

Neue Teilnahmen werden serverseitig mit gleicher Wahrscheinlichkeit zufällig A, B oder C zugeteilt. Die Zuordnung bleibt beim Neuladen erhalten. Das Experiment heißt **`diana-abc-v2`**, der Fragebogen **`diana-v9`**.

- **A:** feste sachliche Standardberatung zur Jobsuche ohne wählbare Persönlichkeit; dieselbe Bewertung, Sortierung, Scores und Begründungsboxen wie B/C.
- **B:** Auswahl zwischen **Top-Berufsberater** und **Fachexperte** mit festen Eigenschaften. Persönliche Rangfolge, Scores und Begründungen; zunächst Stellen ab 70 Punkten, weitere per Button.
- **C:** dieselben Vorlagen und dieselbe Bewertungs-/Darstellungslogik wie B, zusätzlich **Selbst personalisieren** mit Name, Eigenschaften, Bewertungsschwerpunkt und Freitext.

B und C starten mit dem Top-Berufsberater. Einschränkungen in B werden serverseitig geprüft. Der Vergleich B/C untersucht das zusätzliche Angebot freier Gestaltung; alle zufällig C zugeteilten Teilnahmen gehören zu C, auch bei unveränderter Vorlagennutzung. B/A vergleicht das Angebot einer Vorlagenauswahl mit der festen Standardberatung. Untersucht wird kein Chatbot gegen eine reine Stichwortsuche. Die faire Ergebnisdarstellung und das Modell sind in A/B/C gleich. Einordnung: [CONFERENCE-FIT.md](CONFERENCE-FIT.md).

Der vorherige A/B/C-Stand ist auf Branch `sicherung-abc-vor-konferenz-2026-09-14` gesichert; seine `diana-abc-v1`-Teilnahmen bleiben bei V8 und den damaligen Bedingungen. Vorherige `diana-ab-*`-Teilnahmen behalten ihr gestaltbares B und ihren historischen Fragebogen. Sie werden nicht in die neue Vorlagen-B-Gruppe umgedeutet. V6 mit ursprünglichen B/C-Codes bleibt ebenfalls separat erhalten. Version und Experimentkennung gemeinsam auswerten; Details: [ADMIN.md](ADMIN.md).

### Varianten unabhängig von der Umfrage testen

- [/test/a](http://ifaiforschung.informatik.fh-nuernberg.de:5051/test/a) – feste Standardberatung
- [/test/b](http://ifaiforschung.informatik.fh-nuernberg.de:5051/test/b) – feste Beratungsvorlagen
- [/test/c](http://ifaiforschung.informatik.fh-nuernberg.de:5051/test/c) – Vorlagen und eigene Gestaltung

Diese Zugänge haben getrennte Einwilligungen und Sitzungen. Sie erzeugen keine Umfrageantworten, keine zufällige Studienzuordnung und keine Nutzungsmetadaten für die Studie. Vorlagenauswahl und tatsächlich angewendete eigene Gestaltung werden dagegen bei regulären Studienteilnahmen separat von der Selbstauskunft dokumentiert. Der Export verwendet verständliche deutsche Spalten mit Codebuch und technischer Spaltenzuordnung.

## Datenschutz und Studienfreigabe

Das System unterstützt Einwilligung, Teilnahme-ID und gezielten Widerruf.
Der tatsächliche Freigabestatus wird durch die Serverkonfiguration und den
Schalter zur Studienfreigabe in **`/verwaltung`** bestimmt. Eine lokale
Beispielkonfiguration sagt nicht aus, ob die Serverinstanz freigegeben ist.
Verantwortlichkeit, Datenschutzhinweise und Löschabläufe stehen in
[PRIVACY.md](PRIVACY.md). Die technische Freigabe ist keine rechtliche oder
institutionelle Bestätigung.

Vollständige Einzelantworten sollen auch nach der Promotion für die beschriebenen
Forschungszwecke nutzbar bleiben; ihre Erforderlichkeit wird mindestens jährlich
geprüft. Ein Widerruf anhand der Teilnahme-ID umfasst die verknüpften Daten.
Suchprofil und Chatverlauf werden für neue Sitzungen nur vorübergehend im
Arbeitsspeicher gehalten. Die Studie speichert zusätzlich die dokumentierten
Auswahl- und Betriebsmetadaten, ohne daraus Such- oder Chattexte abzulegen.

## Webseite ausprobieren

### Aktueller Ablauf: V9 mit eingebetteter Jobsuche

Der Einstieg ist die **[Vorstellungsseite](http://127.0.0.1:5050/)** mit
Forschungsprojekt, Foto und Kontaktdaten. **„Umfrage starten“** führt zu `/umfrage`.
Nach der Einwilligung und serverseitigen Zuordnung läuft die Teilnahme so ab:

1. **Kurze Vorbereitung:** Vor dem eingebetteten System werden die Nutzung von
   Jobportalen und KI-Chats in den letzten sechs Monaten abgefragt. Es gibt
   abgegrenzte Häufigkeitskategorien und „Keine Angabe“. Alle Gruppen sehen dieselbe
   Aufgabe: ein realistisches Suchprofil erstellen, Stellen und Begründungen ansehen
   und mindestens eine eigene inhaltliche Frage im Chat stellen. Die Antworten
   werden vor **„System ausprobieren“** gespeichert. Eigene Gestaltung in C ist freiwillig.
2. **DIANA nutzen:** A verwendet die feste Standardberatung. B wählt aus den beiden
   festen Vorlagen; C kann dieselben Vorlagen nutzen oder zusätzlich selbst gestalten.
   Während einer Suche können im Wartezeit-Dialog demografische Angaben und das
   Suchvorhaben beantwortet werden. **Keine Bewertungen der Einrichtung, Suche
   oder des Chats werden während der Wartezeit erhoben.**
3. **Ergebnisse besprechen:** Alle Gruppen sehen Scores, Begründungen und dieselbe
   Anzeigelogik. **„Weitere Fragen für die Umfrage beantworten“** erscheint nur bei
   sichtbarer Ergebnis-/Chatansicht, nicht während einer Suche oder eines Dialogs.
   Weitergehen setzt mindestens eine erfolgreich beantwortete eigene Chatnachricht
   voraus. Die automatische Begrüßung zählt nicht; andernfalls führt ein Hinweis zum Chat.
4. **Rückmeldung geben:** Gemeinsame Kategorien sind **Suchvorhaben**,
   **Deine Erfahrung mit der Suche**, **Suchen im Gespräch**, **Score und Begründungen**
   und **Feedback**. B und C erhalten außerdem passende Fragen zu Auswahl bzw.
   Gestaltung und Wirkung ihrer KI-Suchpersönlichkeit. Gemeinsame Ergebnisfragen
   stehen vor bedingungsspezifischen Fragen. Bereits beantwortete Vorabfragen werden
   übersprungen; fehlende demografische Angaben können nachgeholt werden.
5. **Abschließen:** Antworten werden nach jeder Eingabe automatisch gespeichert,
   bei Texteingaben kurz gebündelt. Der Abschluss validiert den vollständigen
   Fragebogen. Die Teilnahme-ID dient unter anderem späteren Löschanfragen.

V9 verwendet 1–10 für graduelle Erfahrungen, Ja/Nein für passende Nutzungsfragen
und Freitext für das Suchvorhaben sowie optionales Feedback. „Nicht genutzt“,
„Kann ich nicht beurteilen“ und „Keine Angabe“ sind eigenständige fehlende Angaben,
keine niedrigen Bewertungen. Die Frage nach tatsächlicher Selbstgestaltung erscheint
nur in C; sie bleibt von der automatisch erfassten Nutzung getrennt.
Fragetexte, Bedingungen und Antwortwerte stehen in `survey_definition_v9.json`.

Das Suchvorhaben wird aus dem abgeschickten DIANA-Suchprofil als bearbeitbarer
Vorschlag übernommen. Eigene Änderungen, auch ein bewusst geleertes Feld,
werden nicht durch spätere Suchen überschrieben. Demografische Angaben und
Vorerfahrung verändern das Matching nicht und werden nicht an das LLM gesendet.
Bewertet wird der Suchprozess und das Beratungsangebot, nicht die Qualität
oder Passung der gefundenen Stellen.

Die eingebettete Jobsuche bleibt beim Wechsel zum Fragebogen erhalten. Ein
separater Sitzungsschlüssel trennt sie von normalen DIANA- und Test-Sitzungen.
Der Browserentwurf bleibt im selben Tab über `sessionStorage` beim Neuladen erhalten;
Serverbestätigungen sichern die gespeicherten Antworten zusätzlich. Auf dem Handy
werden Skalenwerte in zwei Reihen mit fünf Auswahlflächen dargestellt; die
Systemansicht berücksichtigt dynamische Bildschirmhöhe und den sicheren unteren Bereich.

### Speicherung und Auswertung

`PUT /api/survey-drafts` speichert den Antwortentwurf mit monotoner Revision.
`POST /api/survey-responses` validiert ihn beim Abschluss und übernimmt ihn in
`survey_responses`. Neue Teilnahmen verwenden `diana-v9` und `diana-abc-v2`;
fortgesetzte historische Teilnahmen behalten ihren zugewiesenen Stand.
Wiederholtes Absenden derselben Antworten erzeugt keinen zusätzlichen Datensatz.
Die Teilnahme-ID ist keine Identitätsprüfung und verhindert nicht jede
Mehrfachteilnahme in unterschiedlichen Browsern.

Unter **[/verwaltung](http://127.0.0.1:5050/verwaltung)** stehen Einzelantworten,
Korrekturen mit Änderungsverlauf, Filter, Löschung, Diagramme und der
**CSV-Export für Numiqo** bereit. Das Auswertungspaket enthält Codebuch,
Spaltenzuordnung sowie Modell-/Konfigurationsnachweise. Details: [ADMIN.md](ADMIN.md).

Für die geplante Primäranalyse **abgeschlossene und unvollständige Teilnahmen
zusammen exportieren**: Alle gültigen V9-Primärantworten der neuen Kohorte zählen
nach Zuteilung, auch bei unveränderter Vorlagennutzung in C. Der Primärvergleich
ist C minus B beim Einzelitem `system_usefulness` / `v9_system_nutzen`.
Protokoll: [STUDY-PROTOCOL.md](STUDY-PROTOCOL.md).
Offline-Skripte und Aufrufe: [research/README.md](research/README.md).

Der zusätzliche lesbare CLI-Export enthält ausschließlich abgeschlossene Antworten:

```bash
.venv/bin/flask --app app:create_app survey-export --output instance/umfrage.csv
```

CSV-Dateien verwenden UTF-8 mit BOM und Semikolon. Bestehende Exportdateien werden
nicht überschrieben. Freitext wird gegen die Interpretation als Tabellenformel
abgesichert. Forschungsdaten und Exporte unter `instance/` gehören nicht ins Git-Repository.

### Historische Fragebögen und Bedingungen

Diese Angaben beschreiben frühere Studienstände, **nicht den aktuellen V9-Ablauf**:

- **V8 / `diana-abc-v1`:** A war die allgemeine Basisvariante ohne angezeigte Scores
  oder Begründungsboxen und mit zufälliger Ergebnisreihenfolge. B bot feste Vorlagen,
  C zusätzlich eigene Gestaltung. Scores und Begründungen wurden nur B/C abgefragt;
  Einrichtungsfragen konnten schon während der Wartezeit beantwortet werden.
- **V7 / `diana-ab-*`:** A war die allgemeine Basisvariante, B die frei gestaltbare
  KI-Beratung. Fragen zu Persönlichkeit, Scores und Begründungen wurden in A
  übersprungen. V7 liegt unverändert in `survey_definition.json`.
- **V6 / `diana-bc-v1`:** Ursprüngliche Gruppenbezeichnungen B/C bleiben in den
  Originalantworten und im Codebuch dokumentiert. Die Verwaltung stellt sie für den
  historischen Vergleich als A/B dar; sie dürfen nicht mit neuem B/C vermischt werden.

Unvollständige V6/V7/V8-Teilnahmen werden mit ihrem historischen Fragebogen und
ihren Bedingungen fortgesetzt. Auch bereits in V7 fortgesetzte ältere B/C-Teilnahmen
bleiben bei diesem Stand. Abgeschlossene historische Antworten werden nicht
umgeschrieben. Sehr alte V2/V3-Entwürfe übertragen lediglich persönliche Fakten und
Suchvorhaben in einen neuen Durchlauf; Bewertungen werden nicht in neue Antworten umgedeutet.

V4 bis V9 erhalten getrennte versionsbezogene Exportspalten. Experimentkennung
und Fragebogenversion müssen gemeinsam ausgewertet werden. Begleitende
`_antwortstatus`-Spalten (technisch `_status`) unterscheiden beantwortet, fehlend,
übersprungen und nicht gestellte Fragen. Ja=1 und Nein=0 sind gültige Antworten;
fehlende Zahlen bleiben leer. Historische Fragebogen-Dateien werden unverändert erhalten.

### Frisch von GitHub starten

Voraussetzungen: Python 3.12, eine aktuelle Node.js-Version und pnpm.

```bash
git clone https://github.com/chris82829/RAG-Umfrage.git
cd RAG-Umfrage
python3.12 -m venv .venv
.venv/bin/python -m pip install -r requirements-dev.txt
cp .env.example .env
pnpm install --frozen-lockfile
pnpm build
```

Danach den eigenen `OPENAI_API_KEY` in der lokalen `.env` eintragen und mit
`.venv/bin/python app.py` starten. Die Beispielkonfiguration verwendet fünf
fiktive Stellen; der vollständige Stellenexport wird separat importiert
(siehe „Originaldatei importieren“). Datenbank, Nutzerprofile, Chatverläufe,
API-Schlüssel, Modell-Caches und der erzeugte Frontend-Build sind nicht Bestandteil
des Git-Repositories. `pnpm build` erzeugt den für Flask benötigten Frontend-Build.

### Auf diesem Mac

Öffne die **[DIANA-Startseite](http://127.0.0.1:5050/)**: Sie stellt das
Forschungsprojekt und Christoph Scharnagl mit Foto und Kontaktdaten vor.
„Umfrage starten“ führt zur **[Umfrage](http://127.0.0.1:5050/umfrage)**.
Die eigenständige **[Jobsuche](http://127.0.0.1:5050/suche)** bleibt direkt erreichbar.
Die Startseite ist auch unter `/index.html` erreichbar. Wenn der Server bereits läuft,
musst du keinen weiteren starten. „Port 5050 is in use“ heißt in diesem Fall, dass
der vorhandene Server den Port schon belegt.

Wenn die lokale `.venv` eingerichtet ist, starte mit `.venv/bin/python app.py`.
Andernfalls richte sie mit den oben beschriebenen Schritten ein.

#### Historische Bedienungsnotizen vor dem Konferenzumbau

Die folgenden ausführlichen UI-Notizen dokumentieren frühere Entwicklungsschritte.
Insbesondere bekannte Personen als Vorlagen, mobile Schrittleisten und Aussagen
zur eingeschränkten Ergebnisdarstellung in A gelten nicht für V9. Für die aktuelle
Gruppenführung und Reihenfolge gilt der oben beschriebene V9-Ablauf.

Vor der ersten Suche zeigt die linke Seite vier farbige, nummerierte Karten mit
Icons: **Profil erstellen**, **Persönlichkeit festlegen**, **Ergebnisse ansehen**
und **Besprechen & verfeinern**. Alle Karten haben dieselbe helle Hintergrundfarbe;
Icons, Rahmen und Statusmarkierungen behalten ihre Farben. Der aktuelle Schritt und der zugehörige Bereich
sind farbig hervorgehoben. Erledigte Schritte erhalten ein grünes Häkchen mit
„Erledigt“, ohne zusätzliche Umrandung. Beim Zurückgehen bleibt das Häkchen neben
„Aktuell“ erhalten.
Die Schrittkarten erlauben nur den aktuellen Schritt oder einen Rücksprung.
Weiter geht es über die jeweiligen Formular- und Aktionsbuttons. Erst wenn die
erste Suche abgeschlossen ist und die Ergebnisansicht die Anleitung ersetzt,
zeigt die oberste Kopfzeile die vier Schritte ausschließlich mit Icons und Nummern;
der aktuelle Schritt bleibt farbig markiert, erledigte Schritte tragen ein grünes
Häkchen. Die zusätzliche breite Schrittleiste entfällt. Auf dem Handy stehen die
vier kompakten Schaltflächen ebenfalls in einer Zeile. Vollständige Schrittnamen
bleiben als zugängliche Beschriftung und am Desktop als Tooltip verfügbar.
Die Kopfzeile ordnet das DIANA-Logo links, die Schrittanzeige mittig und die
Stellenanzahl rechts an. Der zusätzliche „Mehr erfahren“-Button und der
„DU“-Profilkreis sind entfernt. Auf schmalen Bildschirmen rücken Logo und Schritte
platzsparend zusammen; die Stellenanzahl entfällt dort bei knappem Platz.
Während der Profilerstellung, Persönlichkeitsauswahl und ersten laufenden Suche
bleibt diese kleine Anzeige ausgeblendet. „Neu starten“ blendet sie wieder aus;
eine wiederhergestellte Suche zeigt sie sofort, auch bei ausgeblendeten Ergebnissen.
Unbewertete Anzeigen werden vor der ersten Suche nicht angezeigt.

Rechts steht zunächst ausschließlich der große blaue Button **„Jetzt Profil erstellen“**
mit dem Hinweis „Hier klicken und loslegen“ und einem Pfeil. Erst dieser Button öffnet
die Profilerstellung. Auf dem Handy steht er unter der Anleitung; nach dem Klick
erscheint das Formular. Bereits gespeicherte Sitzungen öffnen weiterhin ihre
Ergebnisse und ihren Chat. „Neu starten“ im rechten Bereich führt zum Startbutton
zurück und behält die Profilangaben für den nächsten Einstieg.

Die rechte Seite beginnt nach dem Start mit dem Formular. Der zusätzliche
DIANA-Kopf mit Kompass und Slogan ist entfernt. Auch die Hinweiszeilen
„Hier bearbeitest du dein Profil“, „Hier wählst du deine Persönlichkeit“ und
„Hier besprichst und verfeinerst du deine Suche“ entfallen. Laufende Statusmeldungen
zur Suche und Bewertung bleiben sichtbar.
Die zusätzliche rechte Tab-Leiste „Suchprofil“, „Persönlichkeit“ und „Besprechen“
ist entfernt. Profil und Persönlichkeit bleiben nach der Suche über die Icons
in der obersten Kopfzeile erreichbar. Das Filter-Popup bietet zusätzlich
den Profilzugang. Beim Wechsel bleiben ungespeicherte
Formularangaben und der Chatentwurf erhalten. Während laufender Anfragen ist der
Bereichswechsel gesperrt; reine Navigation startet keine Suche oder KI-Anfrage.

Neben der Ergebnisüberschrift öffnet der kompakte **Filter-Button** die gespeicherte
Übersicht als Popup: am Desktop beim Darüberfahren, per Klick oder auf dem Handy
per Antippen. Enter und Leertaste öffnen es ebenfalls; Escape, der Schließen-Button
oder ein Klick außerhalb schließen es. Stellenart und Wünsche für die KI-Bewertung
bleiben getrennt, alle ausgewählten Stellenarten werden als „Alle Stellenarten“
zusammengefasst. Lange Angaben scrollen innerhalb des Popups. **„Suchprofil bearbeiten“**
führt direkt zum Formular und erhält bestehende Entwürfe. Die bisherige breite
Chip-Übersicht über den Stellen entfällt.

Die beiden Aktionen **Jobs neu sortieren** und **Neu starten** stehen rechts unter
**„Aktionen“** nebeneinander. Der Schalter und der kurze Ergebnisstatus teilen
sich eine einzelne, 44 Pixel hohe Zeile. Der Bereich startet eingeklappt; die
separate Statusleiste entfällt. Lange Statusangaben werden bei Platzmangel mit
einer Ellipse gekürzt und bleiben als zugänglicher Text und Tooltip vollständig
vorhanden. Die zusätzlichen Buttons „Suchprofil“ und
„Besprechen & verfeinern“ entfallen dort. Dieser Bereich ist zunächst eingeklappt und lässt sich
per Klick, Enter oder Leertaste öffnen und schließen. Beim Bereichswechsel bleibt
die gewählte Klappansicht erhalten; eine neue
Sitzung oder ein Neuladen beginnt wieder eingeklappt. Auch der Hinweis auf eine
notwendige neue Suche steht dort. Der
zusätzliche Sortierbutton unter dem Chatfeld entfällt. In der mobilen
Ergebnisansicht öffnet **„Profil & Chat öffnen“** unten rechts den Chatbereich;
der Button überlagert keine Stellenkarte. Die Schrittanzeige erlaubt weiterhin
nur den aktuellen Schritt oder einen Rücksprung.

Bei einer vollständigen Suche öffnet sich ein **Lade-Popup** mit animierten
Stellenkarten und einer laufenden Lichtspur. Der Hinweis lautet: „Deine Stellen
werden gesucht und persönlich bewertet. Das kann bis zu zwei Minuten dauern.“ Es gibt
keinen Sekundenzähler und keinen Hintergrund-Button. Der Dialog bleibt bis zum
Erfolg oder Fehler offen; Escape blendet ihn nicht aus. Bei reduzierter Bewegung
bleibt die Animation statisch.

Das Popup erscheint erst nach dem echten Suchsignal des Backends, auch bei einer
automatisch im Chat ausgelösten neuen Suche. Antworten, Neubewertung der vorhandenen
Kandidaten, abgewiesene Suchaufträge oder noch nicht verfügbare Indizes öffnen es
nicht. Es gibt keine zusätzliche KI-Anfrage und keine künstliche Mindestwartezeit.

Die erste Chatnachricht begrüßt den Nutzer, nennt die tatsächliche Anzahl der
bewerteten Ergebnisse und verweist auf die Ergebnisübersicht links sowie mögliche
Rückfragen. In B unterscheidet sie zwischen gefundenen und zunächst sichtbaren
Stellen ab 70 Punkten; bei ausgeblendeten Treffern nennt sie die Einblendoption.
In A verweist sie auf alle zurückgegebenen Stellen ohne Score oder Schwellenhinweis.
Die Zahlen werden aus den fertigen Karten berechnet. Die persönliche KI-Erklärung
bleibt darunter erhalten. Die Begrüßung wird einmal mit der neuen Sitzung gespeichert,
ohne zusätzliche KI-Anfrage; spätere Antworten und bestehende Verläufe bleiben erhalten.

Chatnachrichten stehen in abgerundeten Sprechblasen: KI links in hellem Grau,
eigene Nachrichten rechts in hellem Blau. Die Score-Zeile über der Ergebnisliste
entfällt; die Persönlichkeits-Scores bleiben an den einzelnen Stellenkarten.

**Echtes Chat-Streaming:** Die Responses-API liefert den Text bereits während der
Generierung. Das Backend liest ausschließlich das Feld `assistant_message` aus
validierten Zwischenständen der strukturierten Antwort und sendet `assistant_text`
als NDJSON-Snapshot. Das Frontend ersetzt damit die vorläufige Sprechblase.
Die fertige, erneut geprüfte Antwort wird genau einmal gespeichert. Bei Abbruch,
ungültiger Antwort oder Sitzungskonflikt bleibt der bisherige Zustand erhalten;
ein fehlgeschlagener Stream wird nicht automatisch erneut angefragt.

Die automatische Entscheidung zwischen Antwort, neuer Suche und Nachsortierung
bleibt erhalten. Vorläufige Planungsantworten werden nur bei unveränderten
Ergebnissen angezeigt; bei einer Neubewertung kommt der Text aus dem Reranking.
Modell **GPT-5.4**, bisheriger Denkaufwand und alle Begründungen für bis zu
20 Stellen bleiben unverändert. Streaming überbrückt die Textausgabe; die
Denkphase und vollständige Suche werden dadurch nicht verkürzt.
JSON-Clients ohne explizite NDJSON-Anforderung erhalten weiterhin die vollständige
Antwort. Grundlage: [OpenAI Structured Outputs mit Streaming](https://developers.openai.com/api/docs/guides/structured-outputs).


1. **Schritt 1 – Dein Profil:** „Beispielprofil“ neben „Was passt zu dir?“ wählen oder
   eigene Angaben eintragen, dann „Weiter zur Persönlichkeit“.
2. **Schritt 2 – Persönlichkeit:** Nach einer kurzen Erklärung mit Grafik die eigene
   KI-Beratung gestalten: Name, Bewertungsschwerpunkt, Gesprächseigenschaften und
   optionale eigene Hinweise. Die drei Vorlagen **Steve Jobs**, **Angela Merkel**
   und **Günther Jauch** stehen im kompakten Dropdown „Vorlage“ rechts neben „KI-Suchpersönlichkeit“ und füllen alle Felder aus; alles bleibt bearbeitbar. Das Namensfeld steht platzsparend neben „Name“. Das kleine Info-Icon neben der Überschrift öffnet die Erklärung mit Grafik.
3. **Schritt 3 – Ergebnisse:** „Passende Jobs finden“ starten; die KI-Auswertung
   kann etwa eine Minute dauern. Begründungen und Persönlichkeits-Scores vergleichen.
4. **Schritt 4 – Besprechen & verfeinern:** Im Chat rechts Fragen stellen oder die
   Suche anpassen; mobil öffnet „Profil & Chat öffnen“ den Chat. Die Karten aktualisieren sich
   nach jeder erfolgreichen Neubewertung oder Suche. Über Schritt 1 oder 2 lassen
   sich Profil und Persönlichkeit wieder öffnen. Chat- und Formularentwürfe
   bleiben beim Wechsel erhalten; „Abbrechen“ verwirft den geöffneten Formularentwurf.

Die KI-Beratung trägt den Namen der gewählten Persönlichkeit: **Angela-Merkel-KI**,
**Steve-Jobs-KI**, **Günther-Jauch-KI** oder **DIANA-KI**. Eigene Namen erscheinen
beispielsweise als **Alex-Weber-KI**; ein bereits vorhandenes „-KI“ wird nicht
verdoppelt. Chat-Absender, Stellenkarten, Formularhinweise und Such-Popup verwenden
diese Bezeichnung. Unangewendete Änderungen benennen bestehende Ergebnisse nicht
um; laufende Anfragen verwenden die tatsächlich übermittelte Persönlichkeit.
Die Score-Bezeichnung bleibt zum Beispiel **Angela-Merkel-Score**. Die Plattform
heißt weiterhin **DIANA Jobsuche**.

GPT erhält die aktuelle KI-Bezeichnung für neue Antworten und Selbstvorstellungen.
Die Bezeichnung ist ein Anzeigename und keine Behauptung, die reale Person zu sein.
Neue Antworten speichern ihre damalige Persönlichkeitsbezeichnung als `advisor_name`.
Damit bleibt eine Steve-Jobs-KI-Antwort auch nach dem Wechsel zu Angela-Merkel-KI
korrekt beschriftet. Ältere Nachrichten ohne diese Metadaten verwenden weiterhin
den aktuellen Namen; ihre damalige Persönlichkeit wird nicht nachträglich geraten.
Nachrichtentexte, bestehende Sitzungen und Bewertungscaches bleiben erhalten.

Die Persönlichkeit prägt durch konkrete Sprachvorgaben Satzbau, Wortwahl und
Argumentation – sowohl im Chat als auch in der proaktiven Auswahlbegründung und
den Stichpunkten der Stellenkarten, einschließlich des ersten sichtbaren Grundes:

- **Steve-Jobs-KI:** pointiert, direkt und anspruchsvoll; klare Einschätzung zuerst,
  anschließend der konkrete Beitrag der Arbeit und offene Gestaltungsmöglichkeiten.
- **Angela-Merkel-KI:** ruhig, präzise und abwägend; vom tragenden Beleg über eine
  wichtige Einschränkung zu einem begründeten, gegebenenfalls bedingten Fazit.
- **Günther-Jauch-KI:** verständlich, dialogisch und neugierig; eine konkrete Rückfrage,
  wenn sie die Entscheidung unterstützt, ohne Quizsprache oder Show.
- **DIANA-KI:** zugänglich, ausgewogen und ermutigend, mit realistischen nächsten Schritten.
- **Eigene Persönlichkeit:** Eigenschaften und Freitext prägen den Ausdruck sichtbar;
  etwa knapp und direkt oder sorgfältig abwägend mit kritischen Prüffragen.

Stilistische Anlehnung ist ausdrücklich erlaubt. Keine Parodie, bekannten
Catchphrases, erfundenen Zitate oder Behauptungen, die reale Person zu sein.
Selbstgeschriebene hypothetische Sprachmuster dienen nur der Formulierung, nicht
als Jobbelege oder wiederkehrende Textbausteine. Fachliche Fakten, Score-Gewichte,
900-Zeichen-Grenze, zwei bis drei kurze Gründe und automatische Aktionswahl bleiben
unabhängig vom Stil. Die Umsetzung trennt dauerhafte Persönlichkeit und Antwortformat
gemäß den [OpenAI Docs zur GPT-5.4-Stilsteuerung](https://developers.openai.com/api/docs/guides/latest-model?model=gpt-5.4#control-personality-for-customer-facing-workflows).
Sie benötigt keine zusätzlichen Modellaufrufe pro Suche oder Nachricht.
Reine Systemrückmeldungen wie Nulltreffer oder abgewiesene Aktionen bleiben kurze
sachliche Texte; sie lösen keinen zusätzlichen GPT-Aufruf aus.

Das aktuelle **Suchprofil** lässt sich während der Ergebnisansicht direkt öffnen
und bearbeiten. Speichern aktualisiert dieselbe Sitzung; der bisherige Chat bleibt
erhalten. Abbrechen verwirft nur die nicht gespeicherten Profiländerungen.

**„Vorschläge für deinen nächsten Schritt“** passt bis zu drei Chatvorschläge an
das gespeicherte Profil, sichtbare Stellen und die letzten acht Nutzernachrichten
an. Dazu gehören konkrete Passungs- und Skillfragen sowie Verfeinerungen anhand
tatsächlich vorhandener Stellenarten, Arbeitsmodelle und Stundenangaben. Bereits
identisch gesetzte Stellenarten oder Wünsche werden nicht erneut angeboten.
Arbeitsmodell und Stunden werden als Präferenzen formuliert. Bei echten Nulltreffern
steht die Stellenart zum Lockern im Vordergrund; bei ausgeblendeten Scores bleiben
die Vorschläge allgemein. Kürzlich gestellte, wiedererkannte Fragen werden
übersprungen. Ein Klick übernimmt den Vorschlag nur als bearbeitbaren Chatentwurf.
Die Vorschläge entstehen lokal nach festen Kontextregeln ohne zusätzlichen
KI-Aufruf; sie verwenden keine vollständige semantische Analyse des Gesprächs.

Im Chat entscheidet **GPT-5.4 automatisch**, welcher Schritt nötig ist.
Jede Nachricht wird im Modus `auto` verarbeitet; eine Modus-Auswahl gibt es nicht.

- **Antwort:** Rückfragen, Vergleiche und Erklärungen verwenden die sichtbaren
  Karten. Jobs, Scores und Suchkandidaten bleiben unverändert. Dafür gibt es genau
  einen GPT-Aufruf, ohne neue Suchpersona, BM25, E5 oder Reranking.
- **Neu bewerten:** Neue Wünsche zu Ort, Arbeitsmodell oder Stunden, ein geänderter
  Lebenslauf, andere weiche Prioritäten oder eine andere Persönlichkeit
  bewerten die gespeicherten bis zu 20 Kandidaten erneut, ohne die Datenbank neu
  zu durchsuchen. B zeigt Scores und Begründungen und zunächst Stellen ab 70 Punkten;
  schwächere Stellen sind einblendbar. A zeigt alle zurückgegebenen Stellen ohne
  Scores und automatische Begründungsboxen.
- **Neue Suche:** Tatsächlich geänderte Suchaufgaben, angegebene Skills oder die
  Stellenart durchsuchen die gesamte dazu passende Datenbank erneut. Eine ausdrücklich
  gewünschte neue Suche funktioniert auch ohne Profiländerung.

Du kannst im Chat um eine Neubewertung bitten. Die direkte Aktion zum Nachsortieren
der vorhandenen Jobs ist weiterhin verfügbar. Neue Stellenarten oder ein neuer
Suchfokus werden nicht still auf die alte Auswahl angewendet; dafür ist eine
neue Suche erforderlich. Unklare Nachrichten führen zu einer kurzen Rückfrage.
Die Intent-Erkennung erfolgt durch GPT und kann sich irren; Profil und Aktionsstatus
machen die tatsächlich ausgeführte Änderung sichtbar.

Neue Suchen und Neubewertungen speichern alle bis zu 20 bewerteten Ergebnisse
mit dem Chat. Bei früheren Sitzungen mit fünf Karten und einem vollständigen
Kandidatenpool genügt einmal **„20 Jobs neu sortieren“**, um die übrigen bewerteten
Karten zu erhalten. Ein entsprechender Hinweis steht rechts bei den Aktionen.
Sehr alte Chats ohne gespeicherten Kandidatenpool benötigen stattdessen einmal
eine neue Suche. Rückfragen verändern gespeicherte Ergebnisse in beiden Fällen
nicht und lösen keine automatische Nachbewertung aus.

Bei einer erneuten vollständigen Suche mit unverändertem Bewerberprofil verwendet
DIANA die gespeicherte Suchpersona wieder. Das spart einen GPT-Aufruf; Stellen
werden trotzdem neu gesucht und bewertet. Der private, versionierte Fingerprint
berücksichtigt das ganze Profil einschließlich Lebenslauf und weicher Wünsche.
Profiländerungen oder fehlende bzw. veraltete Cache-Daten erzeugen eine neue
Suchpersona. Ein Persönlichkeitswechsel allein macht das nicht erforderlich.
Eine zwischenzeitliche Neubewertung geänderter Wünsche übernimmt nicht heimlich
die alte Suchpersona als aktuell; eine spätere Vollsuche erkennt deren alten Stand.

Pools aus der früheren Version, die noch durch Ort, Arbeitsmodell oder Stunden
vorab eingeschränkt wurden, erhalten einen Hinweis zur einmaligen neuen Suche.
Im Modus „Automatisch“ wird diese beim nächsten tatsächlichen Bewertungsauftrag
nachgeholt; reine Fragen lösen sie nicht aus. Eine ausdrücklich gewählte reine
Neubewertung wird bis dahin mit Erklärung zurückgestellt. Damit bleiben zuvor
ausgeschlossene Stellen nicht dauerhaft außerhalb des Kandidatenpools.

Die Profilangaben bleiben beim Zurückgehen erhalten. Erst der letzte Klick auf
„Passende Jobs finden“ startet die KI-Suche. Die Webseite trägt das Kompass-Logo.
Am Desktop lässt sich die Trennlinie zwischen Jobs und Chat ziehen. Nach Auswahl
der Trennlinie funktionieren auch die Pfeiltasten; Home/End wählen die minimale
bzw. maximale Breite, Doppelklick setzt sie zurück. Die Breite wird als lokale
Darstellungspräferenz gespeichert. Auf schmalen Bildschirmen führen die
Schrittübersicht und der Button „Besprechen & verfeinern“ zur jeweiligen Ansicht.

Das DIANA-Logo führt zur Startseite `/` mit einer kurzen Vorstellung von DIANA
und Christoph Scharnagl, seinem Foto und den beruflichen Kontaktdaten. Der große
Button „Umfrage starten“ steht rechts neben dem Projekttext, mobil direkt darunter.
Der frühere Link `/mehr-erfahren` bleibt als Einstieg in dieselbe Infoseite gültig.
In der eingebetteten Umfrageansicht ist das Logo nicht verlinkt, damit es keine
weitere Umfrage innerhalb der Jobsuche öffnet. Die Testsuche und ihre Entwürfe
bleiben beim Wechsel zwischen System und Fragebogen erhalten.

In B heißt die Bewertung je nach gespeicherter Persönlichkeit **DIANA-Score**,
**Steve-Jobs-Score**, **Angela-Merkel-Score**, **Günther-Jauch-Score** oder
**Eigener-Name-Score**. Eigene Persönlichkeiten benötigen einen Namen; eine
Vorschau zeigt die spätere Beschriftung. Beim Bearbeiten bleibt die Beschriftung
der angezeigten Ergebnisse unverändert, bis die neue Bewertung erfolgreich ist.
Die Skala bleibt 1–100.

In B werden alle bewerteten Stellen mit **70 Punkten oder mehr** direkt angezeigt –
auch alle 20, wenn sämtliche Scores die Grenze erreichen. Es gibt keine zusätzliche
Begrenzung auf fünf Karten. Die zusätzliche Anzahl-/Filterzeile unter „Deine
Empfehlungen“ ist entfernt. Stellen unter 70 Punkten werden zunächst ausgeblendet.
Der Hinweis unter den Stellenanzeigen mit **„Weitere Stellen anzeigen“** nennt die Zahl der ausgeblendeten Ergebnisse und
blendet diese lokal ein. Die Ansicht und der Tastaturfokus wechseln dabei zur
ersten zusätzlichen Stelle; beim Ausblenden bleibt der Fokus am Button.
Liegt die gesamte Auswahl unter 70, erscheint ein Hinweis
mit **„Alle … Stellen trotzdem anzeigen“**. Beides benötigt keine Suche oder KI-Anfrage.
Der Hinweis nennt den Score der aktuellen Persönlichkeit. Die Stellen lassen sich
anschließend wieder ausblenden. Nach einer neuen Suche oder Neubewertung gilt
die Grenze erneut; reine Chatantworten erhalten die aktuelle Anzeigeentscheidung.
Die Grenze ist eine Darstellungsregel (`frontend/score-visibility.js`), keine
empirisch kalibrierte Qualitätsgarantie. Scores und alle 20 Kandidaten bleiben
unverändert in der laufenden Sitzung gespeichert. Auch ausgeblendete Karten können
im Chat besprochen werden. In A entfällt diese Ausblendung: Dort werden alle bis zu
20 zurückgegebenen Stellen ohne sichtbare Bewertung dargestellt.

Inhalt und Originalfoto der Vorstellung stammen aus der bereitgestellten
Präsentation „Vorstellung Promotionsthema.pptx“, Folien 1, 11 und 12; das Foto
wurde unverändert aus `ppt/media/image12.png` übernommen. Berufliche E-Mail
und Sprechzeiten wurden am 09.09.2026 mit dem
[offiziellen Hochschulprofil](https://www.th-nuernberg.de/person/scharnagl-christoph/)
abgeglichen, Institutsname und Adresse mit der
[IFAI-Team- und Kontaktseite](https://www.th-nuernberg.de/einrichtungen-gesamt/in-institute/institut-fuer-angewandte-informatik-ifai/team-und-kontakt/).

Neue GPT-Chatantworten sind auf **900 Zeichen** begrenzt und zielen auf etwa
40–80 Wörter. Alle bis zu 20 Jobbewertungen behalten ihre eigenen Begründungs-Stichpunkte.
Unter **„Warum das passen könnte“** ist zunächst nur der erste Stichpunkt sichtbar.
**„Mehr anzeigen“** öffnet die weiteren Gründe und passenden Fähigkeiten;
**„Weniger anzeigen“** steht ganz unten in der Begründungsbox, nach allen Gründen
und Fähigkeiten, und klappt sie wieder ein. Die Bedienung funktioniert per Klick,
Tastatur und Antippen. Bei geänderter Bewertung beginnt die betreffende Karte wieder
eingeklappt; reine Chatantworten erhalten die Klappansicht. Neue KI-Bewertungen ordnen
die Gründe nach Relevanz, mit der wichtigsten fachlichen Passung oder entscheidenden
Lücke zuerst. Bereits gespeicherte Begründungen behalten ihre Reihenfolge.
Die Aktionen **„Stellendetails“** und **„Mit … besprechen“** stehen nebeneinander
in einer kompakten Zeile. Geöffnete Stellendetails nutzen darunter die volle Breite.
Bei schmalen Karten erscheinen die Kurzbeschriftungen „Details“ und „Besprechen“;
der zugängliche Chat-Button-Name enthält weiterhin die gewählte Persönlichkeit.
Längere gespeicherte Chatnachrichten erscheinen zunächst als Vorschau; „Mehr anzeigen“
öffnet den vollständigen Text. Der gespeicherte Verlauf wird dabei nicht verändert.

Während der einmaligen Indexierung zeigt die Seite den tatsächlichen Fortschritt.
Die Suche über den kompletten Datensatz wird erst nach erfolgreichem Abschluss
freigegeben. Es werden für die Suche alle Anzeigen berücksichtigt, anschließend
bis zu 20 Kandidaten durch GPT bewertet. A zeigt alle zurückgegebenen Stellen;
B zeigt zunächst Empfehlungen ab 70 Punkten und bietet das Einblenden weiterer Stellen an.

## Start

Python **3.12 oder neuer**. Eine lokale `.venv` wird beim Aufbau dieses Projekts
angelegt. Falls noch keine Umgebung existiert:

```bash
python3.12 -m venv .venv
.venv/bin/python -m pip install -r requirements-dev.txt
```

Der Schlüssel steht ausschließlich in der lokalen `.env` (Dateimodus `0600`),
die von `.gitignore` ausgeschlossen wird. `.env.example` enthält keinen Schlüssel.
Bei einer neuen Projektkopie `.env.example` nach `.env` kopieren und
`OPENAI_API_KEY` lokal eintragen. Bestehende Umgebungsvariablen haben Vorrang.
Den im Chat mitgeteilten Schlüssel vor einer Weitergabe oder Veröffentlichung
des Projekts im OpenAI-Konto ersetzen und die lokale `.env` aktualisieren.

```bash
# Einmalig: Original-E5 laden und alle konfigurierten Anzeigen vorberechnen.
.venv/bin/flask --app app:create_app warmup

# Lokaler Server, http://127.0.0.1:5050
.venv/bin/python app.py
```

E5 wird erst bei `warmup` oder einer Suche geladen. Die Modellgewichte belegen
ca. 1,12 GB beim Download; zusätzlich werden RAM und Bibliotheken benötigt.
Der Standard `E5_DEVICE=cpu` funktioniert ohne CUDA. Auf geeigneter Hardware
kann `E5_DEVICE=mps` oder `cuda` gewählt werden. Die Vektoren werden pro Text
auf Platte zwischengespeichert; Änderungen am Text oder an der Modellrevision
führen zu neuen Cache-Einträgen. Es gibt keinen stillen Ersatz durch ein anderes
Embedding-Modell oder durch eine reine BM25-Suche.

Falls der optionale Xet-Download ohne Fortschritt hängt, kann Hugging Face auf
den normalen HTTP-Download umgestellt werden:

```bash
HF_HUB_DISABLE_XET=1 .venv/bin/flask --app app:create_app warmup
```

## API ausprobieren

```bash
curl http://127.0.0.1:5050/api/health

curl -X POST http://127.0.0.1:5050/api/search \
  -H 'Content-Type: application/json' \
  --data-binary @example_search.json

# Gleiches Profil, zusätzlich mit temporärer Chatsitzung:
curl -X POST http://127.0.0.1:5050/api/onboard \
  -H 'Content-Type: application/json' \
  --data-binary @example_search.json
```

Die zurückgegebene `session_id` für weitere Nachrichten einsetzen:

```bash
curl -X POST http://127.0.0.1:5050/api/chat \
  -H 'Content-Type: application/json' \
  -d '{"session_id":"HIER_DIE_SESSION_ID_EINSETZEN","message":"Bitte nur Werkstudentenstellen mit maximal 20 Stunden pro Woche."}'
```

| Endpunkt | Zweck |
| --- | --- |
| `GET /api/health` | Prozess, Datenbank und Konfigurationsstatus; kein Modellzugriff |
| `GET /api/jobs` | 20 unbewertete Vorschauanzeigen und Gesamtzahl der Datenbank |
| `GET /api/index-status` | Tatsächlicher Fortschritt und Freigabe der vollständigen Suche |
| `POST /api/search` | Profil → Suchergebnis ohne gespeicherten Chat |
| `POST /api/onboard` | Profil → Suche, Begrüßung/Begründung und neue Chat-Sitzung |
| `POST /api/chat` | Nachricht, Profil oder Aktion → Antwort, Pool-Neubewertung oder neue Suche |
| `GET /api/sessions/<session_id>` | Gespeicherten Verlauf und Jobkarten laden |
| `DELETE /api/sessions/<session_id>` | Gespeicherten Chat samt Profil löschen |

Antworten enthalten `profile`, `persona`, `jobs`, `assistant_message` und
`retrieval` mit Kandidatenanzahlen. Jeder Job enthält normalisierte Kartenfelder,
`match` mit Score, `reasons` (kurze Stichpunkte), `reason` (kompatible Zusammenfassung), passenden und nicht belegten Skills sowie
`retrieval` mit BM25-/Vektorrang und RRF-Score. Der Match-Score ist eine
gewichtete LLM-Einschätzung von 1–100, keine Wahrscheinlichkeit. Neue Bewertungen
enthalten außerdem `components`, `scoring_weights` und `scoring_version`, sodass
der Chat den tatsächlich angezeigten Score erklären kann. Alte Karten bleiben lesbar.

`/api/chat` interpretiert ausdrücklich gewünschte Änderungen. `mode` ist `auto`
(Standard), `rerank` oder `search`. Ein expliziter Modus darf ohne Nachricht gesendet
werden. Ein vollständiges `profile` bearbeitet das Suchprofil innerhalb derselben
Sitzung; es wird separat von einer Chatnachricht übermittelt. `advisor` ändert die
Bewertungsperspektive. Die Antwort enthält `chat_action` (`answer`, `rerank`, `search`)
und `candidate_pool` mit `available`, `count` und `refresh_required`. Die internen Kandidatentexte sind
nicht Teil der öffentlichen API-Antwort.

Für den Suchstatus können `/api/onboard` und `/api/chat` mit
`Accept: application/x-ndjson` aufgerufen werden. Der Stream liefert
`{"type":"phase","phase":"search"}` erst unmittelbar vor einer tatsächlich
ausgeführten vollständigen Suchpipeline und endet mit
`{"type":"result","data":{...}}`. Fehler erscheinen als
`{"type":"error","error":{"message":"..."},"status":503}` mit dem jeweiligen
Fehlerstatus. Nach Beginn des Streams ist der HTTP-Status bereits 200; maßgeblich
ist dann das terminale Ereignis. Ohne diesen Accept-Header bleiben JSON-Antworten
und deren HTTP-Status unverändert. Die Webseite sendet bei Verbindungsfehlern
keinen Auftrag automatisch erneut, sondern prüft wie bisher den Sitzungsstand.

Nicht erwähnte Filter und Präferenzen bleiben erhalten. Der Server vergleicht die validierten
Profile und erzwingt eine neue Suche bei Änderungen der Retrieval-Eingaben; bloße
Listenreihenfolge und Groß-/Kleinschreibung zählen nicht als fachliche Änderung.
Auch reine Änderungen innerer Leerzeichen in Ortsangaben führen zu keiner Suche.
Die vorhandenen API-Felder `filters.locations`, `filters.remote` und
`filters.max_hours` bleiben für bestehende Clients und Sitzungen erhalten; der
Containername bedeutet für diese Felder ausdrücklich keine harte Filterung.
Zustand und Ergebnisse werden erst nach
erfolgreicher Verarbeitung gespeichert. Parallele Änderungen derselben Sitzung
liefern bei einem Konflikt HTTP 409. Der Verlauf bleibt im Produktivmodus nur im RAM und überlebt keinen Neustart; maximal 100 Nachrichten werden aufbewahrt, die letzten zwölf dienen
dem LLM als Gesprächskontext. Für Rückfragen kennt das antwortende GPT außerdem
alle bis zu 20 bewerteten Karten in ihrer sortierten Reihenfolge samt
Begründungen, auch für Fragen zu Stellen hinter Rang fünf. Die KI weiß, dass
Stellen unter 70 zunächst ausgeblendet sein können. Der vollständige Profilzustand
wird stets übergeben.

## Persönlichkeiten: aktueller Stand und historische Details

Aktuell startet A mit einer festen sachlichen Standardberatung, B/C mit
Top-Berufsberater. B kann zur unveränderten Fachexperten-Vorlage wechseln;
C kann zusätzlich selbst gestalten. Aktuelle Vorlagen stehen als versionierte
MLDS-Dateien in `personas/`; Beschreibung: [MLDS.md](MLDS.md).

### Historische Presets und frühere Bedienung

Die folgenden Beschreibungen bekannter Personen und ihrer Gewichte betreffen
historische Presets und frühere Oberflächen. Sie sind keine aktuelle
Vorlagenauswahl der V9-Studie.


Die Oberfläche startet mit einer **eigenen Persönlichkeit** und zeigt alle Felder
direkt. Es gibt keinen Wechsel mehr zwischen getrennten Vorbild- und Eigenbau-Modi.
Die drei bekannten Personen sind optionale, bearbeitbare Vorlagen: Ein Klick füllt
Name, Schwerpunkt, Eigenschaften und eigene Hinweise. Gesendet werden die sichtbaren
Felder als `mode: custom`; spätere Änderungen werden nicht durch versteckte feste
Vorbild-Einstellungen überschrieben. Bestehende Sitzungen ändern sich erst beim
ausdrücklichen Anwenden. Beim Bearbeiten alter Presets werden daraus eigene Entwürfe;
die API unterstützt die bisherigen Presets weiterhin.

Vor dem ersten Wechsel vom Profil zur Persönlichkeit erscheint die kurze Erklärung
**„KI-Suchpersönlichkeit“**. Die zusammenhängende Einleitung erklärt die Rolle von
Profil und Persönlichkeit, den Vorrang fachlicher Passung und die drei Vorlagen.
Darunter führt die Grafik von der Persönlichkeit über Verbindungen und zwei Pfeile
zu **„Jobs bewerten & sortieren“** und **„Mit dir sprechen“**. Der erste Bereich
macht ausdrücklich klar, dass Nutzerprofil und KI-Persönlichkeit gemeinsam die
Bewertung und Reihenfolge der Jobs bestimmen. Der zweite erklärt den Einfluss auf
Antworten und Begründungen. Beispiele und ein separater
Hinweis unter der Grafik entfallen. „Persönlichkeit erstellen“ führt zu Schritt 2;
Schließen oder Escape bleibt beim Profil. Nach dem Bestätigen erscheint die Grafik
bei einem Rücksprung nicht erneut. „Neu starten“ setzt diese Einführung zurück.
Der Hilfelink **„Wie beeinflusst das meine Suche?“** öffnet sie jederzeit im
Persönlichkeitsformular erneut, auch beim Bearbeiten. Die Grafik verwendet
HTML/CSS und vorhandene Icons, ist auf kleinen Bildschirmen scrollbar und benötigt
keinen zusätzlichen Modellaufruf.

Die Persönlichkeit steht als `advisor` getrennt neben dem Bewerberprofil.
Harte Filter, belegte Kenntnisse und die semantische Suchanfrage werden durch
die Auswahl eines Vorbilds nicht verändert. GPT bewertet jeden der bis zu 20
Kandidaten nach denselben sechs Dimensionen. Der Server berechnet daraus die
gewichteten Scores und sortiert alle Ergebnisse danach. Es gibt keine zufälligen
Punktaufschläge nach Namen; bei gleichwertigen Kriterien sind gleiche Scores möglich.

Die folgenden Gewichte gelten für die weiterhin unterstützten, festen API-Presets.
Die neuen editierbaren Vorlagen verwenden die darunter erläuterte Berechnung aus
Schwerpunkt und Eigenschaften.

| Kriterium | DIANA | Steve Jobs | Angela Merkel | Günther Jauch |
| --- | ---: | ---: | ---: | ---: |
| Fachliche Passung zum Profil | 60 % | 60 % | 60 % | 60 % |
| Ausdrückliche weiche Suchwünsche | 15 % | 15 % | 15 % | 15 % |
| Fachliche Vertiefung | 7 % | 5 % | 8 % | 3 % |
| Lernen und Betreuung | 6 % | 5 % | 2 % | 17 % |
| Innovation und Gestaltung | 6 % | 15 % | 0 % | 3 % |
| Klarheit von Aufgaben und Anforderungen | 6 % | 0 % | 15 % | 2 % |

Die Teilwerte liegen zwischen 1 und 100. Unbekannte ergänzende Kriterien erhalten
`null` und gehen neutral mit 50 ein; daraus darf kein angeblicher Vorteil abgeleitet
werden. Der Fachwert muss durch Profil und Stellenanforderungen begründet sein.
Der gewichtete Mittelwert wird auf eine ganze Zahl gerundet (halbe Punkte aufwärts).
Ein Fachwert unter 40 begrenzt den Gesamtscore auf 39; unter 60 auf 69.

Die neutralen Teilbewertungen aller Kandidaten werden privat mit dem Profil und
Pool gespeichert. Ein reiner Persönlichkeitswechsel verwendet dieselben Teilwerte,
damit die Unterschiede aus der Gewichtung entstehen. Neue Begründungen und Chattext
passen zur neuen Perspektive. Änderungen an Profil oder Anzeigen, eine neue
Gesamtsuche oder eine neue Bewertungsversion lösen eine erneute Beurteilung aus.
Alte Sitzungen erhalten die neue Bewertungsgrundlage bei ihrer nächsten expliziten
Neubewertung. Bis dahin bleiben ihre gespeicherten Scores erhalten.

Bei gültigen gespeicherten Teilbewertungen liefert GPT nur noch die neuen Gründe,
Skillangaben und die kurze Antwort. Die festen Komponenten werden serverseitig
ergänzt und nicht nochmals vom Modell erzeugt. Alle 20 Ergebnisse behalten ihre
vollständigen Scores und Begründungen. Exakt doppelte Beschreibungstexte sowie
unveränderte, erneut übergebene Jobdetails im Gesprächskontext werden für den
Transport zusammengefasst; die ursprüngliche Bewertungsgrundlage bleibt erhalten.

Im Chat spricht Steve direkt und gestaltungsorientiert, Angela ruhig und abwägend,
Günther verständlich und gezielt nachfragend; DIANA bleibt ausgewogen und ermutigend.
Konkrete Stilregeln gelten für Antworten und Neubewertungen. Keine Zitate,
Show-Sprüche, Quizsprache oder Identitätsbehauptungen. Die bisherigen kurzen
Antwortgrenzen bleiben erhalten.
Die Inspirationsprofile bilden keine realen Personen nach und behaupten keine
Unterstützung durch diese Personen.

Eigene Varianten erlauben einen Namen, eine bis vier Eigenschaften und den
Schwerpunkt „Ausgewogen“, „Fachliche Vertiefung“, „Lernen & Entwicklung“ oder
„Innovation & Gestaltung“. Unter **„Eigene Hinweise“** steht zusätzlich ein
optionales Freitextfeld mit bis zu **2.000 Zeichen** zur Verfügung. Darin kannst du
den gewünschten Gesprächsstil und den Blickwinkel für die Begründungen beschreiben.
Der Text bleibt mit der Persönlichkeit gespeichert und wird für Chatantworten und
Neubewertungen berücksichtigt. Eine reine Textänderung nutzt die vorhandenen
Kandidaten und gespeicherten Teilbewertungen; sie startet keine vollständige Suche.
Die drei Vorlagen füllen auch diesen Freitext mit bearbeitbaren Stilhinweisen aus.
Nur alte feste API-Presets ignorieren ihn weiterhin.

Schwerpunkt und Eigenschaften bestimmen die Verteilung
der ergänzenden 25 Prozentpunkte; die festen 60/15-Anteile bleiben erhalten.
Name und Reihenfolge der ausgewählten Eigenschaften beeinflussen die Rechnung
nicht. Die freie Beschreibung verändert keine Gewichte oder fachlichen Nachweise;
sie prägt Formulierungen und Begründungen. Unbelegte Vorteile werden nicht ergänzt.

Die unveränderten neuen Vorlagen verteilen die ergänzenden Gewichte wie folgt:

| Vorlage / Ausgangspunkt | Fachliche Tiefe | Lernen | Gestaltung | Klarheit |
| --- | ---: | ---: | ---: | ---: |
| Eigene DIANA mit Ausgangswerten | 7 % | 7 % | 4 % | 7 % |
| Steve Jobs | 3 % | 5 % | 15 % | 2 % |
| Angela Merkel | 7 % | 4 % | 3 % | 11 % |
| Günther Jauch | 2 % | 15 % | 3 % | 5 % |

Fachliche Passung (60 %) und ausdrückliche Wünsche (15 %) bleiben unverändert.
Beim Ändern von Schwerpunkt oder Eigenschaften werden die ergänzenden Gewichte
neu berechnet. Änderungen an Namen oder Freitext verändern diese Gewichte nicht.

Beispiel für einen Wechsel innerhalb derselben Sitzung:

```json
{
  "session_id": "DIE_BESTEHENDE_SESSION_ID",
  "advisor": {"mode": "preset", "preset": "angela"}
}
```

Diesen Body an `POST /api/chat` senden. Ohne `message` bleibt das Profil
unverändert und die bestehende Suchpersona sowie der Kandidatenpool werden
wiederverwendet. BM25 und E5 werden dabei nicht erneut ausgeführt. Erst nach
erfolgreichem Reranking werden Konfiguration, Karten und Antwort zusammen
gespeichert. Ein normaler Chat ohne `advisor` behält die letzte Auswahl.

## Stellenart, Präferenzen und Quelldaten

Das Original `ChristophJobs01-2026.json` ist eine Liste mit **8.537 Anzeigen**.
Die lokale Datenbank enthält bereits alle Anzeigen. Die Originaldatei bleibt
unverändert. Eine neue Projektkopie startet mit fünf fiktiven Anzeigen; dort
kann der Export mit dem untenstehenden Befehl importiert werden.

| Quelldaten | Normalisiertes Feld / Bedeutung |
| --- | --- |
| `jobId` | `id`, als String |
| `angebotstitel`, `prsFirma` | `title`, `company` |
| `jobKategorie[].bezeichnung` | `employment_types` und originale `categories` |
| `anstellungsart[].bezeichnung` | `contract_types`, etwa Befristet/Festanstellung |
| `arbeitsort` | `location`, einschließlich Straße/PLZ, falls vorhanden |
| `erwartungenTitelText`, `aufgabenTitelText` | `requirements`, `tasks`, von HTML bereinigt |
| `angebotTitelText` | `benefits` |
| `arbeitszeitMin`, `arbeitszeitMax` | `hours_min`, `hours_max` |
| `homeOffice` | `remote`: onsite/hybrid/remote/unknown |
| `bewerberportal` | `application_url`, nur gültiges HTTP(S) |

`employment_types` verwendet `werkstudent`, `praktikum`, `vollzeit`, `teilzeit`,
`ausbildung`, `trainee`, `abschlussarbeit`, `sonstige`. Werkstudent/Praktikum
werden aus den Jobkategorien und expliziten Bezeichnungen erkannt; Befristet ist
keine Beschäftigungskategorie. Vollzeit/Teilzeit werden nur bei ausdrücklich
entsprechender Bezeichnung gesetzt. Alle nicht abgebildeten Kategorien bleiben
als Original-Labels verfügbar und erhalten `sonstige`.

Nur `employment_types` wird **vor** beiden Suchverfahren per parametrisierter
SQL-Abfrage angewendet. Mehrere Stellenarten bedeuten ODER; eine leere Liste
berücksichtigt alle Stellenarten. Ort, Arbeitsmodell, Stunden und Lebenslauf
schließen auf dieser Stufe keine Anzeige aus.

- `locations`: bevorzugte Orte. Das LLM berücksichtigt belegte Ortsangaben und
  benennt Abweichungen; ohne Entfernungsdaten erfindet es weder Umkreis noch Pendelzeit.
- `remote`: 0 % → `onsite`, 100 % → `remote`, 0–49 % und 50–100 % → `hybrid`.
  Die Quellintervalle belegen keine genaue oder garantierte Homeoffice-Quote.
  Der Wunsch nach einem Arbeitsmodell wird bei der Bewertung berücksichtigt.
  Abweichende oder unbekannte Arbeitsmodelle bleiben im Suchbestand.
- `max_hours`: gewünschte maximale Wochenstunden. Ein Angebot mit 10–20 h kann
  zu 15 verfügbaren Stunden passen. Eine höhere Mindeststundenzahl ist eine
  bekannte Abweichung; fehlende oder ungültige Stundenangaben bleiben offen.
- `cv_text`: fachliche Belege aus Ausbildung, Projekten und Erfahrung. Der
  Lebenslauf ist keine Mussliste, deren sämtliche Themen jede Anzeige enthalten
  muss. Er unterstützt auch die inhaltliche Suchanfrage bei einer neuen Suche;
  eine Bearbeitung bewertet zunächst den vorhandenen Pool mit den aktuellen Belegen.

Ort, Arbeitsmodell und Stunden fließen gemeinsam mit weiteren weichen Wünschen
in `preferences_fit` ein; allein solche Abweichungen senken nicht die fachliche
Teilbewertung und führen nicht zu fachlichen Score-Grenzen. Bekannte Nachteile
werden in kurzen Stichpunkten benannt, unbekannte Angaben bleiben unbekannt.
Die Bewertungsversion `persona-weighted-v2` verwirft dafür ältere Teilwert-Caches.

Keine Anzeigen der gewählten Stellenart führt zu einer leeren Liste mit Erklärung, ohne Filterlockerung,
OpenAI-Aufruf oder E5-Inferenz. Weniger als fünf zulässige Anzeigen liefern
entsprechend weniger Ergebnisse.

## Originaldatei importieren

Die Datei enthält unescaped Steuerzeichen in JSON-Strings. Standardmäßig meldet
der Import diesen Fehler. `--allow-control-characters` erlaubt ausdrücklich nur
diese JSON-Abweichung; fehlerhafte Struktur und nicht endliche Zahlen bleiben
Fehler. HTML-Tags sowie Script-/Style-Inhalte werden entfernt. Inhalte aus Anzeigen
und Lebensläufen werden im LLM ausschließlich als Daten behandelt.

Für echte Anzeigen eine eigene Datenbank ohne Demo-Daten verwenden:

```bash
DATABASE_PATH=instance/real-jobs.sqlite3 SEED_DUMMY_DATA=false \
  .venv/bin/flask --app app:create_app import-jobs \
  /Users/christophscharnagl/Downloads/ChristophJobs01-2026.json \
  --allow-control-characters

DATABASE_PATH=instance/real-jobs.sqlite3 SEED_DUMMY_DATA=false \
  .venv/bin/python app.py
```

Importe aktualisieren bestehende IDs und ergänzen neue in einer Transaktion.
Nicht mehr im Export enthaltene IDs werden nicht gelöscht. Ein Import in die
Demo-Datenbank lässt die fünf fiktiven Anzeigen bestehen. Für 8.537 Anzeigen
empfiehlt sich vorheriges `warmup` mit denselben Umgebungsvariablen; die erste
Berechnung des ganzen Korpus braucht wesentlich länger als die fünf Demo-Jobs.

## Pipeline und Modelle

1. GPT-5.4 erzeugt ein strukturiertes Suchprofil mit Persona-Text und Suchanfrage.
   Nur die gewählte Stellenart ist verbindlich. Orts-, Arbeitsmodell- und
   Stundenwünsche gehören in die LLM-Bewertung.
2. SQLite filtert ausschließlich nach Stellenart. BM25 (`rank_bm25.BM25Okapi`) und
   E5 durchsuchen parallel exakt diese Teilmenge. Bei null zulässigen Anzeigen
   entfällt auch Schritt 1.
3. Beide Ranglisten liefern bis zu 20 Treffer. RRF addiert pro Treffer
   `1 / (60 + Rang)` aus jedem Verfahren und behält die besten 20. Dokumente ohne
   gemeinsame BM25-Tokens erhalten keinen künstlichen lexikalischen Bonus.
4. GPT-5.4 liefert Teilbewertungen und Begründungen für jeden fusionierten
   Kandidaten. Der Server prüft die vollständige, eindeutige ID-Abdeckung, berechnet
   die gewichteten Scores und liefert alle bis zu 20 bewerteten Karten. Bei gleichen
   Scores bleibt die ursprüngliche Kandidatenreihenfolge erhalten. Ungültige
   Antworten, erfundene IDs, Verweigerungen und unvollständige Ausgaben führen zu
   einem kontrollierten Fehler. Die App ergänzt nur die Original-Jobdaten.

E5 verwendet exakt `intfloat/multilingual-e5-large-instruct`, auf die Revision
`274baa43b0e13e37fafa6428dbc7938e62e5c439` festgelegt. Suchanfragen erhalten
`Instruct: …\nQuery: …`, Dokumente keinen Prefix; Vektoren sind normalisiert.
Das Modell begrenzt Texte auf 512 Tokens. Anforderungen und Aufgaben stehen deshalb
vor allgemeinen Firmentexten. Längere Lebensläufe werden durch die Persona-Abfrage
verdichtet; längere Anzeigen können dennoch Informationen verlieren. Chunking
ist ein sinnvoller nächster Ausbauschritt.
[E5-Modellkarte](https://huggingface.co/intfloat/multilingual-e5-large-instruct)

OpenAI wird serverseitig über die Responses API mit Pydantic Structured Outputs,
`store=False`, 90 Sekunden Timeout, einem Retry und begrenzter Ausgabelänge
aufgerufen. Das Ausgabelimit beträgt 10.000 Tokens für bis zu 20 vollständige
Bewertungen, sonst 6.000; der Chattext bleibt auf 900 Zeichen begrenzt.
Alle OpenAI-Aufrufe verwenden den festen Snapshot **`gpt-5.4-2026-03-05`**.
Der Modellname wird nicht automatisch auf einen anderen Snapshot umgestellt.
Neue Teilnahmen werden dem verwendeten Systemstand zugeordnet; alte Antworten
ohne Nachweis bleiben als unbekannt gekennzeichnet. Details: [ADMIN.md](ADMIN.md).
[GPT-5.4](https://developers.openai.com/api/docs/models/gpt-5.4),
[Structured Outputs](https://developers.openai.com/api/docs/guides/structured-outputs)

Alle KI-Aufrufe verwenden jetzt zentral **`reasoning.effort=none`**: neue fachliche
Bewertungen, Persona-Erzeugung, Profilverfeinerung, Chatplanung sowie Begründungen
aus bereits gespeicherten Teilbewertungen. Diese Einstellung wird von
[GPT-5.4 offiziell unterstützt](https://developers.openai.com/api/docs/models/gpt-5.4).
Die bisherigen Werte `medium` und `low` werden nicht mehr gesetzt. Die Scores
werden bei gültigen gespeicherten Teilbewertungen weiterhin aus dem Cache berechnet.
Structured Outputs, Streaming, alle 20 Bewertungen, die Begründungen und die
Persönlichkeitsgewichtung bleiben erhalten. `/api/health` meldet den aktiven
Denkaufwand als `openai_reasoning_effort`; die Performance-Logs enthalten ihn ebenfalls.
Die Suchpersona hat kompaktere Textziele;
Grenzen für Fachpassung, Scores und Begründungen bleiben erhalten. Die Optimierung
folgt den [OpenAI-Empfehlungen zur Latenz](https://developers.openai.com/api/docs/guides/latency-optimization):
weniger wiederholte Anfragen und weniger überflüssige Ein- und Ausgabe.
Datensparsame Performance-Logs messen die Suchphasen und GPT-Aufrufe ohne
Profiltexte, Stelleninhalte, Schlüssel oder Sitzungskennungen. Eine konkrete
Wartezeit ist weiterhin von Modellantwort, Umfang und Auslastung abhängig.

Zwei vollständige Live-Suchen am 10.09.2026 mit GPT-5.4 und `none` über alle
8.537 Anzeigen dauerten **63,3 s direkt nach Neustart** und **40,6 s bei geladenem
E5-Modell**. Im zweiten Lauf entfielen 3,6 s auf BM25/Vektorsuche/RRF, 4,7 s auf
die Persona und 31,0 s auf die Bewertung aller 20 Stellen mit Begründungen.
Dies sind zwei Einzelmessungen mit einem fiktiven Profil, keine Zeitgarantie;
der erste Lauf hatte einen parallelen Chat-Aufruf. Die
[vollständigen Messwerte](search-latency-benchmark-2026-09-10.json) enthalten
Phasen, Tokenzahlen und die Zeit bis zum ersten gestreamten Chattext.

Ein früherer kontrollierter Einzelvergleich (vor der Umstellung auf `none`) für das Nachsortieren von 20 fiktiven Stellen
mit bereits gespeicherten Teilbewertungen ergab **27,6 → 18,0 Sekunden**
(rund **35 % kürzer**). Alle Scores blieben gleich. Dies misst den wiederholten
Begründungsschritt, nicht die erste Vollsuche; die Wartezeit kann schwanken.
Die [Messwerte](latency-benchmark.json) dokumentieren auch die Zwischenvariante,
die trotz kompakterer Ausgabe mit `medium` noch keinen Zeitgewinn zeigte.

Die konkreten Gesprächsregeln trennen dauerhafte Persönlichkeit von den festen
Ausgabe- und Längengrenzen entsprechend der
[offiziellen GPT-5.4-Prompting-Dokumentation](https://developers.openai.com/api/docs/guides/latest-model?model=gpt-5.4).

Die Angabe zur überlegenen CV-Passung stammt aus der Aufgabenstellung. Die
Masterarbeit, Testurteile und Messdaten liegen nicht bei. Die Gewichtung von
60 % Fachpassung, 15 % Suchwünschen und 25 % persönlichkeitsspezifischen Kriterien
ist eine dokumentierte Prototyp-Heuristik. Die Erstbewertung der Dimensionen durch
GPT kann zwischen frischen Suchläufen schwanken; sie ist kein objektiver Messwert.
Eine empirische Bestätigung erfordert annotierte Profile und
Jobs, etwa für Recall@20, NDCG@5, Precision@5 und Ablationen der drei Suchstufen.

## Tests und Gunicorn

Für die separate Docker-Installation auf dem Forschungsserver, Port 5051,
siehe [Betrieb und Aktualisierung](DEPLOYMENT.md). Der Container lädt E5 vor der
ersten Anfrage und speichert Daten dauerhaft außerhalb des Images.

```bash
.venv/bin/python -m pytest -q

# Zusätzlich den echten Export in einer temporären Datenbank prüfen:
JOB_EXPORT_TEST_PATH=/Users/christophscharnagl/Downloads/ChristophJobs01-2026.json \
  .venv/bin/python -m pytest -q

.venv/bin/gunicorn --workers 1 --threads 4 --timeout 600 \
  --bind 127.0.0.1:5050 'app:create_app()'
```

Die automatisierten Tests verwenden echte SQLite-/BM25-Implementierungen und
injizierte Embeddings bzw. OpenAI-Antworten. Sie benötigen weder API-Guthaben noch
Modelldownloads. Ein einzelner Worker vermeidet mehrere Kopien des großen E5 im
RAM; Inferenz ist pro Worker gesperrt. `warmup` sollte vor dem Serverstart erfolgen.
Auf diesem Mac läuft die lokale Webseite mit `.venv/bin/python app.py`. Beim
Gunicorn-Start mit MPS brach ein Worker wegen der macOS-Initialisierung nach
`fork()` ab. Der lokale Flask-Start vermeidet diesen Prozesswechsel; Gunicorn
bleibt die vorgesehene Deployment-Option auf einem geeigneten Server.

Der lokale Start lädt E5 jetzt vor dem Öffnen des HTTP-Ports und führt eine kurze
Probe-Inferenz aus. Dabei entstehen keine GPT-Anfragen und kein neuer
Dokumentindex. Auf dem Docker-Server übernimmt die Vorladung bereits der
Gunicorn-Worker. Das reduziert den Kaltstart bei der ersten Suche, nicht die
Zeit für das Erzeugen der GPT-Bewertungen und Begründungen.

Vor den ersten Ergebnissen erhält das rechte Eingabeformular standardmäßig
60 % der Arbeitsfläche (höchstens 800 Pixel; links bleiben mindestens 400 Pixel).
Die Trennlinie bleibt bedienbar. Nach der Suche wird die separat gespeicherte
Chatbreite verwendet. Auf schmalen Geräten bleibt die einspaltige Ansicht bestehen.

Dies ist ein lokaler Prototyp. Für den Zugriff auf eine Suchsitzung wird zusätzlich die zugehörige aktive Einwilligung geprüft. Für öffentliches
Deployment fehlen insbesondere Benutzeranmeldung, Zugriffskontrolle und
Rate-Limits. CORS ist auf die konfigurierten lokalen React-Ursprünge begrenzt.
Profile, CV-Ausschnitte und die Kandidatentexte werden zur Auswertung an OpenAI
gesendet; API-Schlüssel und unbereinigte Quelldatensätze werden nicht übertragen.
`store=False` bedeutet keine durch die App angeforderte Speicherung der Response;
es ist keine Zusage zur vollständigen Datenlöschung beim Anbieter.

## Dateien

- `app.py`: Flask-App-Factory, API-Routen, Pipeline-Orchestrierung und CLI.
- `data_store.py`: Originalformat, HTML-Bereinigung, SQLite, Import und Filter.
- `retrieval.py`: BM25, tatsächliches E5, Vektorcache und RRF.
- `llm_service.py`: Persona, Gesprächsänderungen und geprüftes JSON-Reranking.
- `advisor.py`: vorgegebene und individuelle DIANA-Persönlichkeiten.
- `schemas.py`, `session_store.py`: Eingabeschemata und zeitlich begrenzte RAM-Sitzungen (SQLite-Store nur für Legacy-/Testfälle).
- `dummy_jobs.json`: fünf eindeutig fiktive Anzeigen im Originalformat.
- `requirements.txt`, `requirements-dev.txt`: festgelegte direkte Abhängigkeiten.
- `.env.example`, `example_search.json`: Konfiguration und fertige API-Anfrage.

## React weiterentwickeln

Das fertige Frontend liegt in `web-dist/` und wird direkt durch Flask unter `/`
ausgeliefert. Der Browser bekommt keinen API-Schlüssel. Quelldateien liegen in
`frontend/`; nach Änderungen `pnpm build` ausführen. `pnpm dev` startet optional
einen Vite-Entwicklungsserver auf Port 5173 mit Proxy zum bestehenden Backend.

Die Frontend-Integration verwendet einen statischen Vite-Build mit Flask als
Server: [Vite Backend Integration](https://vite.dev/guide/backend-integration).

Für den vollständigen, wiederaufnehmbaren Indexaufbau auf diesem Mac:

```bash
.venv/bin/python build_index.py --database instance/real-jobs.sqlite3 --device mps --batch-size 16
```

`REQUIRE_COMPLETE_INDEX=true` verhindert teure Suchanfragen während der
Vorbereitung. `GET /api/index-status` meldet den Fortschritt. Der Build speichert
Vektoren in kleinen Blöcken, sodass eine Unterbrechung bereits berechnete
Anzeigen nicht verliert.

### Historische Änderung: Chat vor der Rückmeldung · 10.09.2026

Der eingebettete DIANA-Chat meldet eine bestätigte Nutzernachricht als reines
Fortschrittssignal, ohne den Nachrichtentext zu übertragen. Quelle, Ursprung und
Umfragelauf werden geprüft. Der Fortschritt bleibt für diesen Browserlauf erhalten;
die Ja/Nein-Selbstauskunft wird dadurch nicht automatisch ausgefüllt. Die frühere
Filterführung und gespeicherte Antworten bleiben erhalten. Diese Änderung macht
Chatnutzung zur Voraussetzung für die Rückmeldung; beim Vergleichen früherer und
späterer Teilnahmen den jeweiligen Systemstand berücksichtigen.

Im Wartezeit-Dialog steht „Zurück zum System“ links als dezenter Button; die weitere
Fragegruppe rechts als hervorgehobener Button. „Wartezeit nutzen“ verwendet ebenfalls
die Wellenanimation. Der Hinweis zur Teilnahme-ID nennt die anklickbare Kontaktadresse.

### Historische Änderung: Automatisches Speichern und Zwischenfragen · 10.09.2026

`PUT /api/survey-drafts` sichert den vollständigen aktuellen Antwortentwurf mit einer
monotonen Revision. Serverbestätigungen, Wiederholungen, Reihenfolge und konkurrierende
Speicheranfragen werden geprüft. `GET /api/survey-drafts/<submission_id>` liefert nur den
eigenen Entwurf nach Einwilligung. Kein Profil oder Chattext wird dabei übertragen.
Auswahlwerte werden nach Eingabe gesichert; Text wird kurz gebündelt. Bei Netzfehlern
bleibt der Browserentwurf erhalten und die Oberfläche bietet einen erneuten Versuch.
Noch nicht bestätigte Antworten sind nicht garantiert auf dem Server gespeichert.

Entwürfe stehen in `survey_drafts`, abgeschlossene Antworten in `survey_responses`.
Der Abschluss entfernt den Entwurf atomar; spätere Autosaves können ihn nicht wieder
anlegen. Die Verwaltung zeigt beide mit `response_status` (completed / in_progress),
Statusfilter und `last_saved_at_utc`. In Numiqo unvollständige Teilnahmen bewusst
separat auswerten; bei noch nicht beantworteten Pflichtfragen steht `unanswered`.
Der ältere lesbare CLI-Export bleibt auf abgeschlossene Antworten beschränkt.
Widerruf, administrative Löschung und Studienende erfassen auch Entwürfe.

Im eingebetteten System rendert die Umfrageseite das Warte-Popup. Dort öffnet der
animierte Button „Fragen in der Zwischenzeit beantworten“ die noch offenen Vorabfragen.
Das Fragenfenster hat rechts oben ein Schließen-Kreuz und „Weitere Fragen“ für den
nächsten Block. Nach dem letzten beantworteten Block schließt es nach bestätigtem
Speichern automatisch. Das Warte-Popup bleibt während der Berechnung sichtbar, ohne
den Fragenbutton, wenn nichts mehr offen ist. Der Button für den nachgelagerten
Fragebogen ist während Suche und Zwischenfragen ausgeblendet. Bereits beantwortete
Vorabfragen und leere dadurch erledigte Kategorien werden später übersprungen.

Die Datenschutzhinweise nennen ausdrücklich das fortlaufende Speichern auch bei
Abbruch. Eine vorhandene Teilnahme kann den geänderten Hinweis ausdrücklich erneut
akzeptieren; ihre ID bleibt erhalten, der frühere Einwilligungswortlaut wird archiviert.
Ein bereits widerrufener Zugang bleibt gesperrt.


## Direkte Tests ohne Umfrage

`/test/a` öffnet die feste Standardberatung, `/test/b` die Auswahl aus festen Vorlagen und `/test/c` zusätzlich die eigene Gestaltung. Alle drei zeigen Scores und Begründungen entsprechend dem aktuellen V9-System. Die Zugänge benötigen eigene Einwilligungen und halten Chat und Profil nur in temporären Sitzungen. Sie erzeugen weder Studienzuteilungen noch Umfrageantworten oder Einträge in der Studienauswertung. Die Studienfreigabe in der Verwaltung betrifft diese separaten Tests nicht; vollständige Datenschutzeinstellungen sind weiterhin erforderlich. A, B, C und Umfrage haben getrennte Browser- und Serversitzungen.

Eingebaute Persönlichkeiten liegen als versionierte `.mlds`-Dateien in `personas/`. Das Frontend lädt sie aus `/api/persona-templates`; individuelle Konfigurationen werden in der Sitzung als `advisor_mlds` abgelegt. Siehe [MLDS.md](MLDS.md).

Einzelantworten können unter `/verwaltung` über **Einzelantworten → Ansehen → Antworten bearbeiten** mit Korrekturgrund geändert werden. Ursprungswerte und Änderungsverlauf bleiben erhalten. Details zu Exporten und Korrekturen: [ADMIN.md](ADMIN.md).
