"""Idempotent, non-destructive questionnaire V12 migration.

Run: python survey_migrations.py /path/to/surveys.sqlite3
Historical JSON records and their original question keys remain unchanged. Generated
columns expose the three V12 integer ratings to SQL without a second write source.
An unanswered or explicitly unassessable item is SQL NULL, never zero.
"""
from __future__ import annotations

import argparse
from pathlib import Path

USEFULNESS_ITEMS = ('usefulness_effective', 'usefulness_speed', 'usefulness_overall')


def migrate_v12(db):
    """Caller owns the transaction; safe repeatedly on existing or new stores."""
    for table in ('survey_responses', 'survey_drafts'):
        columns = {row[1] for row in db.execute(f'PRAGMA table_xinfo({table})')}
        if not columns:
            continue
        for name in USEFULNESS_ITEMS:
            if name in columns:
                continue
            db.execute(f'''ALTER TABLE {table} ADD COLUMN {name} INTEGER
                GENERATED ALWAYS AS (CASE
                    WHEN json_extract(answers_json, '$.version') = 'diana-v12'
                      AND json_type(answers_json, '$.{name}') = 'integer'
                    THEN json_extract(answers_json, '$.{name}') ELSE NULL END) VIRTUAL
                CHECK ({name} IS NULL OR {name} BETWEEN 1 AND 5)''')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('database', type=Path)
    args = parser.parse_args()
    # Initialize empty DBs and run the exact migration used during application startup.
    from survey_store import SurveyStore
    SurveyStore(args.database)
    print('V12 migration applied; existing versioned answers preserved.')


if __name__ == '__main__':
    main()
