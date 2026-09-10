"""Versioned study configuration, without applicant inputs or conversation text."""
import hashlib
import importlib.metadata
import json
import platform
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

from llm_service import MODEL, REASONING_EFFORT, MAX_OUTPUT_TOKENS, RERANK_OUTPUT_TOKENS
from retrieval import MODEL_ID, MODEL_REVISION, CACHE_VERSION, RRF_K, LEG_LIMIT


def canonical(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(',', ':'))


class StudyReleases:
    def __init__(self, path, root, jobs):
        self.path = path
        files = ['llm_service.py', 'advisor.py', 'retrieval.py', 'schemas.py', 'app.py',
                 'data_store.py', 'survey_store.py', 'survey_definition_v3.json', 'survey_definition_v4.json', 'survey_definition_v5.json', 'study_assignment.py', 'advisor.py', 'survey_definition.json', 'requirements.txt', 'requirements-server.txt',
                 'web-dist/index.html']
        sources = {name: hashlib.sha256((root/name).read_bytes()).hexdigest() for name in files if (root/name).is_file()}
        packages = {}
        for name in ['openai','pydantic','sentence-transformers','torch','transformers','numpy','rank-bm25','Flask']:
            try: packages[name] = importlib.metadata.version(name)
            except importlib.metadata.PackageNotFoundError: packages[name] = None
        manifest = dict(format_version=1, openai_model=MODEL, reasoning_effort=REASONING_EFFORT,
                        response_store=False, max_output_tokens=MAX_OUTPUT_TOKENS,
                        rerank_output_tokens=RERANK_OUTPUT_TOKENS, embedding_model=MODEL_ID,
                        embedding_revision=MODEL_REVISION, embedding_preprocessing=CACHE_VERSION,
                        rrf_k=RRF_K, retrieval_top_k=LEG_LIMIT, source_sha256=sources,
                        python=platform.python_version(), packages=packages,
                        job_count=len(jobs), job_data_sha256=hashlib.sha256(canonical(sorted(jobs,key=lambda job:str(job['id']))).encode()).hexdigest(),
                        reproducibility_note='Fixed model and configuration do not guarantee identical generative outputs. No personal search inputs or chats are archived.')
        self.release_id = hashlib.sha256(canonical(manifest).encode()).hexdigest()
        self.manifest = {**manifest, 'release_id': self.release_id}
        with sqlite3.connect(path) as db:
            db.executescript('''CREATE TABLE IF NOT EXISTS study_releases (id TEXT PRIMARY KEY, created_at TEXT NOT NULL, manifest_json TEXT NOT NULL);
                CREATE TABLE IF NOT EXISTS study_runs (token_hash TEXT NOT NULL, release_id TEXT NOT NULL, PRIMARY KEY(token_hash, release_id));
                CREATE TABLE IF NOT EXISTS survey_response_metadata (submission_id TEXT PRIMARY KEY, metadata_json TEXT NOT NULL);''')
            db.execute('INSERT OR IGNORE INTO study_releases VALUES (?, ?, ?)',
                       (self.release_id, datetime.now(timezone.utc).isoformat(), canonical(self.manifest)))

    def mark_run(self, digest, db):
        db.execute('INSERT OR IGNORE INTO study_runs VALUES (?, ?)', (digest, self.release_id))

    def capture_response(self, digest, submission_id, db):
        ids = [row[0] for row in db.execute('SELECT release_id FROM study_runs WHERE token_hash=? ORDER BY release_id',(digest,))]
        previous = db.execute('SELECT metadata_json FROM survey_response_metadata WHERE submission_id=?', (submission_id,)).fetchone()
        if previous:
            ids = sorted(set(ids) | set(json.loads(previous[0]).get('release_ids', [])))
        db.execute('INSERT INTO survey_response_metadata VALUES (?, ?) ON CONFLICT(submission_id) DO UPDATE SET metadata_json=excluded.metadata_json', (submission_id, canonical({'release_ids':ids})))

    def all(self):
        with sqlite3.connect(self.path) as db:
            return {row[0]:json.loads(row[1]) for row in db.execute('SELECT id,manifest_json FROM study_releases')}
