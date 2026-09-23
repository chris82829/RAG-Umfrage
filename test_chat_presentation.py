import hashlib
import sqlite3
import json
from contextlib import contextmanager
from types import SimpleNamespace

import pytest

from app import welcome_message
from system_prompt_store import SystemPromptStore, CHAT_GUIDANCE, CHAT_GUIDANCE_VERSION, LEGACY_CHAT_GUIDANCE
from chat_text import clean_job_references, compact_advice, MAX_BC_WELCOME_CHARS, MAX_BC_ANSWER_CHARS
from llm_service import OpenAIService
from test_system_prompts import CapturingResponses, PROFILE, CANDIDATES, neutral_patch


def test_a_opening_is_only_the_actual_model_answer():
    answer='Python passt zur Datenanalyse.'
    result={'jobs':[{'id':str(i)} for i in range(20)],'advisor':{'mode':'preset','preset':'standard'},
            'assistant_message':answer}
    assert welcome_message(result,prompt_policy='unprompted')==answer
    assert welcome_message(result,prompt_policy='career_fixed').startswith('20 Stellen gefunden.')


def test_guidance_migration_preserves_admin_edits_a_and_frozen_participant_prompts(tmp_path):
    path=tmp_path/'prompts.sqlite3'
    store=SystemPromptStore(path)
    original=store.get()
    prompts={key:item['text'] for key,item in original['prompts'].items()}
    prompts['unprompted']='Mein unabhängiger A-Prompt.'
    for policy in ('career_fixed','custom_career'):
        prompts[policy]=prompts[policy].replace('\n\n'+CHAT_GUIDANCE,'')+'\nEine individuelle Administratoreinstellung.'
    store.update(original['revision'],prompts)
    frozen=store.participant_snapshot('a'*64,'example-study','career_fixed')
    with sqlite3.connect(path) as db:
        db.execute('DELETE FROM system_prompt_migrations WHERE name=?',(CHAT_GUIDANCE_VERSION,))
    before=store.get()
    migrated=SystemPromptStore(path).get()
    assert migrated['prompts']['unprompted']==before['prompts']['unprompted']
    for policy in ('career_fixed','custom_career'):
        item=migrated['prompts'][policy]
        assert item['text']==prompts[policy]+'\n\n'+CHAT_GUIDANCE
        assert item['revision']==before['prompts'][policy]['revision']+1
        assert item['sha256']==hashlib.sha256(item['text'].encode()).hexdigest()
    assert store.participant_snapshot('a'*64,'example-study','career_fixed')==frozen
    assert SystemPromptStore(path).get()==migrated
    # Guidance remains editable; it is not injected again on every restart.
    edited={key:item['text'] for key,item in migrated['prompts'].items()}
    edited['career_fixed']=prompts['career_fixed']
    store.update(migrated['revision'],edited)
    assert SystemPromptStore(path).snapshot('career_fixed')['text']==edited['career_fixed']


@pytest.mark.parametrize('policy', ['career_fixed', 'custom_career'])
def test_welcome_is_two_bullets_short_question_and_bounded(policy):
    question = 'Ist dir München wichtiger als Nürnberg?'
    answer = '- [Python-Stelle]\\(job:123): ' + 'Passende Aufgaben mit Python. ' * 15
    answer += '\n- [Datenanalyse](job:456): ' + 'SQL und Pandas passen. ' * 15
    answer += '\n\n' + question
    jobs = [{'id': '123', 'title': 'Python-Stelle'}, {'id': '456', 'title': 'Datenanalyse'}]
    result = {'jobs': jobs, 'advisor': {'mode': 'preset', 'preset': 'diana'}, 'assistant_message': answer}
    message = welcome_message(result, prompt_policy=policy)
    assert len(message) <= MAX_BC_WELCOME_CHARS == 420
    assert len([line for line in message.splitlines() if line.startswith('- ')]) == 2
    assert message.endswith('\n\n' + question)
    assert 'job:' not in message and '123' not in message and '[' not in message
    assert 'Weitere Stellen anzeigen' not in message


