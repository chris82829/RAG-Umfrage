"""Explicit opt-in, eight paid calls on synthetic data; not a ranking benchmark.

Run from the repository: python research/development/2026-09-18-ranking-followups/smoke_test.py --live
Writes responses for manual inspection; never uses participant data.
"""
import argparse
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
from dotenv import load_dotenv
from app import merge_profile
from llm_service import ADVISORY_VERSION, MODEL, OpenAIService, REASONING_EFFORT
from persona_mlds import load_templates
from schemas import Profile

PROFILE = Profile(query='Werkstudent Datenanalyse', skills=['Python', 'SQL'],
                  filters={'employment_types': ['werkstudent']}).model_dump()
JOBS = [
    dict(id='synthetic-pipeline', title='Werkstudent Datenpipelines', company='Testfirma Pipeline',
         tasks='Datenpipelines mit Python und SQL entwickeln und testen.', requirements='Python und SQL.',
         benefits='Feste fachliche Betreuung mit wöchentlichem Mentoring.', remote='hybrid',
         employment_types=['werkstudent'], hours_min=16, hours_max=20),
    dict(id='synthetic-model', title='Werkstudent Modellierung', company='Testfirma Modell',
         tasks='Mit Python und SQL Daten aufbereiten und Vorhersagemodelle trainieren.', requirements='Python und SQL.',
         benefits='Eigenständige Verantwortung für ein kleines Modellierungsprojekt.', remote='onsite',
         employment_types=['werkstudent'], hours_min=16, hours_max=20),
]
QUESTIONS = {
    'career': 'Was ist dir wichtiger: eigenständige Projektverantwortung oder feste fachliche Betreuung?',
    'expert': 'Möchtest du lieber Datenpipelines entwickeln oder Vorhersagemodelle trainieren?',
}
REPLIES = {'career': 'Das Erste.', 'expert': 'Lieber Datenpipelines.'}


def run_role(role):
    model = OpenAIService(os.environ['OPENAI_API_KEY'])
    advisor = load_templates()[role]['advisor']
    candidates = [{'job': job} for job in JOBS]
    initial = model.rerank({}, PROFILE, candidates, advisor=advisor)
    history = [{'role': 'assistant', 'content': QUESTIONS[role]}]
    decision = model.plan_chat(PROFILE, history, REPLIES[role], jobs=JOBS, advisor=advisor)
    changed = merge_profile(PROFILE, decision['profile_patch'])
    updated = model.rerank({}, changed, candidates, advisor=advisor,
                          chat_message=REPLIES[role], chat_context={'messages': history})
    if role == 'career':
        edge_message = 'Weiß ich noch nicht.'
        edge = model.plan_chat(PROFILE, history, edge_message, jobs=JOBS, advisor=advisor)
        edge_ok = edge['action'] == 'answer' and merge_profile(PROFILE, edge['profile_patch']) == PROFILE
    else:
        edge_message = 'Warum passt die Datenpipeline-Stelle zu mir?'
        edge = model.plan_chat(changed, history, edge_message, jobs=JOBS, advisor=advisor, follow_up_allowed=False)
        edge_ok = '?' not in edge['assistant_message']
    expected_id = 'synthetic-model' if role == 'career' else 'synthetic-pipeline'
    preferences = {entry['job_id']: entry['components']['preferences_fit'] for entry in updated['rankings']}
    other_id = next(job['id'] for job in JOBS if job['id'] != expected_id)
    checks = dict(initial_question=initial['assistant_message'].count('?') == 1,
                  reply_triggers_rerank=decision['action'] == 'rerank',
                  preference_recorded=bool(changed['preferences']),
                  skills_unchanged=changed['skills'] == PROFILE['skills'],
                  selected_preference_favored=preferences[expected_id] > preferences[other_id],
                  updated_question=updated['assistant_message'].count('?') == 1,
                  edge_case=edge_ok)
    return dict(role=role, initial=initial, question=QUESTIONS[role], reply=REPLIES[role],
                decision=decision, updated_profile=changed, updated=updated,
                edge_message=edge_message, edge=edge, checks=checks)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--live', action='store_true', help='Authorize eight model calls; uses configured API key.')
    args = parser.parse_args()
    if not args.live:
        parser.error('--live is required; this script makes paid API calls')
    load_dotenv(ROOT / '.env')
    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(run_role, ('career', 'expert')))
    payload = dict(timestamp=datetime.now(timezone.utc).isoformat(), advisory_version=ADVISORY_VERSION,
                   model=MODEL, reasoning=REASONING_EFFORT, calls=8,
                   limitation='Synthetic developmental smoke test, not evidence of ranking quality or reliability.',
                   profile=PROFILE, jobs=JOBS, results=results)
    Path(__file__).with_name('smoke-results.json').write_text(json.dumps(payload, ensure_ascii=False, indent=2)+'\n')
    for result in results:
        print(result['role'], result['checks'], flush=True)
    sys.exit(0 if all(all(r['checks'].values()) for r in results) else 1)
