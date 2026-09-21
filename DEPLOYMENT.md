> Aktueller Datenschutz- und Verwaltungsstand am 10.09.2026 ausgerollt.
> Die Auswertung ist passwortgeschützt erreichbar. Die Teilnahme wird unter
> /verwaltung mit „Umfrage freigeben“ bzw. „Umfrage pausieren“ gesteuert.

# DIANA auf dem Forschungsserver

Ziel: `master@ifaiforschung.informatik.fh-nuernberg.de`, Verzeichnis
`/home/master/diana-survey`, eigenes Compose-Projekt `diana-survey`.
Webadresse im Hochschul-VPN: `http://ifaiforschung.informatik.fh-nuernberg.de:5051/`.
Der Container verwendet intern Port 5050. Bestehende Projekte, Ports und deren
Reverse-Proxy-Konfiguration werden nicht verändert.

## Betrieb

Im Server-Verzeichnis:

```bash
docker compose ps
docker compose logs --tail 100 app
docker compose restart app
docker compose exec -T app flask --app app:create_app survey-export --output /data/instance/umfrage.csv
```

Der CSV-Export überschreibt keine vorhandene Datei; für weitere Exporte einen
neuen Dateinamen wählen. Exportdateien liegen auf dem Host unter
`runtime/instance/`. Datenbank, Umfrageantworten, historische Chat-Daten, Vektorcache und
Modell bleiben im eingebundenen Verzeichnis `runtime/` bei Containerwechseln
erhalten. `runtime/` regelmäßig sichern, SQLite dabei über dessen Backup-API
kopieren oder den DIANA-Container für die Dateikopie kurz anhalten.

Zum Herunterladen eines erstellten Exports auf dem eigenen Rechner ausführen:

```bash
scp master@ifaiforschung.informatik.fh-nuernberg.de:/home/master/diana-survey/runtime/instance/umfrage.csv ~/Downloads/
```

Die CSV lässt sich in Excel öffnen (UTF-8, Semikolon als Trennzeichen).
Erfasst werden nur vollständig abgesendete Fragebögen; noch offene Entwürfe
sind nicht enthalten. Bei einem anderen Exportnamen diesen auch im Downloadbefehl
anpassen. Ein Export von der lokalen DIANA-Installation enthält nicht die
Antworten der Server-Umfrage.

Die Server-Datei `.env` hat Modus 0600 und enthält den API-Schlüssel sowie
`DIANA_UID=1002`, `DIANA_GID=1002`, `DIANA_PORT=5051` und den CORS-Ursprung.
Sie gehört weder ins Git-Repository noch ins Docker-Image. `.dockerignore`
begrenzt den Build-Kontext auf Anwendung, Abhängigkeiten und fertiges Frontend.
Der Container läuft ohne Root-Rechte, mit maximal 6 CPUs und 12 GB RAM.

## Aktualisieren

Zuerst das lokale React-Frontend mit `pnpm build` bauen. Anschließend die
Anwendungsdateien, `web-dist`, `.dockerignore`, `Dockerfile`, `requirements*.txt`, `compose.yaml`
und `gunicorn.conf.py` ins Server-Verzeichnis übertragen. `.env` und `runtime/`
auf dem Server bei Updates behalten. Dort:

```bash
docker compose config --quiet
docker compose up -d --build
docker compose ps
```

Ein Gunicorn-Worker mit vier Threads hält genau ein E5-Modell im Speicher. Vor
dem Annehmen von Anfragen lädt er das Modell und prüft die Vektorsuche für den
vorhandenen Datenbestand, ohne einen GPT-Aufruf auszulösen. CPU-PyTorch und die
Embedding-Bibliotheken sind festgelegt; der vollständige Modell-Snapshot liegt
unter `runtime/huggingface` und wird offline geladen.

Die Ersteinrichtung übernimmt 8.537 Stellen und deren Vektoren. Lokale Chats und
Umfrageantworten werden nicht übernommen. Die Modell-Prüfsumme SHA-256 lautet
`dd6b6e4f52db0a7aff83a13d10e6c5342ef9f6ab799bad3221f4b35ef390fa85`.
GPT verwendet den festen Snapshot `gpt-5.4-2026-03-05` mit `reasoning.effort=none`.

## Umfrageverwaltung

http://ifaiforschung.informatik.fh-nuernberg.de:5051/verwaltung

Kein Nutzername; Anmeldung nur mit dem separat festgelegten Passwort. Der
Server speichert dessen Werkzeug-Hash als einfach gequoteten Wert
`DIANA_ADMIN_PASSWORD_HASH` in `.env` (verhindert Compose-Interpolation von `$`).
Nach Änderung der Umgebungsdatei `docker compose up -d --no-deps app` ausführen;
`restart` allein übernimmt geänderte Umgebungsvariablen nicht.
CSV für Numiqo sowie Codebuch und Systemmanifest sind nach Anmeldung verfügbar.

Bei der Aktualisierung blieb die vorhandene Antwort erhalten. Sicherungen vor
diesem Update: `backups/pre-admin-20260910/application.tar.gz` und
`runtime/instance/pre-admin-20260910.sqlite3`; vorheriges Containerimage:
`diana-survey-app:pre-admin-20260910`. Die Sicherungen enthalten ggf. alte
Zugangsdaten bzw. Forschungsdaten und sind bei Löschanfragen mit zu berücksichtigen.
Neue produktive Such-/Chatsitzungen liegen nur im RAM und enden beim Neustart.

Die Freigabe wird in `privacy_lifecycle` in SQLite gespeichert. Ein Containerwechsel
setzt sie nicht zurück; `.env` und Konfigurationsdateien müssen dafür nicht mehr
geändert werden. Die Einwilligung selbst bleibt vor jeder neuen Teilnahme erforderlich.
