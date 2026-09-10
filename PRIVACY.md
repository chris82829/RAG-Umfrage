# DIANA: Datenschutz-Umsetzung und offene Freigabepunkte

Stand: 10.09.2026. Dies ist eine technische Umsetzung mit einem Entwurf der
Studieninformation, keine rechtliche Bescheinigung der DSGVO-Konformität.
Der Datenschutzstand ist auf dem Server verfügbar. Die Betriebsfreigabe wird
über `/verwaltung` gesteuert und dauerhaft in SQLite gespeichert.
`privacy_settings.json: approved` ist der Anfangswert vor der ersten Admin-Änderung.

## Vom Studienleiter angegebene Rahmenbedingungen

- Auf ausdrücklichen Wunsch benennt die aktuelle Studieninformation ausschließlich
  Christoph Scharnagl als Verantwortlichen. Kontakt: christoph.scharnagl@th-nuernberg.de.
  Dies dokumentiert die Vorgabe des Studienleiters, keine unabhängige rechtliche
  Feststellung der Verantwortlichkeit.
- Zwecke: Promotion und weitere dokumentierte Forschung zu personalisierten
  Such-/Empfehlungssystemen, KI-Beratung und deren Nutzbarkeit.
- Vollständige Umfrage-Einzelantworten inklusive Freitext sollen über das Ende
  der Promotion hinaus nutzbar bleiben. Mindestens jährlich wird die weitere
  Erforderlichkeit je Datenart geprüft und dokumentiert. Keine pauschale Zusage
  unbegrenzter Speicherung und keine automatische Löschung zum Promotionsende.
- Die Freigabe zur Modellverbesserung im OpenAI-API-Projekt ist nach ausdrücklicher
  Bestätigung der Studienleitung ausgeschaltet. DIANA verwendet schon `store=False`.
  Das bedeutet nicht automatisch Zero Data Retention beim Anbieter.
- Neue Suchprofile und Chats werden im Produktivmodus ausschließlich in RAM
  gehalten: Ablauf nach einer Stunde ohne neue Such-/Chataktion, bei Widerruf
  oder Neustart. Die Fortsetzung benötigt einen einzelnen Gunicorn-Worker;
  Threads teilen dessen Speicher. Früher gespeicherte SQLite-Chats werden nicht
  mehr in neue Sitzungen geladen, aber **nicht ungefragt gelöscht**.

## Technische Schutzmaßnahmen

`/umfrage` und `/suche` laden die eigentliche Anwendung erst nach serverseitiger
Bestätigung. Auf der Vorstellungsseite werden keine Matching-API-Anfragen gestartet.
Die Checkbox ist leer, Ablehnen ist möglich. Am Einstieg stehen nur Kurztext,
Link zu `/datenschutz` und Einwilligungscheckbox. Die vollständigen Hinweise
öffnen über den Link in einem neuen Tab; ein Öffnen wird nicht erzwungen oder
als tatsächliches Lesen protokolliert. Die Checkbox bestätigt die Kenntnisnahme
und erteilt ausdrücklich die freiwillige Einwilligung einschließlich OpenAI-Verarbeitung.
Die vollständigen Hinweise und der Impressumslink bleiben ohne Anmeldung erreichbar.

Ein zufälliger 256-Bit-Zugangscode liegt im Sitzungsspeicher und wird ausschließlich
in `X-Diana-Consent`, nicht in einer URL gesendet. Der Server speichert nur dessen
SHA-256-Hash, die genaue Informationsfassung, deren Hash und den UTC-Zeitpunkt.
Keine IP oder Browserkennung werden als Einwilligungsnachweis gespeichert.
Serverseitige Prüfung schützt Suche, Onboarding, Chat, Sitzungszugriff und
Umfrageabgabe; bloßes Umgehen der Oberfläche reicht nicht. Änderungen der
Informationen invalidieren bisherige Einwilligungen für neue Verarbeitung.

Die Antworttabelle bleibt beim bestehenden CSV-Schema. Eine separate Tabelle
ordnet Teilnahme und vorübergehende Sitzungskennung dem Einwilligungsnachweis zu.
Die Daten sind **pseudonymisiert, nicht anonym**. Kontrollen auf Besitz und
Transaktionen verhindern Zugriff durch fremde Einwilligungscodes sowie ein
erneutes Speichern von Antworten nach Widerruf.

„Datenschutz & Widerruf“ bleibt erreichbar. Der Widerruf sperrt die Einwilligung,
löscht zugeordnete Antworten aus der aktiven Datenbank, beendet die RAM-Sitzungen
und entfernt Entwürfe im Browser. Bereits laufende OpenAI-Verarbeitung kann nicht
rückwirkend ungeschehen gemacht werden. Exportkopien, Sicherungen und Anbieter-
Daten müssen über die Studienleitung gesondert behandelt werden. Eine davon getrennte öffentliche Teilnahme-ID kann kopiert und für eine Löschanfrage
an die Studienleitung geschickt werden. Der geheime Zugangscode wird nicht angezeigt.
Die öffentliche ID allein erlaubt keinen API-Zugriff.

Ein Abschluss ist ausschließlich eine bewusste Verwaltungsaktion:
`flask --app app:create_app privacy-end-study --confirm` schließt die Studie und
löscht Antworten und Einwilligungsnachweise. **Nicht ausgeführt, nicht geplant und
nicht an das Promotionsende gekoppelt.** Exporte/Backups erfasst der Befehl nicht.

## Vor tatsächlichem Studienbetrieb klären und dokumentieren

