#!/usr/bin/python3
"""Daily consistent SQLite snapshot, with seven-day retention on this host."""
import datetime
import os
from pathlib import Path
import sqlite3
import time

os.umask(0o077)
root = Path('/opt/diana-survey')
backups = root / 'backups' / 'daily'
backups.mkdir(mode=0o700, parents=True, exist_ok=True)
stamp = datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%SZ')
output = backups / f'jobs-{stamp}.sqlite3'
with sqlite3.connect(f'file:{root}/runtime/instance/jobs.sqlite3?mode=ro', uri=True) as src:
    with sqlite3.connect(output) as dst:
        src.backup(dst)
        if dst.execute('PRAGMA integrity_check').fetchone()[0] != 'ok':
            raise RuntimeError('Database backup failed integrity check')
for previous in backups.glob('jobs-*.sqlite3'):
    if previous.stat().st_mtime < time.time() - 7 * 86400:
        previous.unlink()
print(f'Verified database backup: {output.name}')
