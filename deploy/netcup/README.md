# Öffentliche DIANA-Installation bei netcup

Seit 18.09.2026 auf `159.195.48.19`, Verzeichnis `/opt/diana-survey`.
Ausgangspunkt ist die tatsächlich laufende Hochschulinstallation mit
`DEPLOYED_COMMIT=1f75d03`. Anwendung, gebautes Frontend, Docker-Image,
Modellcache und eine konsistente SQLite-Kopie werden übernommen.
Die alte Installation wird nicht ersetzt. Beide Datenbanken sind danach
unabhängig; neue Antworten werden nicht zwischen den Servern synchronisiert.

## Adressen

- Start: https://159.195.48.19/
- Umfrage: https://159.195.48.19/umfrage
- Verwaltung: https://159.195.48.19/verwaltung
- Testvarianten: https://159.195.48.19/test/a, /test/b, /test/c
- Datenschutz: https://159.195.48.19/datenschutz

Der mitgelieferte `megasrv.de`-Hostname zeigte bei der Einrichtung auf eine
andere IPv4-Adresse. Deshalb verwendet diese Installation direkt die öffentliche
IPv4 mit einem vertrauenswürdigen Let's-Encrypt-Zertifikat. Es ist kein VPN
und keine Browserausnahme für Zertifikate erforderlich.

## Aufbau und Zugang

Debian 13, Docker Engine und Compose. Caddy veröffentlicht ausschließlich
80/TCP sowie 443/TCP+UDP und leitet HTTP auf HTTPS um. Die Python-Anwendung
hat keinen öffentlichen Port und ist nur im Docker-Netz erreichbar.
Ein Worker hält das E5-Modell im Speicher; 16 Threads bedienen Anfragen.
Der Container ist auf 6 CPUs und 12 GB RAM begrenzt und läuft als UID 10001.
Das ersetzt keinen Lasttest gleichzeitiger KI-Suchen; OpenAI-Limits gelten weiter.

Auf dem eingerichteten Mac genügt `ssh diana-netcup`. Der Alias verwendet
`~/.ssh/id_ed25519_diana_netcup`. Der private Schlüssel bleibt ausschließlich
auf dem Mac und gehört weder ins Repository noch in E-Mails. SSH-Anmeldung
per Passwort ist abgeschaltet; der Schlüssel wurde vor dieser Änderung geprüft.
Bei Verlust des Schlüssels ist die netcup-SCP-Konsole der Wiederherstellungsweg.
Die Verwaltung übernimmt den Passwort-Hash aus der alten Serverkonfiguration.

Die Firewall erlaubt SSH und HTTP/HTTPS. Debian-Sicherheitsupdates laufen
automatisch, automatische Neustarts sind deaktiviert. Docker und die Container
starten beim Serverstart. Container-Images werden bei einer bewussten Wartung
aktualisiert, nicht mitten in einer Teilnahme.

## Zertifikat

Caddy verwaltet ein öffentliches Let's-Encrypt-IP-Zertifikat mit dem Profil
`shortlived` und erneuert es selbstständig. IP-Zertifikate sind rund 160 Stunden
gültig. Die Zertifikate und der ACME-Zugang bleiben in den Docker-Volumes
`diana-public_caddy_data` und `diana-public_caddy_config` erhalten.
**Kein `docker compose down -v` verwenden:** Das würde diese Daten löschen.

`default_sni` ist für IP-Zugriffe ohne SNI gesetzt. Der Proxy reicht Streaming
sofort weiter. `proxy_wsgi.py` vertraut genau diesem einen Proxy, damit sichere
Admin-Cookies und die Login-Begrenzung die korrekten Verbindungsdaten nutzen.
Die Anwendung darf deshalb nicht zusätzlich direkt öffentlich veröffentlicht werden.

Quellen: [Caddy-Zertifikatsverwaltung](https://caddyserver.com/docs/automatic-https),
[Let's Encrypt IP-Zertifikate](https://letsencrypt.org/2026/01/15/6day-and-ip-general-availability).

## Betrieb und Updates

```bash
ssh diana-netcup
cd /opt/diana-survey
docker compose -f deploy/netcup/compose.yaml ps
docker compose -f deploy/netcup/compose.yaml logs --tail 80 app
curl --fail https://159.195.48.19/api/health
```

Für Codeänderungen lokal das Frontend neu bauen und die Laufzeitdateien wie in
der Projekt-README übertragen. Zusätzlich `deploy/netcup/` übertragen.
Die Serverdatei `.env`, `runtime/`, `backups/` und Zertifikat-Volumes behalten.
Anschließend auf dem neuen Server:

```bash
cd /opt/diana-survey
systemctl start diana-backup.service
docker compose -f deploy/netcup/compose.yaml config --quiet
docker compose -f deploy/netcup/compose.yaml up -d --build
curl --fail https://159.195.48.19/api/health
```

Bei Änderungen am Caddyfile:

```bash
docker compose -f deploy/netcup/compose.yaml exec caddy caddy validate --config /etc/caddy/Caddyfile
docker compose -f deploy/netcup/compose.yaml exec caddy caddy reload --config /etc/caddy/Caddyfile
```

## Daten, Sicherungen und Protokolle

`runtime/instance/jobs.sqlite3` enthält Stellen, Umfrageantworten, Entwürfe,
Zuordnungen und Einwilligungen. Suchsitzungen der aktuellen Anwendung liegen
im RAM und enden beim Neustart. Die Migration übernimmt auch vorhandene
historische Datenbanktabellen, ohne sie zu bereinigen.

`diana-backup.timer` erstellt täglich eine konsistente SQLite-Sicherung und
prüft ihre Integrität. Dateien liegen unter `backups/daily/` mit Root-Zugriff
und werden nach sieben Tagen entfernt. Diese lokale Sicherung schützt vor
Fehlbedienung, nicht vor dem Verlust des gesamten Servers; Forschungsdaten
zusätzlich regelmäßig über die Verwaltung exportieren und sicher aufbewahren.

```bash
systemctl list-timers diana-backup.timer
systemctl start diana-backup.service
journalctl -u diana-backup.service --no-pager -n 10
```

Web-Zugriffslogs sind aus. Caddys HTTP-Fehlerlogs mit vollständigen Requestdaten
sind ebenfalls deaktiviert. Allgemeine Container-Betriebslogs sind auf je
3 × 10 MB begrenzt; Systemlogs auf 14 Tage und 200 MB. Die Infrastrukturangaben
werden über die lokale `privacy_settings.json` dieser Installation eingebunden.
Bestehende Einwilligungsnachweise behalten ihren ursprünglichen Wortlaut.
Neue Teilnahmen akzeptieren den für diese Installation aktualisierten Hinweis.

Vor Vertragsende Antworten exportieren und erforderliche Daten sowie
Konfigurationen sichern. Durch die Kündigung wird der Server einschließlich
seiner ausschließlich dort liegenden Sicherungen gelöscht.
