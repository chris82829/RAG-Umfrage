import json
import sqlite3
from pathlib import Path

import pytest

from privacy import ConsentInput, PrivacyStore, load_notice, token_hash
from study_metrics import StudyOperationMetrics, empty_metrics, metrics_snapshot
from study_release import StudyReleases
from survey_store import SurveyStore
from test_access import test_notice as standalone_notice


@pytest.fixture
def metrics_store(tmp_path):
    path=tmp_path/'metrics.sqlite3';privacy=PrivacyStore(path)
    settings=tmp_path/'privacy.json'
    settings.write_text(json.dumps(dict(approved=True,controller='Test',retention='Test',openai_processing='Test',technical_processing='Test')))
    notice=load_notice(settings);metrics=StudyOperationMetrics(path);surveys=SurveyStore(path)
    releases=StudyReleases(path,Path(__file__).parents[1],[])
    def consent(letter='a',purpose='study'):
        selected=notice if purpose=='study' else standalone_notice(notice,purpose[-1].upper())
        privacy.accept(ConsentInput(token=letter*64,version=selected['version'],accepted=True,purpose=purpose),selected)
        return token_hash(letter*64)
    return path,privacy,metrics,surveys,releases,consent


def test_totals_distinguish_failed_and_successful_operations_without_events(metrics_store):
    path,_,metrics,_,_,consent=metrics_store;digest=consent()
    with sqlite3.connect(path) as db:
        assert metrics.snapshot(digest,db)==empty_metrics()
        metrics.record_operation(digest,'search',True,1000,db)
        metrics.record_operation(digest,'search',False,250,db)
        metrics.record_operation(digest,'chat',True,1500,db)
        metrics.record_operation(digest,'rerank',True,700,db)
        data=metrics.snapshot(digest,db)
        assert data['capture_version']==1
        assert data['successful_search_count']==data['failed_search_count']==1
        assert data['search_duration_ms']==1250 and data['chat_duration_ms']==1500
        assert data['successful_chat_count']==data['successful_rerank_count']==1
        assert data['failed_chat_count']==0
        assert set(data)==set(empty_metrics())
        assert db.execute('SELECT COUNT(*) FROM study_operation_metrics').fetchone()[0]==1


def test_metrics_only_accept_active_study_consent_and_no_test_routes(metrics_store):
    path,privacy,metrics,_,_,consent=metrics_store
    for letter,purpose in [('a','test_a'),('b','test_b'),('c','test_c')]:
        digest=consent(letter,purpose)
        with sqlite3.connect(path) as db:
            assert metrics.record_operation(digest,'chat',True,50,db) is False
    digest=consent('d');privacy.withdraw('d'*64)
    with sqlite3.connect(path) as db:
        assert metrics.record_operation(digest,'search',False,50,db) is False
        assert metrics.record_operation('missing','search',False,50,db) is False
        assert metrics.snapshot(digest,db)==empty_metrics()


@pytest.mark.parametrize('kind,success,duration',[('click',True,1),('chat',1,1),('chat',True,-1),('chat',True,1.5),('chat',True,True)])
def test_invalid_internal_metric_input_is_rejected(metrics_store,kind,success,duration):
    path,_,metrics,_,_,consent=metrics_store;digest=consent()
    with sqlite3.connect(path) as db:
        with pytest.raises(ValueError):metrics.record_operation(digest,kind,success,duration,db)
        assert metrics_snapshot(digest,db)==empty_metrics()


def test_transaction_rollback_does_not_count_uncommitted_result(metrics_store):
    path,_,metrics,_,_,consent=metrics_store;digest=consent()
    with pytest.raises(RuntimeError):
        with sqlite3.connect(path) as db:
            metrics.record_operation(digest,'chat',True,1,db)
            raise RuntimeError('conflicting session write')
    with sqlite3.connect(path) as db:assert metrics_snapshot(digest,db)==empty_metrics()


@pytest.mark.parametrize('operation',['withdraw','delete_consent','end_study'])
def test_metrics_removed_with_participation(metrics_store,operation):
    path,privacy,metrics,_,_,consent=metrics_store;digest=consent()
    with sqlite3.connect(path) as db:metrics.record_operation(digest,'search',True,1,db)
    if operation=='withdraw':privacy.withdraw('a'*64)
    elif operation=='end_study':privacy.end_study()
    else:
        with sqlite3.connect(path) as db:db.execute('DELETE FROM privacy_consents')
    with sqlite3.connect(path) as db:assert metrics_snapshot(digest,db)==empty_metrics()


def test_metric_capture_snapshot_is_frozen_after_completion(metrics_store):
    path,_,metrics,_,releases,consent=metrics_store;digest=consent()
    with sqlite3.connect(path) as db:
        metrics.record_operation(digest,'search',True,100,db)
        releases.capture_response(digest,'test',db)
    with sqlite3.connect(path) as db:
        metrics.record_operation(digest,'chat',True,50,db)
        releases.capture_response(digest,'test',db,completed=True)
        frozen=db.execute('SELECT metadata_json FROM survey_response_metadata').fetchone()[0]
        assert json.loads(frozen)['operation_metrics']['successful_chat_count']==1
    with sqlite3.connect(path) as db:
        metrics.record_operation(digest,'chat',True,100,db)
        releases.capture_response(digest,'test',db,completed=True)
        assert db.execute('SELECT metadata_json FROM survey_response_metadata').fetchone()[0]==frozen
        assert metrics_snapshot(digest,db)['successful_chat_count']==2


def test_parallel_finished_operations_do_not_lose_increments(metrics_store):
    from concurrent.futures import ThreadPoolExecutor
    path,_,metrics,_,_,consent=metrics_store;digest=consent()
    def finish(_):
        with sqlite3.connect(path,timeout=10) as db:
            metrics.record_operation(digest,'chat',True,10,db)
    with ThreadPoolExecutor(max_workers=4) as pool:list(pool.map(finish,range(16)))
    with sqlite3.connect(path) as db:
        result=metrics_snapshot(digest,db)
        assert result['successful_chat_count']==16 and result['chat_duration_ms']==160
