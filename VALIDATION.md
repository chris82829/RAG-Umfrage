# A/B-Gesamtpaketvergleich · diana-v7 · 10.09.2026

642 Backendtests bestanden, 1 übersprungen; 134 Frontendtests einschließlich
SSR bestanden. Produktionsbuild und `git diff --check` erfolgreich. Keine
Browserprüfung und keine neuen Modellaufrufe für diese Paketumstellung.

A liefert Stellenkarten ohne `match`/`retrieval`, zeigt alle bis zu 20 Ergebnisse
und unterdrückt automatische Bewertungsnachrichten. Chatfragen bleiben verfügbar.
B behält Persönlichkeit, Scores, Begründungen und die Einblendoption unter 70.
V7 stellt die neun zusätzlichen Persönlichkeits-/Bewertungsfragen nur B.
Die archivierte V6-Definition ist bytegleich mit der ursprünglichen Git-Version.

Zusätzliche Integration: Beide historischen Zuordnungen (B→A und C→B) mit neuem
V7-Fragebogen, Onboarding und Abgabe geprüft. Originalcodes, Experimentkennung
und Zeitstempel bleiben erhalten. Gleichzeitige Migration/Zuteilung und Rollback
sind abgedeckt. Der Offline-Modellvergleich verwendet jetzt A/B und trennt
interne Bewertungen von tatsächlich dargestellten Karten; alte Berichte unverändert.

Lokal neu gestartet und auf dem bestehenden Server-Port 5051 ausgerollt.
Startseite, Suche, Umfrage, Verwaltung, Datenschutz und API antworten mit HTTP 200.
HTML und JavaScript sowie elf zentrale Backend-/Definitionsdateien stimmen mit
dem geprüften lokalen Stand überein. Modell weiterhin `gpt-5.4-2026-03-05`,
Denkaufwand `none`; 8.537 Stellen. Technischer Nachweis:
`evaluation/ab-package-20260910/deployment-check.json`.

Vor der Migration vollständiges SQLite-Backup und Anwendung gesichert unter
`backups/pre-ab-package-20260910T182102Z/`. Die fünf abgeschlossenen Antworten
und sieben bestehenden Zuteilungen sind nach dem Update per SHA-256 unverändert.
Keine echten Antworten gelöscht oder für Tests angelegt. Die bisherigen
Einwilligungen müssen wegen der geänderten Studienhinweise erneuert werden.

Die Planung mit 200 auswertbaren Teilnahmen bleibt bestehen. Der Vergleich
untersucht das Gesamtpaket und darf nicht als isolierter Persönlichkeitseffekt
ausgelegt werden; V6 und V7 nicht ungeprüft zusammenlegen.

# Historisch: Persönlichkeitskontrast und Planung mit 200 · 10.09.2026

Die tatsächlichen editierbaren Vorlagen erhalten nun einen konkreten Ausdrucksplan
auf Basis ihrer gewählten Eigenschaften. Gemeinsame Begrüßung verkürzt; alle
neuen generierten Chat- und Suchantworten in B/C auf 600 Zeichen begrenzt.
Keine Änderung an Modell, Denkaufwand, Scores, Gewichten oder Fragebogen.

622 Backend-Tests bestanden (1 übersprungen); nach abschließender sprachlicher
Nachschärfung erneut 418 betroffene Backend-Tests bestanden. 129 Frontend-Tests
und Produktionsbuild bestanden. Drei vollständige synthetische Modellvergleiche
mit je elf logischen Aufrufen archiviert unter `evaluation/personality-20260910/`;
letzte Runde alle mechanischen Checks bestanden. Grenzen der qualitativen
Sichtung sind im Bericht dokumentiert. Kein Browser-QA und keine Testantworten
in der produktiven Umfrage angelegt.

Lokal neu gestartet und auf Port 5051 ausgerollt. Die drei geänderten Python-Dateien
im Container stimmen per SHA-256 mit dem geprüften lokalen Stand überein;
HTML/JavaScript entsprechen dem gebauten Frontend. E5 ist vorgeladen, Health OK.
Die fünf zuvor abgeschlossenen Antworten sind vor/nach Update bytegleich
(Hashvergleich); Runtime und Zugangsdaten wurden nicht ersetzt. Alte Anwendung
auf dem Server unter `backups/pre-personality-20260910/` gesichert.

Studienplan `STUDY-PLAN-200.md` mit reproduzierbarer Sensitivitätsanalyse:
200 auswertbare Hauptantworten, d≈0,398 bei 80 % Power, 250 Starts bei angenommener
20-%-Verlustquote. Kein automatischer Teilnahmestopp eingerichtet.

# Validierung am 10.09.2026

Laufzeit: Python 3.12.14, lokale isolierte `.venv` auf macOS ARM64.

Aktuelle UI-Anpassung: Sichtbarere Hauptaktionen durch dauerhaften Kontrastrand,
stärkeren Schatten, zwei breitere Wellen im Abstand von 1,1 Sekunden und
bewegten Pfeil. Zusätzlich beim Weitergehen im Profil, beim Starten der Suche,
auf allen Fragebogenseiten sowie beim Abschließen. Größere Hauptaktion in der
Umfrage-Fußleiste. Auf kleinen Bildschirmen begrenzte Wellen, bei reduzierter
Bewegung statische Hervorhebung. Einwilligung, Antwortauswahl und optionale
Nebenaktionen werden durch diese Anpassung nicht animiert.

104 Frontend-Tests und SSR-Prüfungen für Weiter/Abschluss/Ergebnisse bestanden;
Produktionsbuild erfolgreich. Der zuvor zurückgenommene Änderungswunsch zu
Wartezeit-Fragen und Such-Popup bleibt unangetastet.


Aktuelle Änderung: Betriebsfreigabe im Admin-Panel über authentifiziertes
GET/PUT `/api/admin/study-status`. CSRF-Schutz und strikt boolesche Eingabe.
SQLite speichert Freigabe/Pause und Änderungszeitpunkt dauerhaft; der Status
wirkt auch auf bestehende Sitzungen und verspätete Schreibvorgänge. Pausieren
löscht keine Antworten und blockiert keinen Widerruf. Endgültig beendete Studien
bleiben geschlossen. Freigabe/Pause ändert nicht die Version des Einwilligungstexts.

