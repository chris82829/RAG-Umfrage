import hashlib
import sqlite3
import json
from contextlib import contextmanager
from types import SimpleNamespace

import pytest

from app import welcome_message
from system_prompt_store import SystemPromptStore, CHAT_GUIDANCE, CHAT_GUIDANCE_VERSION, LEGACY_CHAT_GUIDANCE
from chat_text import clean_job_references, format_chat_answer, remove_gender_suffixes, LEGACY_COMPACT_CHAT_INSTRUCTIONS
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
    assert message.count("Passende Aufgaben mit Python.") == 15
    assert len([line for line in message.splitlines() if line.startswith('- ')]) == 2
    assert message.endswith('\n\n' + question)
    assert 'job:' not in message and '123' not in message and '[' not in message
    assert 'Weitere Stellen anzeigen' not in message


def test_intro_keeps_actual_model_answer_without_substituting_top_job_titles():
    text = 'Am besten passt die dritte Stelle. Welche Tätigkeit bevorzugst du?'
    result = {'jobs': [{'title':'Python-Entwickler'}], 'assistant_message':text}
    assert welcome_message(result,prompt_policy='career_fixed').endswith(text)
    assert 'Python-Entwickler' not in welcome_message(result,prompt_policy='career_fixed')


def test_answer_keeps_intro_all_points_and_missing_skills_in_original_order():
    text = 'Zu deiner Frage: Diese Stelle ist eine Alternative.\n\n- Passung: Python passt zu deinen Datenprojekten.\n- Noch offen: Docker ist in deinem Profil nicht belegt.\n- Arbeitszeit: Die Anzeige nennt 20 Stunden pro Woche.'
    assert format_chat_answer(text) == text


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
    assert result['assistant_message']=='Python passt. Was ist dir wichtiger: Datenpipelines oder Analysen?'


def test_streamed_bc_chat_preserves_full_answer_in_preview_and_final():
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
    assert preview.count("Belegte Python-Aufgaben.") == 40
    assert len(preview) > 380
    assert 'job:' not in preview and '123' not in preview


def test_formatting_never_cuts_abbreviations_or_the_last_sentence():
    text = 'Passung: Python passt.\nNoch offen: Git sowie Container (z. B. Docker) sind nicht belegt. ' + 'Ein vollständiger Satz. ' * 80 + 'DIES IST DAS ENDE.'
    assert format_chat_answer(text) == text
    assert len(format_chat_answer(text)) > 420


def test_long_single_sentence_is_preserved_including_third_turn_conclusion():
    text = '- Data Engineer: ' + 'Zusätzliche ' * 100 + 'Aufgaben.'
    assert format_chat_answer(text) == text
    from chat_completion import conclude_custom_chat, C_SELECTION_CONCLUSION
    assert conclude_custom_chat(text, [{}]) == text + '\n\n' + C_SELECTION_CONCLUSION


def test_generated_ellipsis_is_removed_without_changing_decimal_numbers():
    assert clean_job_references('Python… SQL... Version 3.12 bleibt.') == 'Python SQL Version 3.12 bleibt.'


def test_v2_guidance_migration_removes_old_character_limits_but_keeps_admin_text(tmp_path):
    from system_prompt_store import LEGACY_COMPACT_CHAT_GUIDANCE
    store = SystemPromptStore(tmp_path/'old-prompts.db')
    saved = store.get()
    prompts = {p:entry['text'].replace(CHAT_GUIDANCE, LEGACY_COMPACT_CHAT_GUIDANCE)
               for p,entry in saved['prompts'].items()}
    prompts['career_fixed'] += '\nMeine eigene Regel.'
    store.update(saved['revision'],prompts)
    frozen = store.participant_snapshot('c'*64,'example','career_fixed')
    with sqlite3.connect(store.path) as db:
        db.execute('DELETE FROM system_prompt_migrations WHERE name=?',(CHAT_GUIDANCE_VERSION,))
    migrated = SystemPromptStore(store.path)
    for policy in ('career_fixed','custom_career'):
        text = migrated.snapshot(policy)['text']
        assert LEGACY_COMPACT_CHAT_INSTRUCTIONS not in text
        assert text.count(CHAT_GUIDANCE)==1
        assert '380 Zeichen' not in text
    assert 'Meine eigene Regel.' in migrated.snapshot('career_fixed')['text']
    assert migrated.participant_snapshot('c'*64,'example','career_fixed')==frozen


@pytest.mark.parametrize('schema_name',['ChatDecision','GenericChatDecision'])
def test_chat_schema_has_no_character_cutoff(schema_name):
    import llm_service
    text = 'Python passt zu deinem Profil. ' * 250 + 'Letzter Satz bleibt.'
    schema = getattr(llm_service,schema_name)
    answer = schema.model_validate(dict(action='answer',profile_patch=neutral_patch(),assistant_message=text))
    assert answer.assistant_message == text
    assert 'maxLength' not in schema.model_json_schema()['properties']['assistant_message']


def test_runtime_replaces_obsolete_limits_and_followup_rules_without_mutating_snapshot():
    from chat_text import chat_instructions, LEGACY_DIALOGUE_RULES
    old = next(iter(LEGACY_DIALOGUE_RULES))
    snapshot = old+'\n\n'+LEGACY_COMPACT_CHAT_INSTRUCTIONS+'\nMeine Administratoreinstellung.'
    result = chat_instructions(snapshot)
    assert old not in result
    assert '380 Zeichen' not in result
    assert 'Meine Administratoreinstellung.' in result
    assert result.count('VERBINDLICHES KURZFORMAT') == 1
    assert old in snapshot


def test_all_deployed_v2_variants_are_removed_even_when_new_guidance_is_already_present(tmp_path):
    from chat_text import LEGACY_COMPACT_CHAT_VARIANTS, chat_instructions
    for index, old in enumerate(LEGACY_COMPACT_CHAT_VARIANTS):
        store=SystemPromptStore(tmp_path/f'variant-{index}.db')
        saved=store.get()
        prompts={p:entry['text'] for p,entry in saved['prompts'].items()}
        prompts['career_fixed']=old+'\n\n'+prompts['career_fixed']+'\nMeine Regel.'
        store.update(saved['revision'],prompts)
        with sqlite3.connect(store.path) as db:
            db.execute('DELETE FROM system_prompt_migrations WHERE name=?',(CHAT_GUIDANCE_VERSION,))
        migrated=SystemPromptStore(store.path).snapshot('career_fixed')['text']
        assert '380 Zeichen' not in migrated
        assert migrated.count(CHAT_GUIDANCE)==1
        assert 'Meine Regel.' in migrated
        assert '380 Zeichen' not in chat_instructions(prompts['career_fixed'])
