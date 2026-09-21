# Interaktionsereignisse ab V12

Die Erfassung ist zusätzlich zu den bereits vorhandenen aggregierten Operationsmetriken aktiviert. Sie beginnt erst mit gültiger Einwilligung in die aktualisierten Datenschutzhinweise. Standalone-Tests auf `/test/a`, `/test/b` und `/test/c` schreiben keine Studienereignisse.

## Ereignisse

| event_type | Bedeutung | Metadaten |
|---|---|---|
| dwell_justification | Sichtbare Betrachtungsdauer eines Begründungsbereichs, in Teilintervallen | job_id, rank, duration_ms |
| job_expand | Weitere Begründungen einer Stelle aufgeklappt | job_id, rank |
| job_detail | Stellendetails geöffnet | job_id, rank |
| chat_turn | Erfolgreicher, serverseitig gespeicherter Chatdurchgang | successful_chat_count |

`rank` ist die beim Ereignis angezeigte Position (1–20), nicht ein Qualitätsurteil. Eine Stelle muss zum Zeitpunkt der Übermittlung zur serverseitigen Suchsitzung gehören. Der Zeitstempel ist der UTC-Eingangszeitpunkt am Server; bei Betrachtungsintervallen ist er also nicht der Beginn des Intervalls. IDs binden Ereignisse an die pseudonyme Teilnahme und die konkrete Suchsitzung. Profil-, Chat-, Persönlichkeits- und Begründungstexte werden nicht gespeichert.

Ein `chat_turn` wird in derselben Transaktion wie der erfolgreiche Chat aus `study_operation_metrics.successful_chat_count` abgeleitet. Ein fehlgeschlagener oder zurückgerollter Vorgang erzeugt kein Ereignis. Wiederholungen desselben Schreibvorgangs sind anhand der Erfolgsnummer dedupliziert. Die Erfolgsnummer gilt über mehrere Suchsitzungen derselben Teilnahme hinweg. Nach einer Einführung der Erfassung kann sie aufgrund früherer Chats höher als 1 starten. Clientseitige `chat_turn`-Ereignisse werden verworfen.

## Definition der Betrachtungsdauer und Grenzen

Mindestens die Hälfte des Begründungsbereichs muss sichtbar sein; bei langen Begründungen genügt ein Bereich von einer halben Ansichtshöhe. Browser-Tab und eingebettete Systemansicht müssen sichtbar sein. Lade-/Fragenfenster, ausgeblendete Ansichten und Hintergrund-Tabs pausieren die Messung. Sichtbarkeit wird zusätzlich alle 250 ms geprüft. Es wird spätestens alle 15 Sekunden, beim Ausblenden und beim Verlassen ein Teilintervall übermittelt. Einzelintervalle sind auf 60 Sekunden begrenzt. `keepalive` und ein einmaliger Wiederholungsversuch mit derselben Ereignis-ID vermindern Datenverlust und vermeiden doppelte Zeilen.

Die Erfassung ist **best effort**: Verbindungsabbrüche, geschlossene Browser, ausgeschaltetes JavaScript oder abgelaufene Sitzungen können zu fehlenden Ereignissen führen. Fehlende Zeilen bedeuten deshalb nicht sicher „nicht benutzt“. Sichtbarkeit ist kein Nachweis, dass ein Text tatsächlich gelesen wurde. Gleichzeitig sichtbare Stellen können überlappende Intervalle erzeugen; ihre Summe ist keine gesamte Sitzungsdauer. Lange Verweildauer oder viele Klicks sind keine eigenständigen Qualitätsmaße. Für Auswertungen beachten, dass die drei vorgegebenen erfolgreichen Chatnachrichten ein Studienprotokoll und kein Maß für freiwilliges Engagement darstellen.

Es gibt maximal 10.000 clientseitige Ereignisse pro Teilnahme; erfolgreiche Chatereignisse sind davon ausgenommen. Clientangaben werden hinsichtlich Typ, Wertebereich und Zugehörigkeit geprüft, bleiben dennoch nutzerseitige Beobachtungen. Ein manipulierter Browser kann keine verlässliche Messung echter Aufmerksamkeit liefern.

## Speicherung, Löschung und Export

`migrations/012_study_telemetry.sql` legt die Tabelle `track_events` additiv und wiederholt ausführbar an. Der Laufzeit-Initializer ergänzt Löschtrigger auf `privacy_consents`. Widerruf, administratives Löschen einer Teilnahme und das Beenden der Studie löschen die zugehörigen Ereignisse. Sie werden nicht allein beim Löschen einer temporären Suchsitzung entfernt, da die Forschungsteilnahme weiter bestehen kann.

Der geschützte Telemetrie-CSV-Export enthält Teilnahme-ID, Suchsitzung, Ereignis, UTC-Zeit und aufgeteilte Metadaten. Er enthält keine Einwilligungstoken oder deren Hashes. Dieselben Teilnahmefilter wie bei den Antworten erlauben die Trennung abgeschlossener und unvollständiger Teilnahmen. Die `capture_version` kennzeichnet die Messdefinition; aktuell 1. Historische Teilnahmen ohne Ereignisse dürfen nicht ohne Kennzeichnung mit vollständig erfassten Teilnahmen gleichgesetzt werden.