277 Backend-Tests bestanden; neue Fälle prüfen Zugriffsschutz, Freigabe trotz
initial gesperrter Konfiguration, Pause, erneute Freigabe, erhaltene Antworten,
Einwilligungsnachweis, Status in einer zweiten Store-Instanz und endgültiges Ende.
React-SSR prüft die Admin-Steuerung für offen/pausiert/beendet; Build erfolgreich.
Server ausgerollt und über die authentifizierte Admin-API freigegeben. Öffentliche
Teilnehmer-API meldet ready=true, CSRF-/Anmeldeschutz und weiterhin erforderliche
Einwilligung bestätigt. Antwortanzahl unverändert; keine Testantworten oder
GPT-Aufrufe erzeugt. Lokale Teilnahme ebenfalls freigegeben.


Aktualisierung: Alleinige Benennung von Christoph Scharnagl als Verantwortlichem
auf Vorgabe des Studienleiters. Kompakter Einwilligungseinstieg mit Link zu den
vollständigen Hinweisen unter `/datenschutz`, statt aller Hinweisabschnitte
direkt vor der Checkbox. Leere Checkbox bestätigt Kenntnisnahme und ausdrückliche
Einwilligung; das Öffnen des Links wird nicht erzwungen oder protokolliert.

Prüfung: 16 Datenschutztests bestanden, React-SSR bestätigt versteckte Langtexte
am Einstieg, öffentlich erreichbare vollständige Hinweise und unverändert leere
Checkbox mit deaktiviertem Absenden. Produktionsbuild erfolgreich. Die Änderung
wird auf Port 5051 übernommen; bestehende Freigabesperre bleibt unverändert.


Aktuelle Änderung: Passwortgeschützte Umfrageverwaltung unter `/verwaltung` mit
ID-/Versionsfilter, Einzelansicht, expliziter Löschbestätigung und Numiqo-CSV.
ZIP mit Codebuch und versionierten Systemmanifesten. OpenAI-Snapshot fest auf
`gpt-5.4-2026-03-05`, weiterhin `reasoning.effort=none`. Neue Teilnahmen erhalten
technische Provenienz; historische Antworten bleiben ohne nachträgliche Zuordnung.

Prüfung: **455 Backend-Tests und 104 Frontend-Tests bestanden**. Abgedeckt sind
Anmeldung, Cookie/CSRF, Fehlversuchsbegrenzung, gezielte Löschung samt Widerruf,
Formelschutz, numerische Codes, fehlende Angaben, getrennte 1–5-/1–10-Skalen und
Modellzuordnung. React-SSR prüft Anmeldung, Exportsteuerung und gesperrte
Löschbestätigung bis zur Eingabe der ID. Produktionsbuild erfolgreich.
Lokaler authentifizierter HTTP-Test: Anmeldung, gefilterte Übersicht, CSV mit
28 Spalten, ZIP mit fünf Dateien, Abmeldung und Zugriffsverweigerung ohne Anmeldung.
Alle vier Seiten erreichbar; Health meldet den festen Snapshot. Verfügbarkeit
des Snapshots per OpenAI-Modellabfrage bestätigt, keine Completion ausgeführt.

Keine echten Antworten gelöscht und keine Daten zu Numiqo übertragen.
Anschließend auf ausdrücklichen Wunsch auf Port 5051 ausgerollt: alter
Anwendungsstand und SQLite gesichert, ein vorhandener Antwortdatensatz erhalten.
Anmeldung mit gewünschtem Passwort ohne Nutzernamen, ZIP-Export und Abmeldung
auf dem Server geprüft. Andere Docker-Projekte unverändert. Die noch ausstehende
Studienfreigabe bleibt gesperrt (siehe PRIVACY.md).

Vorangegangene Änderung: Lokale Einwilligung vor Systemstart mit serverseitiger Sperre,
versioniertem Nachweis und Widerruf. Eigenständige öffentliche DIANA-Teilnahme-ID,
Kopieren, E-Mail-Löschanfrage, Anzeige im Abschluss und im CSV. Gezielte Adminlöschung
mit Vorschau. Produktive Suchsitzungen nur im RAM mit Ablauf; keine automatische
Löschung der Forschungsdaten zum Promotionsende. Vollständige Einzelantworten für
konkret benannte Forschung mit regelmäßiger Erforderlichkeitsprüfung vorgesehen.

Prüfung: **269 Backend-Tests und 104 Frontend-Tests bestanden**. React-SSR prüft
Einwilligungssperre, leere Checkbox, Impressumslink, Widerruf, Teilnahme-ID und
E-Mail-Link im Abschluss. Tests prüfen fremde IDs, exakte CSV-Zuordnung, gezielte
Löschung, Retries, Sperre verspäteter Schreibvorgänge nach administrativem Widerruf
sowie RAM-Ablauf. Build erfolgreich. Lokale vier Routen und aktuelle Assets per
HTTP bestätigt, API verweigert Anfragen ohne Einwilligung mit 428.

Keine Browserprüfung oder Live-GPT-Anfrage. Keine echten Antworten/Chats gelöscht.
Nicht auf den Server ausgerollt: privacy_settings.json bleibt bis zur Klärung der
in PRIVACY.md aufgeführten Verantwortlichkeits-, Vertrags-/Drittland- und technischen
Details gesperrt. Die alten Serverdaten wurden nicht verändert.

Vorangegangene Änderung: Vier separate 1–10-Fragen zur Nützlichkeit von Score,
Passungsbegründungen, personalisiertem Chatbot und personalisierter Suche im
neuen Block „Was war nützlich?“. Eigene Skalen-Endpunkte „Gar nicht nützlich“
und „Sehr nützlich“. Alle Bewertungsfragen stehen in kompakten, nummerierten
Karten mit sichtbarer Antwortmarkierung und mobilen 5er-Reihen.

Fragebogenversion v3 enthält 13 Bewertungen. Der Server akzeptiert weiterhin
v1/v2, exportiert ältere Antworten ohne erfundene neue Werte und erhält deren
Wiederholungssicherheit. Unfertige v2-Entwürfe übernehmen vorhandene Antworten;
bereits abgeschlossene v2-Teilnahmen behalten ihre Bestätigung.

