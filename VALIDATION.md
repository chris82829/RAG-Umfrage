# Validierung am 09.09.2026

Laufzeit: Python 3.12.14, lokale isolierte `.venv` auf macOS ARM64.

Aktuelle Änderung: Git-Repository für die Übergabe an
`https://github.com/chris82829/RAG-Umfrage` eingerichtet, Branch `main`.
Die README enthält einen Einstieg für einen frischen Clone einschließlich
Frontend-Build und lokaler Konfiguration. `.gitignore` schützt API-Schlüssel,
Datenbanken, Sitzungen, Modell-Caches, Abhängigkeiten, generierten Frontend-Build,
macOS-Metadaten und Logs. 62 vorgesehene Quelldateien, Assets und Dokumentationen
auf enthaltene lokale Schlüssel und gängige Zugangsdatenmuster geprüft; kein Fund.
Die fünf fiktiven Beispielstellen und synthetischen Evaluationsberichte sind enthalten.

**433 Python-Tests bestanden, 1 optionaler Test übersprungen; 61 Frontend-Tests
bestanden.** Der zuvor geprüfte Produktionsbuild bleibt unverändert.
Keine Änderung am laufenden Server, keine Modellaufrufe oder Browserprüfung.

Vorangegangene Änderung: Aktionsschalter und Ergebnisstatus teilen sich eine kompakte,
44 Pixel hohe Zeile. Der Schalter heißt sichtbar „Aktionen“; „Jobs neu sortieren“
und „Neu starten“ bleiben zunächst eingeklappt. Ein React-Disclosure mit eindeutigem
`aria-controls`, `aria-expanded` und `hidden` bewahrt Tastaturbedienung und setzt
seinen Zustand beim Sitzungswechsel zurück. Alle Aktions-/Hinweisbedingungen bleiben
erhalten. Der Live-Status ist ein eigenständiges, dauerhaft vorhandenes Element und
wird während laufender Anfragen geleert. Die frühere separate grüne Statusleiste
und ihre mobilen Abstände sind entfernt.

Redundante Wörter in Antwort-/Rerank-Rückmeldungen gekürzt. Lange Statusangaben bleiben
einzeilig mit Ellipse; vollständiger Text bleibt für assistive Technik und im Titel
verfügbar. **61 bestehende Frontend-Tests bestanden**, bestehende Textassertions an
die kürzeren Formulierungen angepasst. Produktionsbuild erfolgreich; unabhängiger
statischer Review ohne Befunde. Suchseite und aktuelle Assets per HTTP geprüft,
ausgelieferte Dateien stimmen mit dem Build überein. Keine neuen Tests,
Backendänderungen oder Browserprüfung für diese Oberflächenänderung.

Vorangegangene Änderung: „Stellendetails“ und „Mit … besprechen“ stehen in einer
kompakten gemeinsamen Aktionszeile. Das Details-Panel öffnet sich darunter über die
volle Kartenbreite. Zwei getrennte Buttons bewahren unabhängige Bedienung; der
Chat-Button bleibt während laufender Anfragen gesperrt. Das Details-Disclosure nutzt
lokalen Zustand, eindeutige ID, `aria-expanded`, `aria-controls` und `hidden`.

Containerqueries kürzen bei schmalen Karten (auch in der verstellbaren Desktop-
Spalte) die Chatbeschriftung zu „Besprechen“ und bei noch weniger Platz die andere
Beschriftung zu „Details“. Der vollständige Persönlichkeitsname bleibt im zugänglichen
Namen und Titel des Chat-Buttons enthalten. Lange freie Namen erhalten eine Ellipse;
44-Pixel-Touchhöhe, Fokusdarstellung und reduzierte Bewegung berücksichtigt.
Alte, jetzt ungenutzte Footer-Styles entfernt; andere Filter-Details bleiben erhalten.

**61 bestehende Frontend-Tests bestanden**, Produktionsbuild erfolgreich.
Unabhängiger statischer Review ohne konkrete Befunde. Suchseite und aktuelle Assets
per HTTP geprüft, Dateien stimmen mit dem Produktionsbuild überein. Keine neuen
Tests, Backendänderungen oder Browserprüfung für diese Oberflächenänderung.

Vorangegangene Änderung: „NACH PERSÖNLICHER PASSUNG SORTIERT“ aus der Ergebnisansicht
entfernt. Die bestehende Score-Bezeichnung bleibt rechts ausgerichtet.
Produktionsbuild erfolgreich; Suchseite und aktuelle Assets per HTTP geprüft.
Der entfernte Text ist im ausgelieferten Build nicht mehr enthalten. Keine neuen
Tests, Backendänderungen oder Browserprüfung für diese reine Textentfernung.

Vorangegangene Änderung: „Weniger anzeigen“ steht nach allen zusätzlichen Gründen und
Fähigkeiten ganz unten in der Begründungsbox. Ein React-Disclosure mit unverändert
gekeytem Zustand ersetzt dort den nativen Details-Bereich; der Toggle bleibt im
DOM hinter dem Inhalt und behält beim Öffnen/Schließen seinen Fokus. Der wichtigste
Stichpunkt bleibt sichtbar. Zusätzlicher Inhalt ist anfangs per `hidden` verborgen;
eindeutige IDs, `aria-controls`, `aria-expanded`, Tastaturbedienung, 44-Pixel-Touchhöhe
und reduzierte Bewegung bleiben berücksichtigt. Keine Auswirkung auf Stellendetails
oder ausklappbare Chatnachrichten.

**61 bestehende Frontend-Tests bestanden**, Produktionsbuild erfolgreich.
Unabhängiger Quelltextreview ohne konkrete Regressionsbefunde. Suchseite und aktuelle
Assets per HTTP geprüft; ausgelieferte Dateien stimmen mit dem Build überein.
Keine neuen Tests, Backendänderungen oder Browserprüfung für diese UI-Änderung.

Vorangegangene Änderung: Markenname durchgehend „DIANA Jobsuche“, Forschungsprojekt
und Anleitung ebenfalls „DIANA“. Kopfzeile, Infoseite, Seitentitel, Metabeschreibung,
zugängliche Beschriftungen und README aktualisiert. Produktionsbuild erfolgreich;
Startseite, Suchseite und aktuelle Assets per HTTP geprüft. Der ausgelieferte Build
enthält keine gemischte Schreibweise „Diana“. Unabhängiger Quelltextreview ohne
weitere Produktfundstellen. Keine neuen Tests, Backendänderungen oder Browserprüfung
für diese reine Textänderung; kein Serverneustart notwendig. Historische Zitate in
älteren Validierungseinträgen bleiben als damalige Bezeichnungen erhalten.

Vorangegangene Änderung: deutlichere Persönlichkeitsstile in Chatantworten, proaktiver
Suchansprache und Stellenbegründungen, einschließlich des ersten sichtbaren Grunds.
Feste Presets erhalten getrennte Sprach- und Entscheidungsregeln sowie kurze,
fiktive Stilbeispiele. Diese sind keine echten Zitate oder Stellenbelege. Kritischer
Ton darf keine zusätzlichen Voraussetzungen oder Nutzerwünsche erfinden; sachliche
Passung und bestehende Bewertungsgewichte haben Vorrang. Benutzerdefinierte Namen,
Eigenschaften und Freitext bleiben als nicht vertrauenswürdige Daten abgegrenzt.
Ein berühmter Name als eigenes Label aktiviert keine zusätzlichen Preset-Regeln.