def test_non_list_intro_uses_actual_job_titles_without_fabricated_advice():
    text = 'Am besten passen diese Stellen. Welche Tätigkeit bevorzugst du?'
    result = compact_advice(text, intro_jobs=[{'title': 'Python-Entwickler'}, {'title': 'Data Engineer'}])
    assert result == '- Python-Entwickler\n- Data Engineer\n\nWelche Tätigkeit bevorzugst du?'


@pytest.mark.parametrize('value', ['[Python](job:123)', '[Python]\\(job:123)', '[Python](job:123',
                                  '[Python]\\(job:123', '[Python]('])
def test_public_text_never_contains_reference_syntax(value):
    assert clean_job_references(value) == 'Python'


def test_new_guidance_replaces_legacy_block_and_preserves_snapshot(tmp_path):
    path = tmp_path/'prompts.sqlite3'
    store = SystemPromptStore(path)
    record = store.get()
    texts = {policy: entry['text'] for policy, entry in record['prompts'].items()}
    for policy in ('career_fixed', 'custom_career'):
        texts[policy] = texts[policy].replace(CHAT_GUIDANCE, LEGACY_CHAT_GUIDANCE) + '\nMeine eigene Regel.'
    store.update(record['revision'], texts)
    frozen = store.participant_snapshot('b'*64, 'example', 'career_fixed')
    with sqlite3.connect(path) as db:
        db.execute('DELETE FROM system_prompt_migrations WHERE name=?', (CHAT_GUIDANCE_VERSION,))
    migrated = SystemPromptStore(path)
    for policy in ('career_fixed', 'custom_career'):
        text = migrated.snapshot(policy)['text']
        assert LEGACY_CHAT_GUIDANCE not in text
        assert text.count(CHAT_GUIDANCE) == 1
        assert 'Meine eigene Regel.' in text
    assert migrated.participant_snapshot('b'*64, 'example', 'career_fixed') == frozen


@pytest.mark.parametrize('policy', ['career_fixed', 'custom_career'])
def test_frozen_legacy_prompt_uses_current_intro_format_without_changing_scoring(policy):
    responses = CapturingResponses()
    service = OpenAIService('', client=SimpleNamespace(responses=responses))
    old_prompt = 'Du berätst anhand der übergebenen Stellen.\n' + LEGACY_CHAT_GUIDANCE
    result = service.rerank({}, PROFILE, CANDIDATES, prompt_policy=policy, system_prompt=old_prompt,
                            chat_context={'initial_intro': True})
    assert responses.calls[0]['input'][0]['content'].startswith(old_prompt)
    assert 'VERBINDLICHES KURZFORMAT' not in responses.calls[0]['input'][0]['content']
    assert 'VERBINDLICHES KURZFORMAT' in responses.calls[1]['input'][0]['content']
    assert result['assistant_message'].startswith('- Data Werkstudent')
    assert len(result['assistant_message']) <= MAX_BC_ANSWER_CHARS


def test_streamed_bc_chat_is_bounded_before_any_preview_is_sent():
    long = '- [Python](job:123): ' + 'Belegte Python-Aufgaben. ' * 40 + '\n\nWelche Aufgabe bevorzugst du?'
    data = {'action': 'answer', 'profile_patch': neutral_patch(), 'assistant_message': long}
    class Responses:
        @contextmanager
        def stream(self, **options):
            class Events:
                def __iter__(self):
                    yield SimpleNamespace(type='response.output_text.delta', snapshot=json.dumps(data))
                def get_final_response(self):
                    return SimpleNamespace(status='completed', usage=None, output_parsed=data)
            yield Events()
    service = OpenAIService('', client=SimpleNamespace(responses=Responses()))
    steps = service.plan_chat_steps(PROFILE, [], 'Welche Stelle?', jobs=[], stream=True,
                                    prompt_policy='career_fixed', system_prompt=LEGACY_CHAT_GUIDANCE)
    preview = next(steps)['data']['assistant_message']
    with pytest.raises(StopIteration) as completed:
        next(steps)
    assert preview == completed.value.value['assistant_message']
    assert len(preview) <= MAX_BC_ANSWER_CHARS
    assert 'job:' not in preview and '123' not in preview