Prüfung: **102 Frontend-Tests und 72 Backend-Umfragetests bestanden**.
Produktionsbuild erfolgreich. React-SSR bestätigt vier Karten, 40 Auswahlwerte,
korrekte Skalen-Endpunkte, Antwortmarkierung, eindeutige zugängliche IDs sowie
unveränderten Einstieg und Wartezeit-Fragen. Lokale und Server-Seiten samt aktuellen
Assets bytegenau per HTTP bestätigt; v3-Vertrag mit 13 Bewertungen im laufenden
Container geprüft. Keine Browserprüfung oder GPT-Anfrage.

Vorangegangene Änderung: Direkter Einstieg in DIANA nach „Umfrage starten“.
Während einer vollständigen Suche lassen sich im Wartezeit-Dialog demografische
Angaben, Suchvorhaben und zwei Fragen zur Einrichtung der KI beantworten.
Das eingebettete System bleibt aktiv. Nach Ende der Berechnung bleibt der
Dialog offen und bietet „Ergebnisse ansehen“. Fehlende Angaben werden im späteren
Fragebogen nachgeholt; die Freigabe bleibt an den abgeschlossenen Schritt 3 gebunden.
Das abgeschickte Suchprofil liefert einen bearbeitbaren Vorschlag zum Suchvorhaben.
Manuelle Änderungen und geleerte Antworten bleiben auch bei weiteren Suchen erhalten.

Prüfung: **100 Frontend-Tests und 63 Backend-Umfragetests bestanden**.
Geprüft wurden unter anderem Herkunft und Testlauf der Nachrichten, begrenzte
Datenübertragung ohne Lebenslauf/Chat, Schutz eigener Änderungen, Entwurfs-Migration,
Navigation, Abschlussvalidierung und Speicherung ohne zusätzliche Metadaten.
React-SSR bestätigt direkten Systemstart, beide Wartefrageblöcke, 1–10-Skalen,
bearbeitbaren Suchvorschlag und Ergebnis-Rückkehr. Produktionsbuild erfolgreich.
Seiten und aktuelle Assets lokal sowie auf Server-Port 5051 bytegenau per HTTP
bestätigt; Health-Endpunkt antwortet erfolgreich. Persistente Laufzeitdaten bleiben
erhalten. Keine Browserprüfung oder zusätzliche GPT-Anfrage.

Vorangegangene Änderung: „Keine Vorlage“ ist im Persönlichkeitsmenü auswählbar und
stellt einen unabhängigen neutralen Entwurf ohne Prominenten-Hinweise her.
Das Freitextfeld „Eigene Hinweise“ ist dauerhaft sichtbar; die Klappfunktion
entfällt. Die grüne Markierung der Ergebnisphase wird als nicht interaktive
Vordergrund-Ebene über dem scrollenden Stellenbereich gezeichnet. Auf Mobilgeräten
liegt sie nur über der Ergebnisansicht, nicht über dem Chat.

Prüfung: **16 Frontend-Tests bestanden**, inklusive neutraler Vorlagenauswahl.
React-SSR bestätigt die auswählbare Leeroption und das direkt sichtbare
Freitextfeld mit erhaltenen Vorlageninhalten. Produktionsbuild erfolgreich.
Seiten und aktuelle Assets lokal sowie auf Port 5051 per HTTP bestätigt;
Server-Container healthy, Laufzeitdaten erhalten. Keine Browserprüfung, Backendänderung oder zusätzliche GPT-Anfrage.

Vorangegangene Änderung: Rechter Einstiegsbereich erhält standardmäßig 60 % der
Arbeitsfläche, begrenzt auf 800 Pixel und mindestens 400 Pixel Platz für die
linke Anleitung. Die Trennlinie bleibt mit Maus und Tastatur bedienbar.
Einstiegsbreite und gespeicherte Ergebnis-Chatbreite sind getrennt; die mobile
Einspaltenansicht bleibt bestehen. Eingabeformulare sind auf 720 Pixel begrenzt.

Der lokale Start lädt E5 jetzt vor dem HTTP-Server und führt eine kurze
Probe-Inferenz durch. Keine Dokument-Neuindexierung oder GPT-Anfrage beim
Vorbereiten; bei Ladefehlern bleibt ein späterer Versuch über die Suche möglich.
Der Docker-Server lädt E5 bereits vor dem Annehmen von Anfragen. GPT-5.4 mit
`none` bleibt unverändert; GPT-5.4 mini wurde nur als Vergleichskandidat besprochen.

Prüfung: **193 Python-Tests und 23 Frontend-Tests bestanden**. Neue Prüfungen
betreffen eine initiale Query-Inferenz ohne Dokumentcacheaufbau und die Breite
mit erhaltenem Platz für die Anleitung. Build erfolgreich. Lokaler Start
bestätigt E5 bereit vor Öffnen des HTTP-Ports; Server-Log bestätigt vorgewärmtes
E5. Seiten und Assets lokal und auf Port 5051 bytegenau geprüft, GPT-Modell und
Denkaufwand über Health bestätigt. Keine Browserprüfung oder Live-GPT-Anfrage.

Vorangegangene Änderung: Persönlichkeitsformular an den Stil des Suchprofils angepasst:
gemeinsame kompakte Überschrift, dezenter blauer Vorlagen-Button, normale
Feldbeschriftungen und identische Feldabstände. Zusätzliche Freitext-Hinweise
liegen wie die weiteren Profilwünsche in einem anfangs geschlossenen Abschnitt.
Drei Vorlagen, Name, Gewichtung, Eigenschaften, Freitextwerte und Info-Dialog
bleiben erhalten, auch beim erneuten Bearbeiten einer Persönlichkeit.

Prüfung: **27 vorhandene Frontend-Tests bestanden**; React-SSR bestätigt den
anfangs geschlossenen Zusatzbereich, erhaltene Vorlagenwerte und den Info-Dialog.
Produktionsbuild erfolgreich. Lokale und Server-Seiten samt aktuellen Assets
bytegenau per HTTP geprüft. Server-Container auf Port 5051 aktualisiert und
healthy; dauerhafte Daten unverändert. Keine Browserprüfung oder Live-LLM-Anfrage.