Neue Assistentennachrichten speichern den tatsächlich verwendeten `advisor_name`;
ein späterer Persönlichkeitswechsel benennt diese alten Antworten nicht mehr um.
Legacy-Nachrichten bleiben unverändert und verwenden das bisherige Fallback-Label.
Neutrale Systemmeldungen bleiben kurz und fest vorgegeben. Keine zusätzlichen
Modellaufrufe im produktiven Ablauf, keine Modell-, Score- oder Cacheänderung.

**433 Python-Tests bestanden, 1 optionaler Test übersprungen; 61 Frontend-Tests
bestanden.** Produktionsbuild erfolgreich. Abgedeckt sind alle Promptpfade,
Preset-/Custom-Grenzen, Nachrichtenattribution, Persönlichkeitswechsel sowie
bestehende Bewertungs- und Sitzungsgarantien. Unabhängiger Quelltextreview erfolgt.

Zwei gültige Live-Vergleichsrunden mit GPT-5.4: je fünf Persönlichkeiten, je
Suchbegründung und Chatantwort, insgesamt 20 Aufrufe mit ausschließlich fiktivem
Profil und drei fiktiven Stellen. Alle gültigen Ausgaben erfüllten Schema und
Längenlimits; die Beratungsfrage änderte kein Profil und löste keine Suche aus.
Bei identischen Bewertungsgrundlagen blieben Scores und Komponenten zwischen den
Runden gleich. Der unabhängige Blindreview der zweiten Runde konnte alle fünf
Stile zuordnen und bewertete sie als professionell und besser unterscheidbar.
DIANA und Günther überschneiden sich teilweise; Angela formuliert förmlicher und
ausführlicher. Kleine qualitative Stichprobe, keine allgemeine Qualitätsgarantie.
Ein ausgeschlossener Vorbereitungslauf mit fehlerhaftem Evaluationsprüfcode ist
transparent dokumentiert. Vollständige gültige Beispiele und Methodik stehen in
`personality-style-evaluation.md` und `personality-style-evaluation.json`.
Lokalen Server nach Abschluss der laufenden Anfrage im Leerlauf neu gestartet.
Health, vollständiger Index (8.537 Stellen), Suchseite und aktuelle Assets per
HTTP geprüft; ausgelieferte Assets stimmen exakt mit dem Produktionsbuild überein.
Keine Browserprüfung für diese Änderung.

Vorangegangene Änderung: „Warum das passen könnte“ zeigt pro Stelle zunächst nur
den ersten Stichpunkt. Weitere Gründe und passende Fähigkeiten liegen in einem
anfangs geschlossenen nativen Details-Bereich mit „Mehr anzeigen“/„Weniger anzeigen“.
Neue Scores, Gründe oder Fähigkeiten setzen die Klappansicht zurück; identische
Daten bei reinen Chatantworten erhalten sie. Legacy-Begründung bleibt unterstützt;
bei nur einem Grund ohne weitere Fähigkeiten entfällt der Toggle. Mobile Umbrüche,
44-Pixel-Touchfläche, Tastaturfokus und reduzierte Bewegung berücksichtigt.

Die gemeinsame LLM-Regel für frische und gecachte Bewertungen verlangt zuerst den
wichtigsten sachlichen Entscheidungsgrund, vorrangig fachliche Passung oder eine
entscheidende fachliche Muss-Lücke. Bestehende Gründe werden nicht neu berechnet.
Keine Schema-, Score- oder Cacheänderung und kein kostenpflichtiger Modellaufruf.
**156 bestehende LLM-Tests bestanden**, Produktionsbuild erfolgreich. Unabhängiger
Quelltextreview ohne wesentlichen Befund; geschlossene Darstellung im Quelltext
geprüft. Lokalen Server im Leerlauf neu gestartet; Health, Index, Suchseite und
aktuelle Assets per HTTP geprüft. Keine neuen Tests oder Browserprüfung.

Vorangegangene Änderung: die KI-Beratung verwendet den Namen der gewählten
Persönlichkeit mit „-KI“, beispielsweise „Angela-Merkel-KI“ oder „Alex-Weber-KI“.
Frontend und Backend normalisieren Leerraum zu Bindestrichen und hängen ein
bereits vorhandenes KI-Suffix nicht doppelt an. Chat-Absender, Stellenkarten,
Formularhinweise, zugängliche Beschriftungen und Such-Popup nutzen den Namen;
Anfrageanzeigen verwenden die tatsächlich übermittelte Persönlichkeit. Entwürfe
benennen gespeicherte Ergebnisse nicht um. Alte Nachrichtentexte bleiben erhalten,
die sichtbaren Labels folgen der angewendeten Persönlichkeit.

Beide LLM-Gesprächspfade erhalten den aktuellen Anzeigenamen als nicht
vertrauenswürdige JSON-Daten; feste DIANA-Selbstbezeichnungen sind entfernt.
Die KI behauptet keine reale Personenidentität. Bestehende Raw-Konfiguration,
Scores, Gewichte und Caches bleiben unverändert; kein kostenpflichtiger Liveaufruf.

**402 Python-Tests bestanden, 1 optionaler Test übersprungen; 61 Frontend-Tests
bestanden.** Abgedeckt sind Presets, eigene Namen, KI-Suffix, Konfigurations-
kompatibilität, Trennung von Namen und Anweisungen sowie unveränderte Bewertungen
aller 20 Kandidaten bei einer reinen Umbenennung. Produktionsbuild erfolgreich,
unabhängiger Quelltextreview ohne verbleibenden Befund. Lokalen Server im Leerlauf
neu gestartet; Health, vollständiger Index und aktuelle Assets per HTTP geprüft.
Keine Browserprüfung.

Vorangegangene Änderung: unter „Weitere Aktionen“ die Buttons „Suchprofil“ und
„Besprechen & verfeinern“ entfernt. „Jobs neu sortieren“ und „Neu starten“ bleiben
mit ihren bisherigen Aktionen und Sperrbedingungen nebeneinander erhalten.
Ungenutzte Profilbutton-Styles entfernt; Bedienungsdokumentation aktualisiert.
Unabhängiger Quelltextreview bestätigt verbleibende Profil- und Chat-Zugänge
auch mobil und das bestehende Zweispaltenlayout. Produktionsbuild erfolgreich;
Suchseite und aktuelle Assets liefern HTTP 200 und stimmen mit dem Build überein.
Keine Backendänderung, neuen Tests, Modellaufrufe oder Browserprüfung für diese
kleine Oberflächenänderung.

