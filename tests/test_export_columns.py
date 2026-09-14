"""Readable names preserve values, archived versions, codes and missingness."""
import csv
import io
import json
import re
import zipfile

import pytest

from export_columns import export_headers, export_name
from survey_store import SurveyRequest, SurveyDraftRequest, VERSIONED_FIELDS
from study_usage import empty_usage
from test_admin import admin_app, login
from test_survey_v7 import versioned_payload, seed_record


def read_csv(raw):
    return list(csv.DictReader(io.StringIO(raw.decode('utf-8-sig')), delimiter=';'))


def test_default_names_are_unique_ascii_and_preserve_all_values(admin_app):
    seed_record(admin_app, 'diana-v6', 'C', 'a')
    seed_record(admin_app, 'diana-v7', 'B', 'b')
    client=admin_app.test_client();login(client)
    readable=read_csv(client.get('/api/admin/export').data)
    technical=read_csv(client.get('/api/admin/export?columns=technical').data)
    assert len(readable)==len(technical)==2
    for new, old in zip(readable, technical):
        assert len(new)==len(old)
        assert all(re.fullmatch('[a-z][a-z0-9_]*', key) for key in new)
        assert new=={export_name(key):value for key,value in old.items()}
        assert 'v6_system_nutzen' in new and 'v7_system_nutzen' in new
        assert new['ki_letzte_verwendung']=='unknown'
        assert new['ki_jemals_selbst_gestaltet']==''
        assert new['ki_auswahlwechsel_anzahl']==''
    assert readable[0]['v7_chat_hilfe_suchwuensche']=='8'
    assert 'v7_ki_selbst_angepasst_selbstauskunft' in readable[0]
    assert client.get('/api/admin/export?columns=unknown').status_code==400


def test_zip_codebook_mapping_covers_every_header_and_exact_question(admin_app):
    client=admin_app.test_client();login(client)
    archive=zipfile.ZipFile(io.BytesIO(client.get('/api/admin/export?format=zip').data))
    headers=next(csv.reader(io.StringIO(archive.read('diana_numiqo.csv').decode('utf-8-sig')), delimiter=';'))
    book=json.loads(archive.read('codebook.json'))
    mapping=read_csv(archive.read('spaltenzuordnung.csv'))
    assert headers==[item['variable'] for item in book]==[item['export_spalte'] for item in mapping]
    assert len(headers)==len(set(headers))
    assert json.loads(archive.read('study_manifest.json'))['column_names']=='readable'
    by_name={item['variable']:item for item in book}
    for version, fields in VERSIONED_FIELDS.items():
        for field in fields:
            technical=version[6:]+'_'+field['name']
            item=by_name[export_name(technical)]
            assert item['question']==field['title']
            assert item['technical_variable']==technical
            assert item['versions']==[version]
            if field['kind']=='scale':
                assert item['minimum']==1 and item['maximum']==10
                assert item['endpoints']==field['scale']
            status=by_name[export_name(technical+'_status')]
            assert status['codes']['unanswered']=='Noch nicht beantwortet'
    assert by_name['v7_suche_aufwand']['reverse_direction'] is True
    assert by_name['v7_system_nutzen']['reverse_direction'] is False
    assert by_name['v7_score_nutzen']['visible_if_export']=={'field':'v7_studiengruppe_originalcode','equals':'B'}
    assert by_name['v7_suchwuensche_im_chat_geaendert']['codes']=={'1':'Ja','0':'Nein'}
    assert by_name['ki_jemals_selbst_gestaltet']['codes']['0'].startswith('Im erfassten Zeitraum')


def test_readable_defaults_keep_numeric_zero_and_missing_status_distinct(admin_app):
    store=admin_app.extensions['survey_store']
    payload=versioned_payload(arm='B')
    payload.update(search_refinement='no',score_usefulness='not_used',feedback='=1+1')
    store.save(SurveyRequest.model_validate(payload).root)
    store.save_draft(SurveyDraftRequest.model_validate(dict(version='diana-v7',submission_id='b'*32,
        revision=1,answers={'study_arm':'A','search_goal':'Python'})).root)
    client=admin_app.test_client();login(client)
    rows=read_csv(client.get('/api/admin/export').data)
    complete=next(row for row in rows if row['teilnahme_status']=='completed')
    draft=next(row for row in rows if row['teilnahme_status']=='in_progress')
    assert complete['v7_suchwuensche_im_chat_geaendert']=='0'
    assert complete['v7_score_nutzen']==''
    assert complete['v7_score_nutzen_antwortstatus']=='not_used'
    assert complete['v7_verbesserungsvorschlaege_freitext']=="'=1+1"
    assert draft['v7_score_nutzen_antwortstatus']=='skipped'
    assert draft['v7_system_nutzen_antwortstatus']=='unanswered'
    assert draft['abgeschlossen_am_utc']==''


def test_usage_columns_export_numeric_flags_and_do_not_expose_persona_content(admin_app):
    store=admin_app.extensions['survey_store']
    store.save(SurveyRequest.model_validate(versioned_payload(arm='B')).root)
    row=admin_app.extensions['admin_data'].records()[0]
    row['personality_usage']=dict(empty_usage(),capture_version=1,initial_source='template',initial_template_id='career',
        last_source='custom',ever_template=True,ever_custom=True,selection_change_count=1)
    csv_row=read_csv(admin_app.extensions['admin_data'].csv_data([row]))[0]
    assert csv_row['ki_erste_vorlage']=='career'
    assert csv_row['ki_letzte_verwendung']=='custom'
    assert csv_row['ki_jemals_selbst_gestaltet']=='1'
    assert csv_row['ki_jemals_vorlage']=='1'
    assert csv_row['ki_auswahlwechsel_anzahl']=='1'
    assert not any('name' in key or 'freitext' in key for key in csv_row if key.startswith('ki_'))


def test_headers_reject_unknown_mapping_or_duplicate():
    with pytest.raises(KeyError):export_name('v7_unknown_question')
    with pytest.raises(ValueError):export_headers(['v7_score_usefulness']*2)
    with pytest.raises(ValueError):export_headers([], columns='unknown')
