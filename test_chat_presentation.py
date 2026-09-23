import hashlib
import sqlite3

from app import welcome_message
from system_prompt_store import SystemPromptStore, CHAT_GUIDANCE, CHAT_GUIDANCE_VERSION


def test_a_opening_is_only_the_actual_model_answer():
    answer='Python passt zur Datenanalyse.'
    result={'jobs':[{'id':str(i)} for i in range(20)],'advisor':{'mode':'preset','preset':'standard'},
            'assistant_message':answer}
    assert welcome_message(result,prompt_policy='unprompted')==answer
    assert welcome_message(result,prompt_policy='career_fixed').startswith('Hallo! 20 Stellen')


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