Vorangegangene Änderung: den blauen Verarbeitungs-/Ladestatus mit Zeitangabe über
der Stellenliste samt ungenutzten Styles entfernt. Die Fortschrittsanzeige im Chat
und das Popup bei vollständigen Suchen bleiben erhalten. Produktionsbuild erfolgreich;
Suchseite und aktuelle Assets per HTTP geprüft, entfernte Statuskomponente im
Build nicht mehr enthalten. Keine Backendänderung, neuen Tests, Modellaufrufe
oder Browserprüfung für diese Darstellungsänderung.

Vorangegangene Änderung: den Hinweis „KI-Empfehlungen können sich irren. Prüfe die
Stellenbeschreibung.“ unter dem Chatfeld samt ungenutzten Styles entfernt.
Produktionsbuild erfolgreich; Suchseite und aktuelle Assets per HTTP geprüft,
entfernter Text im ausgelieferten Build nicht mehr vorhanden. Keine Backendänderung,
neuen Tests, Modellaufrufe oder Browserprüfung für diese Textentfernung.

Vorangegangene Änderung: breite Filter-/Wunsch-Chips über der Ergebnisliste durch
kompakten Filter-Button neben der Überschrift mit nativem Popover ersetzt.
Hover öffnet ohne Fokuswechsel; Klick hält offen, Enter/Leertaste fokussieren den
Schließen-Button. Escape, Schließen, Fokus außerhalb und Klick außerhalb schließen
es. Touch nutzt denselben Button. Gespeicherte Stellenart und weiche Wünsche bleiben
getrennt; alle Stellenarten werden zusammengefasst. „Suchprofil bearbeiten“ nutzt
die bestehende Navigation mit Entwurfserhalt. Popup liegt im Toplayer, passt seine
Position und Größe an den sichtbaren Viewport an und scrollt lange Inhalte intern.
Bereichswechsel, neue Sitzung, Rückkehr zur Info-Seite oder laufende Anfrage schließen
es. Ungenutzte Styles der bisherigen Übersicht entfernt.

Produktionsbuild und **60 bestehende Frontend-Tests erfolgreich**. Suchseite und
aktuelle Assets liefern HTTP 200; ausgelieferte Dateien stimmen mit dem Build
überein. Integration, Tastatur-/Touch-Behandlung und mobile CSS-Regeln im Quelltext
geprüft. Keine neuen Tests, Backendänderungen, Modellaufrufe oder Browserprüfung.

Vorangegangene Änderung: den zusätzlichen Chat-Hinweis zu ausgeblendeten niedrigen
Scores entfernt. Der Hinweis und Einblendebutton unter der Jobliste bleiben
erhalten. Produktionsbuild und ausgelieferte Assets geprüft; keine Backendänderung,
neuen Tests oder Modellaufrufe für diese Textentfernung.

Vorangegangene Änderung: die drei erklärenden Schritt-Hinweiszeilen im rechten Bereich
für Profil, Persönlichkeit und Chat samt ungenutzter Styles entfernt.
Schrittanzeige oben, Formulare, Chat sowie echte Lade-, Fehler- und Ergebnisstatus
bleiben erhalten. Produktionsbuild erfolgreich, aktuelle Webseite und Assets per
HTTP geprüft. Keine Backendänderung, neuen Tests, Modellaufrufe oder Browserprüfung
für diese Textentfernung.

Vorangegangene Änderung: „Mehr erfahren“-Button und „DU“-Profilkreis aus der Kopfzeile
entfernt. Ein gemeinsamer Innenbereich ordnet Logo, Schrittanzeige und Stellenzahl
auf breiten Bildschirmen links, mittig und rechts an. Auf schmalen Bildschirmen
stehen Logo und Schritte platzsparend nebeneinander; die Stellenzahl wird bei
knappem Platz ausgeblendet. Die Info-Startseite bleibt über das Logo erreichbar.
Produktionsbuild und aktuelle Assets per HTTP geprüft; responsive Breiten und
CSS-Spezifität im Quelltext geprüft. Keine Backendänderung, neuen Tests,
Modellaufrufe oder Browserprüfung für diese Layoutänderung.

Vorangegangene Änderung: der Hinweis auf weitere, niedriger bewertete Stellen mit
Einblendebutton steht unter der Jobliste. Abstand an die neue Position angepasst;
beim Einblenden wird die erste zusätzliche Kartenüberschrift fokussiert und die
Karte sichtbar gescrollt. Beim Ausblenden bleibt der Fokus am Button.
Scoregrenze und gespeicherte Ergebnisse unverändert. Produktionsbuild erfolgreich,
aktuelle Webseite und Assets per HTTP geprüft. Keine Backendänderung, neuen
Tests, Modellaufrufe oder Browserprüfung für die Positionsänderung.

Vorangegangene Änderung: die Anzahl-/Filterzeile unter der Ergebnisüberschrift entfernt.
Überschrift, Jobkarten, Score-Sichtbarkeit und Suchlogik bleiben erhalten.
Produktionsbuild erfolgreich; aktuelle Webseite und Assets per HTTP geprüft.
Keine Backendänderung, neuen Tests, Modellaufrufe oder Browserprüfung für diese
kleine Textentfernung.

Vorangegangene Änderung: die rechte Tab-Leiste mit „Suchprofil“, „Persönlichkeit“ und
„Besprechen“ samt eigener CSS-Datei entfernt. Kopfzeilen-Icons, eingeklappte
weitere Aktionen und Formulare bleiben erhalten. Navigation und mobile Zugänge
im Quelltext geprüft; Produktionsbuild erfolgreich, aktuelle Webseite und Assets
liefern HTTP 200. Keine Backendänderung, neuen Tests, Modellaufrufe oder
Browserprüfung für diese kleine Darstellungsänderung.

Vorangegangene Änderung: GPT-Latenz reduziert durch Wiederverwendung unveränderter
Suchpersonas, schlankere Ausgabe bei festen Teilbewertungen, exakte Deduplikation
von Jobtexten und geringeren Reasoning-Aufwand ausschließlich für Begründungen
bei gültigem Bewertungscache. Erstbewertung, Persona und Chatplanung bleiben bei
GPT-5.4 mit `medium`; gecachte Begründungen verwenden `low`. Alle 20 Ergebnisse,
Fachpassungsregeln, Gewichte und unveränderbare Komponenten bleiben erhalten.

- **376 Python-Tests bestanden, 1 optionaler Test übersprungen**. Darunter
  vollständiger Profil-Fingerprint, Weitergabe des ursprünglichen Persona-Stands
  nach weichem Rerank, Legacy-/Versions-/Neustartfälle, frisches Retrieval trotz
  wiederverwendeter Persona, strikte Cache-Ausgabeschemas, ID-Abdeckung aller 20
  Stellen, unveränderte Scores, verlustfreie Textreferenzen und private Logs.
- Kontrollierter Livevergleich mit 20 fiktiven Stellen und bereits validierten
  festen Teilbewertungen: bisher **27,645 s**, kompakter Cache-Pfad mit `medium`
  **28,704 s**, endgültiger Cache-Pfad mit `low` **17,994 s**. Gegenüber der
  Ausgangsvariante **34,9 % kürzere Laufzeit** und **44,7 % weniger Ausgabetokens**
  (3.737 → 2.065, einschließlich Reasoning). Alle 20 Scores und Komponenten
  blieben gleich; je 2–3 gültige Gründe, Beispiele fachlich geprüft.