Server-Umfrage per vorhandenem CLI exportiert: zum Exportzeitpunkt 0 vollständig
abgesendete Antworten. CSV in Downloads gespeichert, UTF-8-BOM/Semikolon und
21 Spalten geprüft. Export-/Download-Anleitung in `DEPLOYMENT.md` ergänzt.

Vorangegangene Bereitstellung: DIANA als eigenes Docker-Compose-Projekt `diana-survey`
auf `ifaiforschung.informatik.fh-nuernberg.de:5051` gestartet. Server-Verzeichnis
`/home/master/diana-survey`; bestehende sieben Container und deren Startzeiten
unverändert. CPU-Image mit festgelegtem Embedding-Stack, ein Gunicorn-Worker,
vier Threads, E5-Vorladung ohne GPT-Aufruf, nicht privilegierter Nutzer,
6 CPUs/12 GB RAM als Obergrenze, automatische Neustarts und Healthcheck.

Übertragen wurden die aktuellen Build-Dateien, 8.537 Stellen, der vollständige
Vektorcache und der per SHA-256 geprüfte Modell-Snapshot. Chat- und Umfragetabellen
starten leer; der API-Schlüssel liegt nur in einer Server-Umgebungsdatei (0600),
nicht im Image. Laufzeitdaten sind persistent eingebunden.

Prüfung über die VPN-erreichbare Adresse: Startseite, Umfrage, eingebettete Suche
und sämtliche referenzierten Build-Assets stimmen bytegenau mit dem lokalen
Build überein. Health meldet GPT-5.4/`none`, Index vollständig. Ungültige
Umfrageantworten werden abgelehnt. Eine vollständige Live-Suche liefert 20 Jobs
mit mindestens zwei Begründungen; Chat-Sitzung erfolgreich wieder geladen.
Nur diese eigens angelegte Testsitzung anschließend gelöscht. Gesamtdauer
**66,923 Sekunden** (erste Textvorschau 66,488 s), Einzelmessung auf dem Server.
`pip check` fehlerfrei, Container healthy, kein API-Schlüssel unter `/app/.env`.
Keine Browserprüfung und keine Änderungen an bestehenden Server-Projekten.
Details: `server-deployment-check-2026-09-10.json`; Betrieb: `DEPLOYMENT.md`.

Vorangegangene Prüfung: Lokalen Server neu gestartet und zwei vollständige Live-Suchen
über den vom Frontend verwendeten Streaming-Endpunkt `/api/onboard` gemessen.
Fiktives Data-Science-/Softwareprofil, Angela-Merkel-KI, keine Stellenart ausgeschlossen:
alle 8.537 Anzeigen berücksichtigt, jeweils 20 Stellen mit mindestens zwei
Begründungen bewertet. Nur die beiden eigens erzeugten Testsitzungen anschließend
gelöscht; keine Umfrageantworten angelegt oder bestehenden Sitzungen verändert.

Erste Suche nach Neustart: **63,302 s** insgesamt (Datenbank 1,120 s,
Persona 7,259 s, Retrieval einschließlich E5-Laden 26,488 s, Reranking 27,345 s).
Zweite frische Suche im selben Prozess: **40,604 s** insgesamt (Datenbank 1,125 s,
Persona 4,730 s, Retrieval 3,642 s, Reranking 30,979 s). GPT macht im zweiten Lauf
rund 88 % der Gesamtzeit aus. Beide GPT-Aufrufe je Lauf bestätigen `none` und
null Reasoning-Tokens. Erste gestreamte Chattexte nach 60,870 bzw. 40,347 s;
Streaming liefert bei dieser Vollsuche also erst kurz vor dem fertigen Ergebnis Text.

Einzelmessungen, keine belastbare Latenzverteilung oder Qualitätsbewertung.
Während des ersten Laufs gab es einen unabhängigen Chat-Aufruf; dessen Phasen
wurden aus der Aufschlüsselung entfernt. Bestehender Vektorcache war vollständig,
keine Browser-Renderzeit gemessen. Details: `search-latency-benchmark-2026-09-10.json`.
Server bleibt mit geladenem E5-Modell verfügbar; Health und Startseite bestätigt.

Vorangegangene Änderung: Die drei Buttons „Umfrage starten“, „Jetzt Profil erstellen“
und „Weitere Fragen für die Umfrage beantworten“ teilen sich eine deutlichere
Animation mit zwei versetzt auslaufenden blauen Wellen und einem Pfeilimpuls.
Die Animation bleibt beim Überfahren aktiv. Zusätzlicher Abstand an der
Umfrage-Fußleiste lässt die Wellen auch auf schmalen Bildschirmen auslaufen.
Deaktivierte Buttons und die Systemeinstellung für reduzierte Bewegung bleiben
berücksichtigt. Die Freigabe des Weiter-Buttons erst nach Schritt 3 ist unverändert.

Prüfung: **23 vorhandene Frontend-Tests bestanden**, Produktionsbuild erfolgreich.
Startseite, Umfrage, eingebettete Suche und aktuelle Assets per HTTP bestätigt.
Keine Browserprüfung, Backendänderung oder Live-LLM-Anfrage.

Vorangegangene Änderung: GPT-5.4 verwendet für alle Anfragen zentral
`reasoning.effort=none`. Die bisherigen Werte `medium` und `low` entfallen bei
Persona-Erzeugung, Profilverfeinerung, Chat, frischen Bewertungen und der erneuten
Begründung gespeicherter Bewertungen. Modell, Streaming, Structured Outputs,
Ausgabelimits, alle 20 Bewertungen, Begründungen und Persönlichkeitsgewichtung
bleiben erhalten. Health-Endpunkt und Performance-Logs melden den aktiven Denkaufwand.

