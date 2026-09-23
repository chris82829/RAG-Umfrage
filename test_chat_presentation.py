import hashlib
import sqlite3
import json
from contextlib import contextmanager
from types import SimpleNamespace

import pytest

from app import welcome_message
from system_prompt_store import SystemPromptStore, CHAT_GUIDANCE, CHAT_GUIDANCE_VERSION, LEGACY_CHAT_GUIDANCE
from chat_text import clean_job_references, compact_advice, remove_gender_suffixes, MAX_BC_WELCOME_CHARS, MAX_BC_ANSWER_CHARS
from llm_service import OpenAIService
from test_system_prompts import CapturingResponses, PROFILE, CANDIDATES, neutral_patch


def test_a_opening_is_only_the_actual_model_answer():
    answer='Python passt zur Datenanalyse.'
    result={'jobs':[{'id':str(i)} for i in range(20)],'advisor':{'mode':'preset','preset':'standard'},
            'assistant_message':answer}
    assert welcome_message(result,prompt_policy='unprompted')==answer
    assert welcome_message(result,prompt_policy='career_fixed').startswith(
        'Hallo! 20 Stellen gefunden und bewertet. Du kannst mich alles über diese Stellen fragen.\n\n')


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
    assert result == '- Python-Entwickler\n\n- Data Engineer\n\nWelche Tätigkeit bevorzugst du?'


def test_long_followup_drops_repeated_intro_and_preserves_job_titles():
    first = 'Werkstudent im Bereich Data Management (m|w|d)'
    second = 'Werkstudent/Praktikant Data Engineering mit Python (m/w/d)'
    text = 'Am besten passen deine Kenntnisse zur ersten Stelle.\n'
    text += '- ' + first + ': ' + 'Python und Pandas passen. ' * 12
    text += '\n- ' + second + ': ' + 'SQL passt zu den Datenaufgaben. ' * 12
    text += '\n\nWillst du lieber ETL oder ML?'
    result = compact_advice(text)
    assert len(result) <= MAX_BC_ANSWER_CHARS
    assert result.startswith('- ' + remove_gender_suffixes(first) + ':')
    assert '\n- ' + remove_gender_suffixes(second) + ':' in result
    assert 'Am besten' not in result
    assert result.endswith('\n\nWillst du lieber ETL oder ML?')


@pytest.mark.parametrize('value', ['[Python](job:123)', '[Python]\\(job:123)', '[Python](job:123',
                                  '[Python]\\(job:123', '[Python]('])
def test_public_text_never_contains_reference_syntax(value):
    assert clean_job_references(value) == 'Python'


@pytest.mark.parametrize('suffix', ['(m/w/d)', '(w/m/d)', '(m|w|d)', '(f/m/d)', '(M / W / D)', '(m/w/x)'])
def test_chat_omits_gender_suffixes_but_preserves_technical_details(suffix):
    text = f'- Data Engineer {suffix}: Python (Pandas) passt.\n- Analyst {suffix} (SQL)'
    assert remove_gender_suffixes(text) == '- Data Engineer: Python (Pandas) passt.\n- Analyst (SQL)'


@pytest.mark.parametrize('policy', ['career_fixed', 'custom_career'])
@pytest.mark.parametrize('count', [0, 1, 7, 20])
def test_greeting_uses_actual_count_and_requested_sentence(policy, count):
    jobs = [{'id': str(i), 'title': f'Python-Stelle {i} (m/w/d)'} for i in range(count)]
    result = {'jobs': jobs, 'advisor': {'mode': 'preset', 'preset': 'diana'},
              'assistant_message': 'Python passt. Welche Aufgaben bevorzugst du?'}
    message = welcome_message(result, prompt_policy=policy)
    assert len(message) <= MAX_BC_WELCOME_CHARS
    assert '(m/w/d)' not in message
    if count == 0:
        assert message == 'Aktuell gibt es keine Stellen zur gewählten Stellenart.'
    else:
        found = f'{count} Stellen' if count != 1 else 'Eine Stelle'
        reference = 'diese Stellen' if count != 1 else 'diese Stelle'
        assert message.startswith(f'Hallo! {found} gefunden und bewertet. Du kannst mich alles über {reference} fragen.\n\n')
        assert message.endswith('Welche Aufgaben bevorzugst du?')


@pytest.mark.parametrize('schema_name', ['ChatDecision', 'GenericChatDecision'])
def test_final_chat_text_is_clean_including_a_without_changing_profile_patch(schema_name):
    import llm_service
    patch = neutral_patch()
    result = getattr(llm_service, schema_name).model_validate({
        'action': 'answer', 'profile_patch': patch,
        'assistant_message': 'Data Engineer (m/w/d) passt. Kenntnisse (Python) helfen.',
    })
    assert result.assistant_message == 'Data Engineer passt. Kenntnisse (Python) helfen.'
    assert result.profile_patch.model_dump() == patch


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


def test_compacting_never_clips_explanations_or_adds_ellipsis():
    text = '- Python-Entwickler: Deine Python-Kenntnisse passen zu den Datenaufgaben. Weitere Aufgaben sind möglich.\n- Data Engineer: Hier kannst du deine SQL-Kenntnisse einsetzen.\n\nWelche Aufgabe bevorzugst du?'
    result = compact_advice(text, max_characters=160)
    assert '…' not in result and '...' not in result
    assert 'Deine Python-Kenntnisse passen zu den Datenaufgaben.' in result
    assert 'Weitere Aufgaben' not in result
    assert result.endswith('Welche Aufgabe bevorzugst du?')
    assert len(result) <= 160


def test_long_single_sentence_is_omitted_instead_of_being_cut_mid_word():
    text = '- Data Engineer: ' + 'Zusätzliche ' * 100 + 'Aufgaben.'
    assert compact_advice(text) == '- Data Engineer'
    from chat_completion import conclude_custom_chat, C_SELECTION_CONCLUSION
    assert conclude_custom_chat('Eine ' * 100 + 'Aussage.', [{}]) == C_SELECTION_CONCLUSION


def test_generated_ellipsis_is_removed_without_changing_decimal_numbers():
    assert clean_job_references('Python… SQL... Version 3.12 bleibt.') == 'Python SQL Version 3.12 bleibt.'