- Dies sind drei Einzelmessungen, keine garantierte Produktionslatenz und keine
  umfassende Qualitätsstudie. Ein früherer Vorbereitungslauf mit falsch benanntem
  synthetischem Cache-Feld wurde aus dem Vergleich ausgeschlossen. Die initiale
  Vollsuche wurde nicht erneut live gemessen. Rohmetriken: `latency-benchmark.json`.
- Neue Suchen mit unverändertem Profil benötigen nach gültiger Persona-Speicherung
  einen GPT-Aufruf weniger; die erstmalige Suche weiterhin zwei. Tests belegen
  die Aufrufzahl, ohne Nutzersitzungen oder Kontingente dafür zu verwenden.
- Server ohne aktive Anfrage neu gestartet. Webseite, Health-Check und fertiger
  Suchindex liefern HTTP 200. Keine UI-Änderungen oder Browserprüfung. Phasen-
  und GPT-Laufzeiten werden ohne vertrauliche Inhalte protokolliert.

Vorangegangene Änderung: die vier rechten Aktionsbuttons befinden sich in einem
anfangs geschlossenen nativen `details`-Bereich „Weitere Aktionen“. Die drei
Navigationstabs bleiben sichtbar. Klick und Tastatur öffnen bzw. schließen den
Bereich; ein gedrehter Pfeil zeigt den Zustand. Die Zusammenfassung bleibt über
dem bei Bedarf scrollbar begrenzten Inhalt erreichbar. Neue Sitzungen starten
geschlossen; Tabwechsel und Antworten erhalten den Klappzustand. Produktionsbuild
und ausgelieferte Assets per HTTP geprüft, HTML-/CSS-Verträge im Quelltext geprüft.
Keine Backendänderung, neuen Tests, Modellaufrufe oder Browserprüfung für diese
kleine Darstellungsänderung.

Vorangegangene Änderung: die kompakte Schrittanzeige in der obersten Kopfzeile erscheint
erst mit einer Ergebnissitzung. Vorher dient die ausführliche Anleitung zur
Orientierung; der Einstieg, beide Formulare und die erste laufende Suche blenden
keine zusätzlichen Kopfzeilen-Icons ein. Zurückgesetzte Suchen verbergen die
Anzeige, wiederhergestellte Suchen zeigen sie auch bei niedrigen Scores oder
Nulltreffern. Bedingung im Quelltext geprüft, Produktionsbuild erfolgreich;
aktuelle Seite und Assets per HTTP geprüft. Backend unverändert, keine neuen
Modellaufrufe, kein Neustart und keine Browserprüfung.

Vorangegangene Änderung: die bisherige Begrenzung der öffentlichen Ergebnisse auf fünf
Karten ist entfernt. Alle bis zu 20 Kandidaten behalten ihre vollständigen
Bewertungen und Begründungen. Die Oberfläche zeigt sämtliche Stellen ab 70 Punkten
direkt; niedrigere Scores bleiben über einen Button mit Anzahl einblendbar.
Der Chat erhält ebenfalls bis zu 20 bewertete Stellen als Kontext.

- **321 Python-Tests bestanden, 1 optionaler Test übersprungen**. Regressionen
  prüfen vollständige 20er-Ergebnisse auch bei gecachten Bewertungen, korrekte
  Sortierung und Chatkontext bis zur 20. Stelle. Die API erhält alle Karten nach
  Neustart, Antwort und Neubewertung; Kandidatenpool und Bewertungscache bleiben
  privat. Frühere Sitzungen mit fünf Karten werden erst bei einer normalen
  Neubewertung ergänzt, nicht durch GET oder eine reine Chatfrage.
- **60 Frontend-Tests bestanden**, Produktionsbuild erfolgreich. 20 gute Scores
  zeigen 20 Karten; sieben Scores ab 70 zeigen sieben Karten; Einblenden liefert
  alle 20 unverändert. Grenzwert 70, Rückkehr zur gefilterten Ansicht, Reihenfolge
  und Erhalt der Anzeigeentscheidung bei Chatantworten geprüft. Ein Hinweis
  erklärt bei älteren Sitzungen die einmal nötige Neubewertung.
- Lokaler Server ohne aktive Anfrage neu gestartet. `/suche`, aktuelle Assets,
  Health-Check und fertiger Suchindex liefern HTTP 200. Keine Browserprüfung
  oder echten Modellaufrufe für diese Änderung.

Vorangegangene Änderung: alle vier bisherigen Ergebnisaktionen stehen rechts unter
den Navigationstabs in einem Raster mit zwei Spalten. Der zugehörige Hinweis
auf eine notwendige neue Suche ist ebenfalls rechts. Der doppelte Sortierbutton
unter dem Chatfeld entfällt. Mobil führt ein rechtsbündiger Button in einer
eigenen Fußzeile aus der Ergebnisansicht zu Profil und Chat, ohne Karten zu
überdecken oder die Rücksprungregeln der Schrittanzeige zu ändern.

- **59 Frontend-Tests bestanden**, Produktionsbuild erfolgreich. Bestehende
  Aktions-, Entwurfs- und Navigationsregeln weiterhin geprüft. Platzierung,
  Lade-Sperren, mobile Erreichbarkeit auch ohne sichtbare Jobs sowie Flex-/Scroll-
  Verhalten zusätzlich im Quelltext geprüft; keine Browserprüfung.
- `/suche` und aktuelle JavaScript-/CSS-Assets liefern HTTP 200. Im ausgelieferten
  Build steht die Aktionsgruppe im rechten Bereich; der alte Ergebnisbereich
  und Chatfuß enthalten keine doppelten Aktionsleisten.
  Backend unverändert; kein Server-Neustart oder zusätzlicher Modellaufruf.

Vorangegangene Änderung: drei rechte Navigationstabs „Suchprofil“, „Persönlichkeit“ und
„Besprechen“. Die bisherige zusätzliche Schrittleiste ist durch vier kompakte
Schaltflächen mit Icons und Nummern in der obersten Kopfzeile ersetzt. Der
aktuelle Schritt bleibt hervorgehoben; erledigte Schritte tragen ein Häkchen.
Die ausführliche Anleitung vor der ersten Suche bleibt erhalten.

- **59 Frontend-Tests bestanden**, Produktionsbuild erfolgreich. Bestehende
  Reihenfolge- und Rücksprungregeln weiterhin geprüft. Tabwechsel, Erhalt von
  Entwürfen, erneuter Klick auf den aktiven Formular-Tab, Lade-Sperren und
  zugängliche Beschriftungen zusätzlich im Quelltext geprüft.
- Mobile Tabs bleiben sichtbar; Kopfzeile verwendet bei schmalen Bildschirmen
  vier 44-Pixel-Schaltflächen in einer Reihe. CSS-Breiten und Spezifität geprüft,
  keine Browserprüfung für diese Änderung.
- `/suche` und aktuelle JavaScript-/CSS-Assets liefern HTTP 200. Ausgelieferter
  Build enthält die neue Navigation und keine separate Schrittleiste mehr.
  Backend unverändert; kein Server-Neustart oder zusätzlicher Modellaufruf.