1. Die rechtliche Zuordnung von Doktorand/Institut und, falls zutreffend, die
   Vereinbarung gemeinsamer Verantwortung nach Art. 26 DSGVO, inklusive
   Betroffenenrechte und wesentlichem Inhalt für Teilnehmende. Ein Institut ist
   nicht automatisch eine eigene juristische Person. Die Benutzerangabe wird
   nicht als Prüfung dieser Zuständigkeit dargestellt.
2. Vertragspartner der OpenAI-Nutzung, Auftragsverarbeitung, Unterauftragnehmer,
   tatsächliche Verarbeitungsorte und einschlägige Drittlandgarantien. Training
   deaktiviert ersetzt diese Prüfung nicht. Die gegenwärtigen allgemeinen
   Anbieterinformationen sind keine Bestätigung der Kontokonfiguration/Verträge.
3. Transportverschlüsselung und Infrastrukturprotokolle/Fristen. Die bisherige
   Serveradresse verwendet HTTP auf Port 5051; VPN-Zugang allein belegt keine
   durchgehende Transportabsicherung. Gunicorn-Zugriffslogs sind abgeschaltet,
   andere Infrastrukturprotokolle wurden nicht geprüft.
4. Rollen/Zugriffsrechte, Umgang mit CSV-Exporten und Backups, Löschung historischer
   Chatbestände sowie Dokumentation der mindestens jährlichen Erforderlichkeits-
   prüfung. Es wurde keine automatische Anonymisierung behauptet oder durchgeführt.
5. Verbindliche Texte in `privacy_settings.json` pflegen und ausrollen. Die
   Teilnahme wird unabhängig davon in `/verwaltung` freigegeben oder pausiert.
   Die Betriebsfreigabe ist keine automatische Prüfung der rechtlichen Inhalte.

## Quellen

- [Gewünschtes Impressum](https://www.hochschuljobboerse.de/impressum)
- [Datenschutzkontakt TH Nürnberg](https://www.th-nuernberg.de/datenschutz/)
- [DSGVO, insbesondere Art. 5, 7, 13, 26, 28, 32, 44 ff. und 89](https://eur-lex.europa.eu/legal-content/DE-EN/ALL/?from=EN&uri=CELEX%3A32016R0679)
- [EU-Kommission: Grundsätze, einschließlich Forschungsaufbewahrung](https://commission.europa.eu/law/law-topic/data-protection/information-business-and-organisations/principles-gdpr_en)
- [BayLfD: Aufbewahren von Einwilligungen](https://datenschutz-bayern.de/datenschutzreform2018/aki08.html)
- [OpenAI: API-Datenkontrollen](https://developers.openai.com/api/docs/guides/your-data)

## Löschanfrage anhand der Teilnahme-ID

Die ID hat das Format `DIANA-xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx`. Sie bleibt bei
Wiederholungen gleich, steht im Abschlussbildschirm und ist während der Teilnahme
über „Teilnahme-ID & Datenschutz“ erreichbar. Dort gibt es einen Kopierknopf und
einen vorbereiteten E-Mail-Link. E-Mails werden nur durch die Person selbst versendet.
Der CSV-Export verwendet für neue Teilnahmen dieselbe ID in der ersten Spalte;
ältere Antworten behalten ihre ursprüngliche Antwort-ID.

Nach dem Ausrollen kann die Studienleitung gezielt prüfen und löschen:

```bash
# Vorschau, keine Löschung:
docker compose exec -T app flask --app app:create_app privacy-delete --participation-id DIANA-...
# Nach Prüfung der Anfrage:
docker compose exec -T app flask --app app:create_app privacy-delete --participation-id DIANA-... --confirm
```

Die Aktion löscht nur Antworten dieser ID und widerruft die zugehörige Einwilligung.
Der minimale Nachweis samt Widerrufszeitpunkt bleibt für die Nachweisverwaltung;
seine weitere Aufbewahrung wird ebenfalls regelmäßig geprüft. Exportkopien und
Sicherungen müssen separat anhand derselben ID bereinigt werden. Bei Ausführung
als separater CLI-Prozess werden aktive RAM-Sitzungen im Webprozess sofort für
weitere Zugriffe/Änderungen gesperrt und spätestens beim Ablauf oder Neustart
entfernt; der CLI-Prozess greift nicht auf den RAM eines anderen Prozesses zu.
Unbekannte IDs lösen keine Löschung aus. Die öffentliche ID wird nicht als
Zugangsberechtigung zu einer Antwort akzeptiert.

## Geschützte Ergebnisverwaltung

`/verwaltung` bietet nach eigener Passwortanmeldung Einzelansichten, Numiqo-Export
und gezielte Löschung. Details zu Zugang, Exportkopien und Löschumfang stehen in
ADMIN.md. Neue Antworten erhalten einen technischen Systemstand (Modellversion,
Einstellungen und Prüfsummen); die Datenschutzhinweise nennen diese Zuordnung.
Sie enthält keine zusätzlichen Such- oder Chattexte und wird beim Widerruf
zusammen mit der zugehörigen Antwort gelöscht. Globale Systemmanifeste ohne
Teilnehmerdaten bleiben für die wissenschaftliche Dokumentation erhalten.


Fortlaufende Umfrageentwürfe werden vor dem Abschluss auf dem Studienserver gespeichert.
Der Datenschutzhinweis nennt Teilantworten bei Abbruch. Entwürfe sind an dieselbe
Einwilligung und Teilnahme-ID gebunden und in Löschung, Widerruf und Studienende
enthalten. Bei erneuter ausdrücklicher Zustimmung zu geänderten Hinweisen bleibt die
Teilnahme-ID erhalten; frühere Einwilligungsfassungen liegen in `privacy_consent_history`.
Widerrufene Zugänge können dadurch nicht reaktiviert werden.