Die [offizielle GPT-5.4-Modellseite](https://developers.openai.com/api/docs/models/gpt-5.4)
bestätigt `none` als unterstützten Wert. Prüfung: **521 Python-Tests bestanden,
1 übersprungen**. Vorhandene API-/SDK-Tests prüfen `none` in sämtlichen Aufrufpfaden,
einschließlich echter SDK-Serialisierung mit simulierten Streaming-Antworten und
vollständigen Begründungen für 20 Stellen. Keine Live-LLM-Anfrage oder neue
Latenzmessung; frühere Benchmarkwerte im README sind ausdrücklich als historisch
gekennzeichnet. Frontend unverändert.
Lokalen Server neu gestartet; `/api/health` bestätigt `gpt-5.4`, Denkaufwand
`none` und weiterhin 8.537 Stellen.

Vorangegangene Änderung: „Weitere Fragen für die Umfrage beantworten“ und seine
Fußleiste erscheinen erst nach einer vollständig abgeschlossenen ersten Suche
(DIANA-Schritt 3). Die Freigabe kommt aus dem eingebetteten System, mit Prüfung
von Ursprung, Fenster und Testlauf-ID. Wiederhergestellte Suchsitzungen werden
ebenfalls erkannt; Laden, Fehler und Textvorschauen geben den Fragebogen nicht frei.
Auch null Treffer und ausgeblendete Scores zählen als abgeschlossene Suche.
Die Freigabe bleibt für diesen Testlauf bei Rücksprüngen und Neuladen erhalten.

„Umfrage starten“, „Jetzt Profil erstellen“ und der neue Weiter-Button teilen sich
eine dezente Einblend-, Leucht- und Pfeilanimation. Deaktivierte Buttons und die
Systemeinstellung für reduzierte Bewegung werden berücksichtigt. Keine Änderung
an Matching, Modellen, API oder Antwortdaten der Umfrage.

Prüfung: **93 Frontend-Tests bestanden**, darunter neue Tests für die
Abschlussmeldung, Wiederherstellung, falsche bzw. veraltete Fensterereignisse und
die gesperrte Vorwärtsnavigation vor Schritt 3. React-SSR bestätigt die fehlende
Fußleiste vor dem Abschluss und den animierten Button danach, bei unverändertem
Vorschaufenster. Produktionsbuild und HTTP-Prüfung der aktuellen Seiten und Assets
erfolgreich. Keine Browserprüfung, zusätzlichen LLM-Aufrufe oder Backendänderungen.

Vorangegangene Änderung: Umfrage als geführter Ablauf ab der Vorstellungsseite `/` bzw.
`/index.html`. „Umfrage starten“ öffnet zuerst demografische Angaben, danach die
eingebettete Jobsuche und anschließend vier nacheinander gezeigte Kategorien:
Suchvorhaben, KI-Suchpersönlichkeit, Suchen im Gespräch und Gesamterfahrung.
Die Systemseite enthält ausschließlich DIANA und den Weiter-Button. Die Vorschau
wird erst nach den demografischen Angaben geladen und bleibt bei Rücksprüngen
eingebunden. Der Maximieren-Button entfällt.

Neun Bewertungsfragen verwenden ausschließlich 1–10 mit einheitlichen
Zustimmungsankern. Der Inhalt bewertet die Suche und Beratung mit der Persönlichkeit;
keine Frage bewertet die Passung der gefundenen Jobs. Das Suchvorhaben wird
gesondert als Text erfasst. Demografische Auswahlfelder erlauben „Keine Angabe“,
die Studien-/Fachrichtung ist optional. Formulare und CSV verwenden eine gemeinsame
Fragedefinition. Eine neue Version `diana-v2` trennt die Daten von der früheren
1–5-Skala. Gespeicherte V1-Antworten bleiben erhalten und haben eigene Exportspalten.

Validierung: **520 Python-Tests bestanden, 1 übersprungen; 84 Frontend-Tests
bestanden.** Die Umfragetests prüfen zusätzlich die 1–10-Grenzen aller neun
Skalen, demografische Auswahlwerte, Suchvorhaben, Vorwärts-/Rückwärtsnavigation,
Reparatur ungültiger gespeicherter Schritte und getrennte V1-/V2-Exporte.
React-SSR prüft den Einstieg über die Vorstellungsseite, das verzögerte Laden der
Vorschau, die reine Systemansicht mit einem Button, die einzelnen Kategorien,
anfangs leere Radio-Gruppen und das Sperren beim Speichern. Produktionsbuild
erfolgreich. Mobile CSS: fünf Skalenwerte pro Zeile, einspaltige Demografie,
mindestens 44 Pixel hohe Bedienelemente, Systemansicht mit dynamischer Viewporthöhe
und Safe-Area-Abstand. Keine Browser- oder reale Geräteprüfung, keine zusätzlichen
Live-LLM-Anfragen. Testantworten ausschließlich in temporären Datenbanken.
Lokalen Flask-Server neu gestartet; Vorstellung, `/index.html`, `/umfrage`,
eingebettete Suchroute und aktuelle Build-Assets per HTTP bestätigt.

Vorangegangene Änderung: Zusätzliche Umfrageseite `/umfrage` mit zwei Schritten,
eingebetteter und vergrößerbarer DIANA-Jobsuche sowie den vier vorgegebenen Fragen.
Das Vorschaufenster bleibt beim Wechsel zum Fragebogen eingebunden. Eine eigene
Browser-Sitzung trennt die Testsuche von einer normalen DIANA-Sitzung. Der
Fragebogen speichert einen Entwurf im selben Tab und zeigt erst nach bestätigter
Serverspeicherung eine Danke-Seite.

Antworten werden separat von Suchprofilen und Chatverläufen in SQLite gespeichert.
Der neue POST-Endpunkt prüft Pflichtfelder, Skalenwerte, Antwortoptionen und
Textlänge. Eine zufällige Teilnahme-ID verhindert doppelte Einträge bei
wiederholten oder gleichzeitigen Requests. CSV-Export über den Flask-Befehl
`survey-export`, mit deutschen Beschriftungen, UTF-8-BOM und Formelabsicherung;
kein öffentlicher Export und kein Überschreiben vorhandener Dateien.

Validierung: **493 Python-Tests bestanden, 1 übersprungen; 80 Frontend-Tests
bestanden.** Davon 36 neue Backend- und 10 neue Frontend-Tests für die Umfrage,
einschließlich dauerhafter Speicherung, gleichzeitiger Wiederholungen, ungültiger
Eingaben, Export, Antwortentwürfen, Verbindungsfehlern und Sitzungstrennung.
React-SSR prüft die eingebettete Suchroute, vier beschriftete Fragengruppen,
15 anfangs nicht ausgewählte Antworten und die Sperre während des Speicherns.
Produktionsbuild erfolgreich; `/umfrage`, `/umfrage/`, Startseite, eingebettete
Suchroute und aktuelle Build-Assets per HTTP geprüft. Lokales Backend mit
8.537 Stellen und unverändertem GPT-5.4 erreichbar.
Keine Browserprüfung oder zusätzlichen Live-LLM-Aufrufe;
alle Testantworten ausschließlich in temporären Testdatenbanken.

Vorangegangene Änderung: Die grüne Zusammenfassung des Suchwunsches oberhalb der
Persönlichkeitsauswahl ist entfernt, einschließlich der ungenutzten CSS-Regeln.
Die Angaben bleiben im Suchprofil erhalten. Produktionsbuild erfolgreich;
Suchseite und aktuelle Assets per HTTP geprüft. Keine neuen Tests oder
Backendänderungen für diese Entfernung.

Vorangegangene Änderung: „Wie beeinflusst das meine Suche?“ ist jetzt ein kleines
Info-Icon direkt neben „KI-Suchpersönlichkeit“. Der separate Textbutton entfällt.
Das Icon öffnet weiterhin denselben Erklärdialog mit Grafik; Tooltip, zugänglicher
Name, Tastaturbedienung und Lade-Sperre bleiben erhalten.

Produktionsbuild und React-SSR-Prüfung von Position, Icon, Beschriftung und
Lade-Sperre erfolgreich. Suchseite und aktuelle Assets per HTTP bestätigt.
Keine neuen Tests, Backendänderungen oder Browserprüfung für diese Layoutänderung.

Vorangegangene Änderung: Die Formularüberschrift heißt „KI-Suchpersönlichkeit“.
„Vorlage“ steht als kompakte Auswahl mit Pfeil rechts daneben. Die native
Auswahl mit drei Personen, automatisches Ausfüllen, Fokusziel und Lade-Sperren
bleiben erhalten. Flexible Überschrift und mindestens 44 Pixel Bedienhöhe
berücksichtigen schmale Chatbereiche und Mobilgeräte.

Produktionsbuild erfolgreich. Neuer gemeinsamer Kopfbereich, Standardpersönlichkeit,
drei Vorlagen sowie aktive/gesperrte Auswahl per React-SSR geprüft. Suchseite
und aktuelle Assets per HTTP bestätigt. Keine neuen Tests, Backendänderungen
oder Browserprüfung für diese Layoutänderung.

Vorangegangene Änderung: Suchhinweis „Das kann bis zu zwei Minuten dauern.“ und eine
Begrüßung in der ersten Chatnachricht nach der Suche. Der Server ergänzt nach der
Bewertung die tatsächliche Trefferzahl, die sichtbare Teilmenge ab 70 Punkten,
den Verweis auf die Ergebnisübersicht links und die Einladung zu Rückfragen.
Die ursprüngliche persönliche KI-Erklärung bleibt im nächsten Absatz erhalten.
Bei null sichtbaren Treffern wird keine sichtbare Stellenliste behauptet;
weniger passende Stellen können weiterhin eingeblendet werden.

Die Begrüßung wird einmal mit dem neuen Chat gespeichert. Keine zusätzliche
KI-Anfrage, keine geänderten Modelle, Scores oder Folgeantworten. Produktionsbuild
erfolgreich; lokaler Server neu gestartet und aktuelle Assets per HTTP geprüft.
**175 API-Tests bestanden.** Sie prüfen unter anderem gemischte, komplett sichtbare,
ausgeblendete, einzelne und leere Ergebnisse sowie gespeicherte Begrüßungen und
unveränderte Folgeantworten. Kein kostenpflichtiger Modell- oder Browsertest.

Vorangegangene Änderung: kompaktere Profilerstellung. Der kurze Button „Beispielprofil“
steht neben „Was passt zu dir?“, der Einleitungssatz entfällt. Vorlagen werden
über ein natives Dropdown gewählt; Name und Eingabe stehen in einer Zeile.
Die drei Vorlagen füllen weiterhin alle Felder, danach bleiben sie bearbeitbar.
Beschriftungen, Hinweise und Auswahlerfolg bleiben für Screenreader zugänglich.
Bedienelemente behalten mindestens 44 Pixel Höhe, schmale Container verwenden
kompakte Beschriftungen und flexible Eingabebreiten.

Produktionsbuild und alle **70 Frontend-Tests erfolgreich**. Profilkopf,
Bearbeitungsansicht und Standardpersönlichkeit plus drei Vorlagen per React-SSR
geprüft. Suchseite und aktuelle Assets per HTTP bestätigt.
Keine neuen Tests oder Backendänderungen für diese Layoutänderung.

Vorangegangene Änderung: KI-Sprechblasen, echtes Streaming und kompaktere Ergebnisse.
Die zusätzliche Persönlichkeits-Score-Zeile über den Stellen ist entfernt. Das
Such-Popup zeigt animierte Karten und eine Lichtspur ohne Zeitangabe oder
Hintergrund-Button. Auch im Chat ersetzt eine Punkteanimation den Sekundenzähler.

- GPT-5.4, Prompts, Ausgabegrenzen, Reasoning-Stufen und vollständige Begründungen
  für alle bis zu 20 Kandidaten bleiben erhalten.
- Responses-SDK-Streaming, strukturierte Zwischenstände, NDJSON-Transport und
  React-Vorschau verbunden. Keine zusätzliche API-Anfrage pro Nachricht.
- Vorschautext ändert keine Session. Ergebnisprüfung und optimistische Sperre
  gelten weiterhin; Abbruch/Fehler schließen den Upstream und speichern keine
  Teilantwort. Reine Fragen lösen weder neue Suche noch Neubewertung aus.
- **449 Backend-Tests bestanden, 1 optionaler Test übersprungen.** Darunter echte
  OpenAI-SDK-SSE-Verarbeitung mit simuliertem HTTP-Transport: frühe Textausgabe,
  Unicode/JSON-Escapes, Abbruch, 20 Stellen mit vollständigen Begründungen sowie
  unverändertes Modell und unveränderte Reasoning-Einstellungen.
- **70 Frontend-Tests bestanden**, inklusive Text vor Endergebnis, getrennten
  UTF-8-Bytes, Fehlern und unvollständigen Streams ohne automatisches Wiederholen.
- Produktionsbuild erfolgreich; beide Sprechblasen und der Suchdialog per React-SSR
  geprüft. Lokaler Server neu gestartet, Startseite, Suche, Modellkonfiguration,
  bereiter Index sowie aktuelle Build-Assets per HTTP bestätigt.
  Kein Browser- oder kostenpflichtiger Modelltest;
  die neuen Streaming-Tests verwenden kontrollierte Antworten.

Vorangegangene Änderung: Koffer-Icon bei „Jobs bewerten & sortieren“ in der Info
durch Lucides `ArrowDownWideNarrow` ersetzt: absteigende Balken mit Sortierpfeil.
Größe, Farbe und zugänglicher Begleittext bleiben erhalten. Produktionsbuild
erfolgreich; Suchseite und aktuelle Assets inklusive neuem Icon per HTTP geprüft.
Keine neuen Tests, Backendänderungen oder Browserprüfung für diesen Iconwechsel.
Änderungen bleiben lokal.

Vorangegangene Änderung: Info-Überschrift und zentrales Grafiklabel heißen
„KI-Suchpersönlichkeit“. Der Bereich „Jobs bewerten & sortieren“ erklärt ausdrücklich,
dass Nutzerprofil und KI-Persönlichkeit gemeinsam die Bewertung und Reihenfolge
bestimmen. Einleitung, fachlicher Vorrang, Gesprächsbereich und Pfeilverbindungen
bleiben erhalten; Beispiele und separater Hinweis bleiben entfernt.

Produktionsbuild erfolgreich. Beide Dialogvarianten per React-Server-Rendering
auf Titel, gemeinsame Bewertungsgrundlage und zwei Pfeile geprüft. Suchseite und
aktuelle Assets per HTTP geprüft; ausgelieferte Dateien entsprechen dem Build.
Keine neuen Tests, Backendänderungen, Modellaufrufe oder Browserprüfung für diese
Textänderung. Änderungen bleiben lokal.

Vorangegangene Änderung: Gewünschten Einleitungstext im Persönlichkeitsdialog exakt
zusammengeführt, einschließlich fachlicher Passung und Vorlagenhinweis. Der separate
Hinweis unter der Grafik entfällt. Grafik mit zentraler Persönlichkeit, Verbindungen
und zwei Pfeilen zu den farbigen Wirkungsbereichen wiederhergestellt. Die kurze
Überschrift und die Entfernung der Beispiele bleiben erhalten. Zwei Spalten und
Pfeile bleiben auch bei schmaler Darstellung verbunden; Dialoghöhe ist begrenzt
und der Inhalt bei Bedarf scrollbar.

Produktionsbuild erfolgreich. Beide Dialogvarianten per React-Server-Rendering
geprüft: exakter Einleitungstext, zusätzlicher Hinweis genau einmal in der Einleitung,
zwei Pfeile und zwei Wirkungsbereiche, keine Beispiele oder erzwungenen Titelumbrüche.
Suchseite und aktuelle Assets per HTTP geprüft; ausgelieferte Dateien entsprechen
dem Build. Keine neuen Tests, Backendänderungen, Modellaufrufe oder Browserprüfung.
Änderungen bleiben lokal.

Vorangegangene Änderung: Persönlichkeits-Einführung vereinfacht. Kurze Überschrift
„Deine Persönlichkeit“ ohne erzwungenen Zeilenumbruch und mit responsiver Schriftgröße.
Zwei farbige Bereiche mit Icons erklären in je einem Satz „Stellen bewerten“ und
„Mit dir sprechen“. Beispiele (einschließlich auskommentierter Reste), zusätzliche
Unterüberschrift, zentrale Wiederholung und Pfeilverzweigung entfernt. Die Grundlage
bleibt in einem kurzen Satz erklärt. Beide Bereiche stehen auch mobil in klarer
Lesereihenfolge untereinander. Vorlagenauswahl und Erstellungsfelder bleiben erhalten.

Produktionsbuild erfolgreich. Beide Dialogvarianten per React-Server-Rendering
geprüft: kurze Überschrift ohne `<br>`, genau zwei Wirkungsbereiche, keine Beispiele,
passender Bestätigungsbutton. Suchseite und aktuelle Assets per HTTP geprüft;
ausgelieferte Dateien stimmen mit dem Build überein. Keine neuen Tests,
Backendänderungen, Modellaufrufe oder Browserprüfung für diese Darstellungsänderung.
Änderungen bleiben lokal.

Vorangegangene Änderung: Die Persönlichkeitskonfiguration startet als eigene,
direkt bearbeitbare KI-Beratung. Drei optionale Vorlagen (Steve Jobs, Angela Merkel,
Günther Jauch) füllen Name, Bewertungsschwerpunkt, Gesprächseigenschaften und freie
Hinweise vollständig aus. Die Oberfläche sendet diese sichtbaren Werte als
`mode: custom`; nachträgliche Änderungen bleiben erhalten. Der frühere Moduswechsel
und die vier nicht bearbeitbaren Vorbildkarten sind entfernt. Alte Sitzungen
bleiben unverändert, bis ein Entwurf ausdrücklich angewendet wird; feste API-Presets
bleiben kompatibel. Die Backend-Formeln und Modellpfade sind unverändert.

Eine kurze native Dialog-Einführung vor dem ersten Wechsel zu Schritt 2 zeigt eine
HTML/CSS-Grafik mit zwei Wirkungen: ergänzende Gewichtung/Score/Reihenfolge sowie
Gesprächston/Rückfragen/Begründungen. Bestätigen öffnet die Erstellung, Schließen
oder Escape kehrt zum Profil zurück. Die Einführung ist über den Hilfelink erneut
aufrufbar und wird bei einem Rücksprung nicht automatisch wiederholt. „Neu starten“
setzt den Einführungsstatus zurück. Native Modalität, Fokus auf die Überschrift,
Schließen vor dem Schrittwechsel, zugängliche Beschriftungen, mobile Umbrüche und
begrenzte Dialoghöhe mit internem Scrollen sind im Quelltext berücksichtigt.
Formulierung und Feldhilfen verdeutlichen die Trennung von Suchprofil und Beratung.

**66 Frontend-Tests bestanden**, darunter fünf neue Regressionstests für Standard,
Vorlagenbefüllung, bearbeitete Felder, unabhängige Entwürfe und Legacy-Konvertierung.
**227 bestehende Python-Tests für Bewertung und LLM-Anbindung bestanden.** Zusätzlich
fünf tatsächlich aus den Frontend-Funktionen erzeugte Konfigurationen durch das
Python-Schema und zehn gemockte Chat-/Bewertungspfade geprüft: Eigenschaften,
Schwerpunkt und Freitext kommen unverändert an, Freitext bleibt außerhalb der
Systemanweisungen. Gegenläufige Lern-/Gestaltungsbelege ändern bei gleicher
Fachpassung die Reihenfolge entsprechend der jeweiligen Vorlage.

React-Server-Rendering mit Standard und allen drei Vorlagen geprüft: genau drei
Vorlagen, alle Eingabefelder sichtbar, keine alten Modus-Radios; Dialog enthält
beide Wirkungsbereiche und die Einstiegsaktion. Produktionsbuild erfolgreich.
Lokalen Server nach festgestelltem Stillstand neu gestartet; Health, vollständiger
Index (8.537 Anzeigen), Suchseite und exakte Build-Assets per HTTP geprüft.
Keine Browserprüfung und keine echten Modellaufrufe für diese Änderung.
Alle Änderungen bleiben lokal und uncommitted; kein weiterer GitHub-Push.

Vorangegangene Änderung (09.09.2026): Git-Repository für die Übergabe an
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

## Randomisierter Vergleich B/C

Gezielte Prüfungen für stabile serverseitige Zufallszuordnung, parallele Anfragen, Einwilligung/Widerruf, Schutz vor manipulierten Gruppenangaben, B-Neutralität bei Onboarding/Chat/Reranking/neuer Suche, C-Personalisierung, frühere Suchsitzungen, Autosave, Export und Gruppenfilter. SSR-Prüfung beider Einrichtungsabläufe und der gemeinsamen Ergebnisfragen. Es wurden keine echten Studienantworten oder kostenpflichtigen Modellaufrufe zu Testzwecken erzeugt.

## Verwaltung mit Diagrammen · 11. September 2026

24 gezielte Backendtests bestanden (Verwaltung, A/B-Fragebogen, Aggregation,
Versions-/Experimenttrennung, fehlende Werte, Legacy-Skalen, Zugriffsschutz,
Einzel- und Sammellöschung einschließlich veralteter Bestätigung und Widerruf).
135 Frontendtests bestanden; nach der Legacy-Skalenbeschriftung wurde der
Verwaltungs-Renderingtest erneut erfolgreich ausgeführt. Produktionsbuild erfolgreich.
Die Backendtests liefen wegen dataloser iCloud-Dateien in der Projekt-venv in
`/tmp/diana-admin-py312` mit den produktiven Versionen der benötigten Bibliotheken.

Server bereitgestellt und per HTTP geprüft: neues HTML/JS identisch zum Build;
Analytics für V1–V7 erfolgreich; sämtliche vorhandenen Einzelantworten abrufbar;
Analytics und Löschvorschau ohne Anmeldung gesperrt. Die fünf vor dem Deployment
abgeschlossenen Antworten sind anhand ihrer Inhaltsprüfsummen unverändert.
Keine tatsächliche Sammellöschung, keine neuen Modellanfragen und keine Browser-QA.
Prüfergebnis: `evaluation/admin-analytics-20260911/deployment-check.json`.

## Allgemeiner Chat A und Zufallsreihenfolge · 11. September 2026

Neue Zuordnungen: diana-ab-v2. Tests prüfen scoreunabhängige, reproduzierbare
Permutation ohne verlorene oder doppelte Karten; unveränderte Reihenfolge bei
Sessionabruf, Antworten und Neubewertung; neue Seeds bei Vollsuchen; unveränderte
personalisierte Sortierung; Neustart alter A-Sitzungen; tatsächliche allgemeine
Systemnachricht ohne fachliche Rollenregeln; keine Scores im Chatkontext; Antworten
über 600 Zeichen ohne maxLength und ohne max_output_tokens im API-Aufruf.
203 fokussierte Tests bestanden nach der letzten Änderung (LLM, Zufallsreihenfolge,
Verwaltung und Aggregation); die übrigen App-/Advisor-/Zuordnungstests des vorherigen
breiteren Laufs bestanden ebenfalls. 135 Frontendtests und Produktionsbuild bestanden.
Keine neuen echten Modellaufrufe durch die Prüfungen und keine Browser-QA.

Serverprüfung: allgemeiner Prompt SHA-256
`130eacc25cf219ef09e04a40d2512e104a25efe3300e123654d8f0377e6b3136`;
Antwortschema ohne maxLength; Experiment diana-ab-v2; HTML/JS identisch zum Build;
Analytics und CSV mit presentation_versions erfolgreich. Die fünf vor der
Bereitstellung abgeschlossenen Antworten sind unverändert erhalten geblieben.
Prüfprotokoll: `evaluation/generic-random-20260911/deployment-check.json`.

Ein-Satz-Prompt A (11. September 2026): sieben gezielte Tests bestanden. Die
vollständige Systemnachricht ist exakt `Du bist ein allgemeiner KI-Assistent.`;
kein zusätzlicher Systemtext und keine Antwortlängenbegrenzung. Produktionsbuild
und Serverimport bestätigt; Health 200, ausgeliefertes HTML identisch zum Build.
Darstellungsstand `random-order-generic-chat-v2` trennt diesen Promptstand von V1.