Vorangegangene Änderung: optionales Freitextfeld „Eigene Beschreibung“ für selbst
gestaltete Persönlichkeiten, maximal 2.000 Zeichen mit Zeichenzähler. Beschreibung
wird getrimmt validiert, gespeichert und an beide LLM-Pfade als strukturierter
Stil-/Begründungswunsch übergeben. Sie verändert keine Profilangaben, Fakten,
Gewichte oder gespeicherten Teilbewertungen. Vorbilder ignorieren den Freitext.

- **317 Python-Tests bestanden, 1 optionaler Test übersprungen**: Grenzen und
  ungültige Datentypen, Persistenz über Neustart, Legacy-Konfigurationen,
  reine Textänderung als Neubewertung ohne Retrieval sowie Weitergabe an Chat
  und Reranking. Beschreibung bleibt außerhalb der Systemanweisungen;
  Komponenten-Cache und Scores bleiben bei reinen Textänderungen stabil.
- **59 Frontend-Tests bestanden**, Produktionsbuild erfolgreich. Validierung,
  Leer-/Altwerte, Beschreibungslimit, Erkennung nicht angewendeter Änderungen
  und Wechsel zu Vorbildern geprüft. Keine Browserprüfung oder echten
  Modellaufrufe für diese Änderung.
- Server ohne aktive Anfrage neu gestartet. Webseiten und aktuelle Assets per
  HTTP erreichbar. Mit absichtlich fehlendem Profil den aktiven Datenvertrag
  geprüft: gültige Beschreibung zulässig, Überlänge abgewiesen; keine neue
  Suche oder Sitzung angelegt.

Vorangegangene Änderung: die bisherige Informationsseite ist die Startseite unter `/`
und `/index.html`; `/mehr-erfahren` bleibt als Alias erhalten. Die Jobsuche liegt
unter `/suche`. „Jobsuche starten“ steht als großer blauer Link rechts neben dem
Projekttext, mobil direkt darunter; der alte Zurück-Button entfällt.
Inhalte, Bild und Kontakte unverändert. Browsernavigation, direkte URLs und der
Wechsel ohne Verlust von Profilentwürfen, Chat und Ergebnissen berücksichtigt.

- **7 gezielte Backend-Tests bestanden**: Direktaufruf und Neuladen der vier
  Webseitenrouten, unveränderte API-Antworten und 404 für unbekannte API-Routen.
- **58 Frontend-Tests bestanden**, Produktionsbuild erfolgreich. Navigation,
  Fokusziele, echte Links und mobile CSS-Regeln im Quelltext geprüft.
  Keine Browserprüfung oder zusätzlichen Modellaufrufe für diese Änderung.
- Lokaler Server ohne aktive Anfrage neu gestartet. `/`, `/index.html`, `/suche`
  und `/mehr-erfahren` sowie aktuelle Assets und Health-Check liefern HTTP 200.
  Neuer Seitentitel und Startseiten-CTA sind im ausgelieferten Build enthalten.

Vorangegangene Änderung: Chat-Auswahl „Was soll Diana tun?“ und zugehöriger Modus-State
entfernt. Jede gesendete Chatnachricht verwendet fest `mode: auto` und wird vom
bestehenden LLM-Planer eingeordnet. Leere Chatnachrichten bleiben gesperrt;
Hinweise verweisen auf eine Bitte im Chat statt auf die entfernte Auswahl.
**58 Frontend-Tests bestanden**, Produktionsbuild erfolgreich; aktuelle Seite und
Assets liefern HTTP 200. Der ausgelieferte Build enthält keine Modus-Auswahl mehr.
Such-Popup und Statusmeldungen bleiben erhalten. Backend unverändert; kein
Server-Neustart, keine Browserprüfung oder zusätzlichen Modellaufrufe nötig.

Vorangegangene Änderung: Lade-Popup ausschließlich während einer tatsächlichen neuen
Suchpipeline. Native Dialogbedienung mit animierten Stellenkarten, sichtbarer
Laufzeit, Schätzung „meist etwa eine Minute“ und zusätzlichem Hinweis ab 90 Sekunden.
Der Dialog lässt sich in den Hintergrund legen; dies bricht die Anfrage nicht ab.
Die rechten Schritt-Hinweise und Statusmeldungen sind wieder sichtbar.

- **295 Python-Tests bestanden, 1 optionaler Test übersprungen**, darunter
  117 API-Tests mit 26 neuen Streamingfällen: echtes Suchsignal vor Persona und
  Retrieval, Auto-Chat entscheidet vorher, keine Suchphase bei Antwort/Reranking,
  abgewiesenem Auftrag, fehlendem Index oder leerer Vorauswahl. Fehler vor und
  nach Streambeginn, sichere Fehlermeldungen, CAS-Konflikte, atomare Speicherung
  und unveränderte JSON-Clients geprüft.
- **58 Frontend-Tests bestanden**, darunter 15 Streaming-Tests: byteweise UTF-8,
  geteilte Zeilen, inkrementelle/deduplizierte Phase, Antworten ohne Suchphase,
  fehlerhafte bzw. unvollständige Antworten, 409/503-Status, JSON-Kompatibilität
  und keine automatischen Wiederholungen von Anfragen.
- Zusätzlich isolierter Test über eine echte lokale HTTP-Verbindung: Das
  Suchsignal war lesbar, während ein Fake-Modell noch auf Freigabe wartete;
  danach gültiges Ergebnis und gespeicherte Testsitzung. Keine echten
  Nutzersitzungen verändert und keine Modellaufrufe für diese Prüfung.
- Produktionsbuild erfolgreich. Dialog, mobile Größen, reduzierte Bewegung
  sowie Fokus-/Schließverhalten im Quelltext geprüft; keine Browserprüfung.
- Lokaler Server nach Abschluss einer laufenden Anfrage neu gestartet. Suche,
  „Mehr erfahren“, aktuelle Assets, Health-Check und fertiger Index per HTTP
  erreichbar. Die aktive Streaming-Schnittstelle weist ein absichtlich ungültiges
  Profil korrekt mit NDJSON/400 ab, ohne Suche oder neue Sitzung.

Vorangegangene Änderung: rechter Diana-Kopf mit Kompass und Slogan sowie die
Hinweiszeilen für Profil und Persönlichkeit entfernt. „Neu starten“ liegt nun
bei den Ergebnisaktionen und bleibt mobil über die Ergebnisansicht erreichbar.
Produktionsbuild erfolgreich. Seite und aktuelle Assets liefern HTTP 200;
entfernte Inhalte fehlen im ausgelieferten JavaScript, Startaktionen bleiben
enthalten. Scroll-, Fokus- und Reset-Verträge im Quelltext geprüft. Keine
Browserprüfung oder zusätzlichen Modellaufrufe für diese Layoutänderung.

Vorangegangene Änderung: größerer Startbutton „Jetzt Profil erstellen“ mit dem Hinweis
„Hier klicken und loslegen“, rundem Pfeil und deutlichen Hover-, Fokus- und
Druckzuständen. Flexible Breite, umbrechende Texte und reduzierte Bewegung
berücksichtigt. Verhalten der Profilerstellung unverändert. Produktionsbuild
erfolgreich; Seite, aktuelle Assets, neue Beschriftung und Fokus-Stile per HTTP
geprüft. Keine zusätzlichen Modellaufrufe oder Browserprüfung.

Vorangegangene Änderung: der Erledigt-Status erscheint ausschließlich als grünes
Häkchen bzw. „Erledigt“-Badge. Die grünen Rahmenregeln für erledigte Schritte
wurden entfernt, einschließlich Hover. Aktive Hervorhebung und gemeinsame
Kastenfüllung bleiben erhalten. Produktionsbuild und aktuelle Assets per HTTP geprüft.

Vorangegangene Änderung: alle vier Anleitungskarten verwenden denselben hellen
Hintergrund, auch im aktiven Zustand und beim Überfahren mit der Maus. Farbige
Icons, Nummern, Rahmen und Statusmarkierungen bleiben erhalten. Reine CSS-Änderung;
Produktionsbuild und Auslieferung der aktuellen Assets per HTTP erfolgreich.

Vorangegangene Änderung: der rechte Startbereich enthält nur „Los geht’s“. Das Profil,
die Diana-Kopfzeile und weitere Hinweise erscheinen erst nach diesem Klick.
Mobil stehen die Anleitung und der Button untereinander in einem gemeinsamen
Scrollbereich. Nach dem Start greift wieder die bestehende Formularansicht.
Gespeicherte Sitzungen werden direkt geöffnet; ein Reset zeigt den Startbutton.
Formularentwürfe bleiben beim Wechsel zu „Mehr erfahren“ erhalten.

**43 vorhandene Frontend-Tests bestanden**, Produktionsbuild erfolgreich.
Start-/Reset-Zustände und mobile Layoutregeln im Quelltext geprüft; Suche,
„Mehr erfahren“ und aktuelle Assets liefern HTTP 200. Der ausgelieferte
JavaScript-Build enthält den neuen Startbutton. Keine Browserprüfung oder
zusätzlichen Modellaufrufe für diese Änderung.

Vorangegangene Änderung: vier farbige Schritte mit Icons, aktiver Hervorhebung und
grünem Erledigt-Status. Die Schrittkarten erlauben nur Rücksprünge bzw. den
aktuellen Schritt; vorwärts führen die regulären Formular- und Aktionsbuttons.

- **43 Frontend-Tests bestanden**, darunter zehn Tests für die Schrittnavigation:
  Onboarding, Ergebnisse, Chat, Editoren, Ladezustände, ungültige Ziele und
  gesperrte Vorwärtssprünge auch nach Rückkehr zu einem früheren Schritt.
- Abschlussmarkierungen bleiben beim Zurückgehen erhalten. Gespeicherte Sitzungen
  leiten ihren Fortschritt aus vorhandenem Profil, Ergebnissen und Chatverlauf ab;
  eine neue Sitzung setzt die Markierungen zurück.
- Codeprüfung der Formularentwürfe, Fokusziele, Lade-Sperren und mobil sichtbaren
  Fehlermeldungen. Desktop: kompakte Leiste über beiden Bereichen; mobil: zwei
  Karten pro Zeile. Die frühere Hinweisbox wurde entfernt.
- Produktionsbuild erfolgreich. Suche, „Mehr erfahren“ und aktuelle JS-/CSS-/SVG-
  Assets liefern HTTP 200. Keine Backendänderungen, zusätzlichen Modellaufrufe
  oder Browserprüfung für diese UI-Änderung.

Vorangegangene Änderung: Ort, Arbeitsmodell und Wochenstunden sind weiche Präferenzen;
der Lebenslauf liefert fachlichen Kontext. Nur die Stellenart filtert per SQL.

- **269 Python-Tests bestanden, 1 optionaler Test übersprungen**, darunter
  91 API-Tests und 128 Tests für LLM-Verträge und Bewertungsregeln.
- API-Feldstruktur bleibt kompatibel. Tests sichern, dass bekannte und unbekannte
  abweichende Orte, Arbeitsmodelle und Stunden den Kandidatenpool nicht verkleinern.
  Wünsche und CV gelangen vollständig zum LLM. Änderungen dieser Angaben bewerten
  den vorhandenen Pool neu; Stellenart, Suchaufgaben und Skills lösen weiterhin
  eine neue Suche aus. Explizite Suchaufträge und unveränderte Angaben geprüft.
- Frühere, hart eingeschränkte Pools werden markiert. Reine Fragen erhalten sie,
  automatische Bewertungsaufträge erweitern sie einmal durch eine neue Suche;
  explizites Reranking weist zunächst auf die nötige Aktualisierung hin.
  Unbeschränkte alte Pools benötigen keine solche Suche.
- Nur lesend am Originalbestand geprüft: **8.537 → 8.537 Anzeigen** trotz
  unbekanntem Wunschort, Remote-Präferenz und einer gewünschten Wochenstunde.
  Mit Stellenart Werkstudent **3.088 → 3.088 Anzeigen** unter denselben Wünschen.
- **5 echte GPT-5.4-Aufrufe in 21,4 Sekunden:** drei Wunschänderungen führten zu
  `rerank` und den passenden Profil-Patches (München, Homeoffice, 15 Stunden).
  Ein CV-only-Profil lieferte eine inhaltliche Suchanfrage mit Python und SQL.
  Drei fachlich gleiche synthetische Stellen blieben alle im Bewertungsergebnis:
  passende Präferenzen **84**, Angaben unbekannt **77**, abweichende Präferenzen
  **72** Punkte. Fachlicher Teilwert jeweils **88**; Unterschiede ausschließlich
  durch die Präferenzpassung. Stundenintervall 10–20 h wurde bei Wunsch 15 h
  korrekt berücksichtigt, unbekannte Angaben blieben offen. Kurze Begründungen
  nannten die bekannten Abweichungen. Keine echten Nutzersitzungen geändert.
- Bewertungsversion `persona-weighted-v2` verhindert die Übernahme alter
  Teilbewertungen, die noch auf der früheren Filtersemantik beruhen.
- **33 Frontend-Tests bestanden**, Produktionsbuild erfolgreich. Wünsche und
  feste Stellenart werden getrennt angezeigt; Vorschläge, Profilaktionen und
  der Aktualisierungshinweis für alte Pools sind geprüft. Beide Seiten, neue
  Assets, Health-Check und Indexstatus nach Serverneustart per HTTP erreichbar.
  Keine Browser-Prüfung; keine Änderungen an Index oder Originalexport nötig.

Vorangegangene Änderung (Bewertungsversion v1): evidenzbasierte Teilbewertungen mit unterschiedlichen
Persönlichkeitsgewichten und konkreten, sachlichen Gesprächsstilen.

- **233 Python-Tests bestanden, 1 optionaler Test übersprungen**; darunter
  98 LLM-Vertragstests, 71 API-Tests und 19 Tests der Bewertungsregeln.
- Gleiche Teilwerte können je nach Persönlichkeit unterschiedliche Scores und
  Reihenfolgen erzeugen. Gleiche Passung darf gleich bewertet bleiben; keine
  Namensaufschläge. Ganzzahlige Werte, unbekannte Zusatzangaben, Rundung,
  Fachpassungsgrenzen sowie Gewichtsverteilung für eigene Eigenschaften geprüft.
- Vollständige Abdeckung aller 20 Kandidaten vor serverseitiger Top-5-Auswahl,
  stabile Reihenfolge bei Gleichstand, begrenzte Ausgaben und ungültige IDs geprüft.
- Teilwert-Cache: neutral bei Persönlichkeitswechsel, ungültig bei verändertem
  Profil/Jobtext oder Bewertungsversion. Modellabweichungen überschreiben keine
  fixierten Werte. Private Speicherung, Neustart, Legacy-Sitzungen, reine
  Antworten und neue Suche ohne alten Cache geprüft.
- Echte GPT-5.4-Prüfung mit **20 synthetischen Kandidaten**, vier Perspektiven
  und drei identischen Chatfragen: **7 API-Aufrufe, 79,9 Sekunden insgesamt**.
  Erste vollständige 20er-Bewertung: 40,6 Sekunden. Je fünf gültige Ergebnisse,
  unveränderte gespeicherte Teilwerte beim Wechsel, kurze Stichpunkte und
  Chatantworten innerhalb 900 Zeichen. Fragen ergaben `answer` mit neutralem
  Profil-Patch, ohne neue Suche. Keine Änderungen an echten Nutzersitzungen.

| Dieselbe synthetische Stelle | DIANA | Steve Jobs | Angela Merkel | Günther Jauch |
| --- | ---: | ---: | ---: | ---: |
| Datenprototypen, wenig Anleitung | 62 | 65 | 62 | 55 |
| Datenqualität, klare Aufgaben | 66 | 59 | 74 | 60 |
| Datenanalyse mit Mentoring | 76 | 70 | 79 | 80 |
| Reporting mit Workshops | 75 | 73 | 76 | 75 |
| Klinische Tätigkeit ohne passende Fachkenntnisse | 29 | 25 | 31 | 31 |

Diese Zahlen prüfen die Umsetzung anhand bewusst unterschiedlicher Testanzeigen;
sie sind kein Qualitätsbenchmark. Die erste Live-Prüfung lag vor der abschließenden
Präzisierung der Rückfragen für Günther und der Übergabe bereits feststehender
Top-5-IDs bei gecachter Neubewertung. Die Werteberechnung ist identisch.

Abschließende Nachkontrolle: eigener Berater „Alex“ mit fixierten synthetischen
Teilwerten erfolgreich neu bewertet; bevorzugte Mentoring-Stelle und unveränderte
Komponenten geprüft. Günthers finale Chatantwort war sachlich, enthielt die
relevante Rückfrage nach Betreuung und änderte das Profil nicht. Ein vorheriger
Stil-Check hatte genau eine Frage verlangt und schlug bei einer Antwort ohne Frage
fehl; diese starre Erwartung wurde auf die tatsächliche Regel „höchstens eine
hilfreiche Rückfrage“ korrigiert. Die professionelle Formulierung bleibt eine
qualitative Prüfung, keine deterministisch garantierte Eigenschaft jeder Antwort.
Nach der letzten Stilpräzisierung erneut **117 Bewertungs-/LLM-Tests bestanden**.
Produktionsbuild und alle Frontend-Tests erfolgreich; beide Seiten, Assets,
Health-Check und Indexstatus nach Serverneustart per HTTP erreichbar. Kein Browser-Test.

Vorangegangene reine Layoutänderung: drei nummerierte Einstiegskarten ersetzen die
unbewertete Jobvorschau. Start-, Lade-, Reset- und bestehende Sitzungszustände
im Quelltext geprüft; Produktionsbuild und HTTP-Auslieferung erfolgreich.
Keine neuen Modellaufrufe oder Browser-Tests für diese Änderung.

- Vorherige automatisierte Suite: **170 bestanden, 1 optionaler Test übersprungen**.
- Separater Datenimport-Test mit der angehängten Datei: **30 bestanden**,
  einschließlich Import aller **8.537 Originalanzeigen** in eine temporäre DB.
- React-Produktionsbuild erfolgreich; **30 Frontend-Tests bestanden**, darunter
  der Erhalt mehrerer Arbeitsmodelle nach einer Chat-Verfeinerung.
- Dynamische Chatvorschläge: gespeicherte Filter ohne Chatnachricht, sichtbare
  Stellen, nicht belegte Skills, frühere Nutzerfragen, neue Ergebnisse, Legacy-Daten,
  echte Nulltreffer und ausgeblendete Treffer geprüft. Keine erfundenen Stunden;
  schwache eingeblendete Jobs liefern keine zusätzlichen Filtervorschläge.
  C/C++ und SQL/NoSQL bleiben getrennt. Höchstens drei Vorschläge, stabile IDs,
  begrenzte Textlängen und unveränderte Quelldaten geprüft. Klick übernimmt nur
  einen Entwurf (Quelltextprüfung); keine Browser- oder neuen Modellaufrufe.
- Score-Anzeige: 70 Punkte eingeschlossen, 69 ausgeblendet; gemischte und nur
  niedrige Scores, leere Suchergebnisse sowie ungültige Score-Werte geprüft.
  Einblenden erhält Originalreihenfolge und Scores. Sichtbare Anzahl, bewertete
  Anzahl und Kandidatenzahl bleiben getrennt. Reine Antworten erhalten die
  Anzeigeentscheidung; geänderte Ergebnisse/Persönlichkeiten setzen sie zurück.
  Bestätigte neue Suchen und Neubewertungen setzen die Freigabe auch dann zurück,
  wenn die Bewertung identisch ausfällt (Quelltextprüfung des Submit-Pfads).
- Chat-Dispatch: direkte Antworten behalten Karten, Scores, Profil, Suchpersona
  und Kandidatenpool bei; keine Embedding-, Persona- oder Reranking-Aufrufe.
  Weiche Prioritäten und Persönlichkeitswechsel verwenden denselben vollständigen
  Pool, geänderte Kernkriterien lösen eine neue Suche aus. Die Moduswahl wird geprüft.
- **66 API-Tests** enthalten einen 30-Anzeigen-Fall: 20 Kandidaten werden gespeichert,
  nach App-Neustart wiederverwendet und ein zuvor nicht sichtbarer Kandidat auf
  Rang 20 rückt in die Top 5. Interne Kandidaten erscheinen nicht in API-Antworten.
- Leere und ältere Pools, unveränderte Formulare, Indexvorbereitung, explizite
  Neusuche, unzulässige Filteränderungen im Sortiermodus und atomare Fehlerfälle
  geprüft. Bei Ortsfiltern entsprechen auch innere Leerzeichen der SQL-Semantik.
- **Sechs echte GPT-5.4-Planungsaufrufe** mit synthetischen Angaben: Frage → Antwort,
  Neugewichtung → Reranking, neuer Ort → Suche, Dank → Antwort, wiederholte Filter
  → Antwort, mehrdeutiger Ort → Rückfrage. Alle erwarteten Aktionen und die
  Schema-Gültigkeit bestätigt; Antwortlängen 137–458 Zeichen. Dies ist eine
  begrenzte Stichprobe, keine vollständige Evaluation der Absichtserkennung.
- UI-Helper prüfen Modusfreigaben, tatsächlich angewendete Profile/Persönlichkeiten,
  den Erhalt von Entwürfen bei verlorenen Antworten und den bestätigten Aktionsstatus.
  Profilbearbeitung und Chat-Auswahl wurden im Quelltext geprüft; kein Browser-Test.
- Nach Einbau von „Mehr erfahren“: **33 API-Tests bestanden**, beide Seiten
  `/` und `/mehr-erfahren` sowie die ausgelieferten Assets mit **HTTP 200** geprüft.
  Die Datenbank enthält weiterhin 8.537 Anzeigen, der Index meldet `ready`.
- Score-Namen für alle vier Vorbilder, bestehende Chats ohne gespeichertes Vorbild
  und eigene Namen einschließlich Leerzeichen/Umlauten geprüft. Die Beschriftung
  verwendet die Persönlichkeit der gespeicherten Ergebnisse.
- Porträt per Bytevergleich identisch mit `ppt/media/image12.png` der bereitgestellten
  Präsentation; die ausgelieferte Datei entspricht ebenfalls dem Original.
- Infoseite: Suchbereich bleibt ausgeblendet montiert, sodass Formulare, Entwürfe
  und Ergebnisse beim internen Seitenwechsel erhalten bleiben. Dies wurde im
  Quelltext geprüft; für diese Änderung wurde kein Browser-Test ausgeführt.
- Echter GPT-Test für kurze Antworten: **407 Zeichen / 55 Wörter**,
  weiterhin fünf gültige Jobbewertungen.
- Neue Frontend-Prüfungen sichern Mindestbreiten beider Bereiche, die
  Richtung der Tastatursteuerung und die Vorschau langer bestehender Nachrichten.
- Schema-Test: 900 Zeichen Chattext werden akzeptiert, 901 abgewiesen;
  alle fünf Jobbewertungen bleiben unabhängig davon erhalten.
- Tatsächliche HTTP-Antwort für die React-Startseite: **200**.
- Persönlichkeit getrennt vom Bewerberprofil geprüft: Wechsel erhält Suchpersona,
  Retrieval-Anfrage und Filter; folgende Chats behalten die Auswahl. Bei Fehlern
  bleibt der gespeicherte Zustand vollständig erhalten.
- Echter Persönlichkeitswechsel auf Angela Merkel erfolgreich: Profil und
  Suchpersona blieben identisch; die neue Bewertung wurde gespeichert.
- Echter Folgechat „nur Werkstudent, maximal 20 Stunden“ erfolgreich:
  **2.970 zulässige Anzeigen**, fünf aktualisierte Karten; Skills und Persönlichkeit
  blieben erhalten. Gesamter Wechsel-/Chat-Test: **135,1 Sekunden**.
- Zusätzlicher echter GPT-Test mit Günther-Jauch-Inspiration: ein Profil ohne
  harte Filter wird korrekt als uneingeschränkt erklärt; keine internen Job-IDs
  in der Antwort.
- Alte Chats ohne Persönlichkeit verwenden den DIANA-Standard.
- Originaldatenbank mit **8.537 Anzeigen** importiert und im laufenden Server aktiv.
- Echter GPT-5.4-Test mit Originalanzeigen: fünf eindeutige Ergebnisse mit
  ganzzahligen Scores **1–100** und je **2–3 Stichpunkten mit maximal 200 Zeichen**.
- Vollständige E5-Indexierung abgeschlossen: **8.537 Anzeigen**,
  **8.228 eindeutige Dokumentvektoren**, **0 fehlende oder ungültige Vektoren**
  bei Prüfung auf Dimension 1.024; gleiche Texte teilen sich einen Cache-Eintrag.
- Vollständiger HTTP-Live-Test mit dem Originalbestand erfolgreich: **HTTP 201**,
  **8.537 zulässige Anzeigen → 20 hybride Kandidaten → 5 GPT-Empfehlungen**,
  Scores **91, 87, 82, 79, 76**, jeweils drei gültige kurze Begründungen.
  Laufzeit: **66,5 Sekunden**, anschließend identischen Zustand per HTTP geladen.
  Alle Ergebnis-IDs sind echte Datensatz-IDs; die Auswahl geht über die erste
  unbewertete 20er-Vorschau hinaus.
- `pip check`: keine inkonsistenten Abhängigkeiten.
- Quelltextprüfung: kein API-Schlüssel in auslieferbaren Dateien;
  lokale `.env` mit Dateimodus `0600`.
- Echter OpenAI-Zugriff: Modell `gpt-5.4` verfügbar.
- Echte GPT-5.4-Persona erfolgreich erzeugt und gegen das Schema validiert.
- Echtes GPT-5.4-Reranking erfolgreich: vier nach den gesetzten Demo-Filtern
  zulässige Kandidaten ergeben vier gültige, eindeutige Job-IDs.
- Echte GPT-5.4-Chat-Verfeinerung erfolgreich: „Werkstudent, maximal 20 Stunden“
  wurde korrekt angewendet; zuvor angegebene Skills blieben erhalten.
- Echter E5-Warmup erfolgreich: fünf Dokumentvektoren mit dem vorgegebenen,
  auf Revision festgelegten Modell erzeugt und lokal zwischengespeichert.
- Gunicorn-Start und tatsächlicher HTTP-Health-Check erfolgreich (HTTP 200).
- Vorheriger vollständiger Live-Test mit den fünf Dummy-Anzeigen nach Warmup: **HTTP 201, fünf eindeutige Jobkarten**,
  echte E5-Scores, BM25/RRF, GPT-5.4-Persona und Reranking sowie anschließend
  per HTTP wieder abgerufener, identischer Chat-Zustand. Laufzeit: **48,3 Sekunden**.

Der erste HTTP-Versuch mit dem kompletten Bestand brach unter Gunicorn/MPS
beim macOS-Initialisieren nach `fork()` ab. Die lokale Webseite wurde deshalb
mit `.venv/bin/python app.py` ohne diesen Prozesswechsel gestartet.

Beim ersten Modelldownload blieb der optionale Xet-Transport ohne Fortschritt.
Der dokumentierte HTTP-Download mit `HF_HUB_DISABLE_XET=1` war erfolgreich.
Ein vor Abschluss des Downloads gestarteter API-Aufruf überschritt das
clientseitige Zeitlimit von zehn Minuten. Deshalb den dokumentierten Warmup vor
dem ersten regulären API-Aufruf ausführen.

Die regulären Tests verwenden echte SQLite-/BM25-Implementierungen und
kontrollierte Testvektoren bzw. simulierte OpenAI-Antworten. Die separat genannten
GPT-5.4-Prüfungen verwenden echte API-Aufrufe mit dem synthetischen Beispielprofil.
Dies prüft die technische Integration; eine Aussage zur Matching-Qualität oder
Reproduktion der Masterarbeit lässt sich daraus nicht ableiten.
