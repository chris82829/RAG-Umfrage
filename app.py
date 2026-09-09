"""Flask API for the hybrid matching prototype. Run: python app.py"""
from __future__ import annotations

import hashlib
import json
import logging
import os
import time
from contextlib import contextmanager
from pathlib import Path

import click
from dotenv import load_dotenv
from flask import Flask, Response, jsonify, request, send_from_directory, stream_with_context
from flask_cors import CORS
from pydantic import ValidationError
from werkzeug.exceptions import HTTPException

from data_store import JobStore
from llm_service import LLMUnavailable, OpenAIService, PersonaResult
from retrieval import EmbeddingUnavailable, HybridRetriever
from schemas import ChatInput, Profile, SearchInput
from session_store import SessionConflict, SessionStore
from index_state import read_progress, write_progress
from advisor import AdvisorConfig, resolve_advisor

BASE_DIR = Path(__file__).resolve().parent
MATCHING_POLICY_VERSION = 'employment-only-v1'
# Bump when persona instructions or its output contract change incompatibly.
PERSONA_CACHE_VERSION = 'search-persona-v1'


def persona_fingerprint(profile):
    """Fingerprint all applicant inputs; only the owning session stores this value."""
    canonical = json.dumps(Profile.model_validate(profile).model_dump(mode='json'),
                           sort_keys=True, ensure_ascii=False, separators=(',', ':'), allow_nan=False)
    return f'{PERSONA_CACHE_VERSION}:{hashlib.sha256(canonical.encode()).hexdigest()}'


def reusable_persona(persona, saved_fingerprint, current_fingerprint):
    if saved_fingerprint != current_fingerprint:
        return False
    try:
        PersonaResult.model_validate(persona)
    except ValidationError:
        return False
    return True


def project_path(value):
    path = Path(value).expanduser()
    return path if path.is_absolute() else BASE_DIR / path


def merge_profile(profile, patch):
    """None preserves a value; [] clears a list; max-hours has an explicit clear flag."""
    merged = {**profile, 'filters': dict(profile['filters'])}
    for key in ('query', 'skills', 'preferences'):
        if patch.get(key) is not None:
            merged[key] = patch[key]
    filters = patch.get('filters') or {}
    for key in ('employment_types', 'locations', 'remote'):
        if filters.get(key) is not None:
            merged['filters'][key] = filters[key]
    if filters.get('clear_max_hours'):
        merged['filters']['max_hours'] = None
    elif filters.get('max_hours') is not None:
        merged['filters']['max_hours'] = filters['max_hours']
    return Profile.model_validate(merged).model_dump()


def describe_filters(filters):
    labels = {'werkstudent': 'Werkstudent', 'praktikum': 'Praktikum', 'vollzeit': 'Vollzeit',
              'teilzeit': 'Teilzeit', 'ausbildung': 'Ausbildung', 'trainee': 'Trainee',
              'abschlussarbeit': 'Abschlussarbeit', 'sonstige': 'Sonstige'}
    types = filters.get('employment_types') or []
    return f"Stellenarten: {', '.join(labels.get(x, x) for x in types)}" if types else 'alle Stellenarten'


def profile_changes(before, after):
    """Ignore list order/casing; only changed retrieval inputs need another search."""
    def comparable(value):
        if isinstance(value, str):
            return ' '.join(value.casefold().split())
        if isinstance(value, list):
            return sorted({comparable(item) for item in value})
        if isinstance(value, dict):
            return {key: comparable(item) for key, item in value.items()}
        return value
    core = any(comparable(before.get(key)) != comparable(after.get(key))
               for key in ('query', 'skills'))
    before_filters, after_filters = before.get('filters') or {}, after.get('filters') or {}
    core = core or comparable(before_filters.get('employment_types', [])) != comparable(after_filters.get('employment_types', []))
    soft = any(comparable(before.get(key)) != comparable(after.get(key))
               for key in ('preferences', 'cv_text'))
    soft = soft or any(comparable(before_filters.get(key)) != comparable(after_filters.get(key))
                       for key in ('locations', 'remote', 'max_hours'))
    return core, soft


def restricted_legacy_pool(state):
    """Older sessions may have discarded jobs using now-soft preferences."""
    filters = (state.get('profile') or {}).get('filters') or {}
    return (state.get('_matching_policy_version') != MATCHING_POLICY_VERSION
            and bool(filters.get('locations') or filters.get('remote')
                     or filters.get('max_hours') is not None))


def public_state(state):
    """Expose evaluated job cards while keeping retrieval pools and caches private."""
    return {**{key: value for key, value in state.items() if not key.startswith('_')},
            'candidate_pool': {'available': '_candidates' in state,
                               'count': len(state.get('_candidates', [])),
                               'refresh_required': restricted_legacy_pool(state)}}


def create_app(config=None, *, retriever=None, llm=None):
    # Explicit path: never load an unrelated parent-directory .env.
    load_dotenv(BASE_DIR / '.env', override=False)
    app = Flask(__name__)
    app.config.from_mapping(
        DATABASE_PATH=os.getenv('DATABASE_PATH', 'instance/jobs.sqlite3'),
        SEED_DUMMY_DATA=os.getenv('SEED_DUMMY_DATA', 'true').lower() == 'true',
        REQUIRE_COMPLETE_INDEX=os.getenv('REQUIRE_COMPLETE_INDEX', 'false').lower() == 'true',
        EMBEDDING_CACHE_DIR=os.getenv('EMBEDDING_CACHE_DIR', '.cache/embeddings'),
        E5_DEVICE=os.getenv('E5_DEVICE', 'cpu'),
        E5_BATCH_SIZE=int(os.getenv('E5_BATCH_SIZE', '8')),
        OPENAI_API_KEY=os.getenv('OPENAI_API_KEY', ''),
        CORS_ORIGINS=os.getenv('CORS_ORIGINS', 'http://localhost:5173,http://127.0.0.1:5173'),
        MAX_CONTENT_LENGTH=128 * 1024,
        JSON_SORT_KEYS=False,
    )
    if config:
        app.config.update(config)
    app.json.ensure_ascii = False
    origins = app.config['CORS_ORIGINS']
    if isinstance(origins, str):
        origins = [x.strip() for x in origins.split(',') if x.strip()]
    CORS(app, resources={r'/api/*': {'origins': origins}})

    db_path = project_path(app.config['DATABASE_PATH'])
    db_path.parent.mkdir(parents=True, exist_ok=True)
    store = JobStore(db_path)
    store.initialize()
    if app.config['SEED_DUMMY_DATA']:
        store.seed_if_empty(BASE_DIR / 'dummy_jobs.json')
    sessions = SessionStore(db_path)
    engine = retriever or HybridRetriever(
        cache_dir=project_path(app.config['EMBEDDING_CACHE_DIR']),
        device=app.config['E5_DEVICE'], batch_size=app.config['E5_BATCH_SIZE'])
    performance_logger = app.logger.getChild('performance')
    performance_logger.setLevel(logging.INFO)
    language_model = llm or OpenAIService(api_key=app.config['OPENAI_API_KEY'],
                                        performance_logger=performance_logger)
    app.extensions.update(job_store=store, chat_store=sessions, retriever=engine,
                          llm_service=language_model)

    @contextmanager
    def timed_phase(phase, **metadata):
        started, status = time.monotonic(), 'ok'
        try:
            yield
        except Exception:
            status = 'error'
            raise
        finally:
            performance_logger.info(json.dumps({
                'event': 'matching_phase', 'phase': phase,
                'elapsed_ms': round((time.monotonic() - started) * 1000, 2),
                'status': status, **metadata}, separators=(',', ':')))

    @app.get('/')
    @app.get('/index.html')
    @app.get('/suche')
    @app.get('/mehr-erfahren')
    def website():
        return send_from_directory(BASE_DIR / 'web-dist', 'index.html', max_age=0)

    @app.get('/assets/<path:filename>')
    def website_asset(filename):
        return send_from_directory(BASE_DIR / 'web-dist' / 'assets', filename)

    @app.get('/api/jobs')
    def browse_jobs():
        # Initial browsing is unranked and never calls either model.
        jobs = store.filter_jobs({})
        return jsonify(jobs=[{k: v for k, v in job.items() if k not in ('search_text', 'raw')}
                             for job in jobs[:20]], total=len(jobs), ranked=False)

    @app.get('/api/index-status')
    def index_status():
        return jsonify(read_progress(db_path, store.count(), app.config['REQUIRE_COMPLETE_INDEX']))

    def wants_ndjson():
        # An ordinary browser's */* is not an opt-in to streaming. Limit this
        # protocol to the two mutation endpoints that the frontend negotiates.
        return request.endpoint in {'onboard', 'chat'} and any(
            media_type == 'application/x-ndjson' and quality > 0
            for media_type, quality in request.accept_mimetypes
        )

    def ndjson_line(event):
        return app.json.dumps(event, separators=(',', ':'), allow_nan=False) + '\n'

    def error_response(error, status):
        if wants_ndjson():
            return Response(ndjson_line({'type': 'error', 'error': error, 'status': status}),
                            status=status, mimetype='application/x-ndjson',
                            headers={'Cache-Control': 'no-store', 'X-Accel-Buffering': 'no'})
        return jsonify(error=error), status

    def complete_operation(operation):
        """Run the same generator synchronously for existing JSON clients."""
        try:
            while True:
                next(operation)
        except StopIteration as completed:
            return completed.value
        finally:
            operation.close()

    def operation_response(operation, status=200):
        if not wants_ndjson():
            return jsonify(complete_operation(operation)), status

        @stream_with_context
        def events():
            try:
                while True:
                    try:
                        event = next(operation)
                    except StopIteration as completed:
                        yield ndjson_line({'type': 'result', 'data': completed.value})
                        return
                    yield ndjson_line(event)
            except Exception as error:
                # Headers may already be sent. Reuse the existing safe error
                # handlers, including validation fields and optimistic-lock 409,
                # then deliver their status in the final protocol event.
                response = app.make_response(app.handle_user_exception(error))
                yield response.get_data(as_text=True)
            finally:
                operation.close()

        return Response(events(), mimetype='application/x-ndjson',
                        headers={'Cache-Control': 'no-store', 'X-Accel-Buffering': 'no'})

    def parse_body(schema):
        if not request.is_json:
            return None, error_response({'code': 'invalid_content_type',
                                         'message': 'Content-Type application/json erforderlich.'}, 415)
        body = request.get_json()
        return schema.model_validate(body), None

    def rank_candidates(profile, persona, candidates, filtered_count, advisor,
                        chat_message=None, chat_context=None, assessment_cache=None):
        with timed_phase('rerank'):
            reranked = language_model.rerank(persona or {}, profile, candidates,
                                             advisor=advisor, chat_message=chat_message,
                                             chat_context=chat_context,
                                             assessment_cache=assessment_cache)
        lookup = {item['job']['id']: item for item in candidates}
        cards = []
        for result in reranked['rankings']:
            candidate = lookup[result['job_id']]
            job = {key: value for key, value in candidate['job'].items()
                   if key not in ('search_text', 'raw')}
            cards.append({**job, 'match': result,
                          'retrieval': {k: v for k, v in candidate.items() if k != 'job'}})
        # Retain the complete retrieval pool independently of evaluated cards.
        # Raw exports and embedding inputs are not needed by later reranking calls.
        pool = [{**item, 'job': {key: value for key, value in item['job'].items()
                                if key not in ('search_text', 'raw')}} for item in candidates]
        result = {'profile': profile, 'persona': persona, 'advisor': advisor, 'jobs': cards,
                  '_matching_policy_version': MATCHING_POLICY_VERSION,
                  '_candidates': pool, 'assistant_message': reranked['assistant_message'],
                  'retrieval': {'filtered_count': filtered_count, 'candidate_count': len(pool)}}
        if isinstance(reranked.get('assessment_cache'), dict):
            result['_assessment_cache'] = reranked['assessment_cache']
        return result

    def match_steps(profile, persona=None, chat_message=None, chat_context=None, advisor=None,
                    saved_persona_fingerprint=None):
        advisor = AdvisorConfig.model_validate(advisor or {}).model_dump()
        # Only employment type excludes jobs. The legacy filters container also
        # holds soft location, work-model and hours wishes for the LLM.
        with timed_phase('prefilter'):
            jobs = store.filter_jobs({'employment_types': profile['filters']['employment_types']})
        if not jobs:
            return {'profile': profile, 'persona': persona, 'advisor': advisor, 'jobs': [],
                    'assistant_message': 'Für die gewählten Stellenarten sind keine Anzeigen vorhanden. '
                    f"{describe_filters(profile['filters'])}. "
                    'Du kannst die Stellenart im Suchprofil oder im Chat ändern.',
                    'retrieval': {'filtered_count': 0, 'candidate_count': 0},
                    '_candidates': [], '_matching_policy_version': MATCHING_POLICY_VERSION,
                    **({'_persona_fingerprint': saved_persona_fingerprint}
                       if saved_persona_fingerprint is not None else {}),
                    'chat_action': 'search'}
        progress = read_progress(db_path, store.count(), app.config['REQUIRE_COMPLETE_INDEX'])
        if progress['status'] != 'ready':
            raise LLMUnavailable(f"Der Suchindex wird vorbereitet: {progress['completed']} von {progress['total']} Stellen. Bitte kurz warten.")
        # This event is reached only after the server committed to a real full
        # search, not while chat intent is still unknown or a cached pool reranks.
        yield {'type': 'phase', 'phase': 'search'}
        current_fingerprint = persona_fingerprint(profile)
        cache_hit = reusable_persona(persona, saved_persona_fingerprint, current_fingerprint)
        with timed_phase('persona', cache_hit=cache_hit):
            if not cache_hit:
                persona = language_model.generate_persona(profile)
        # Include literal skills to preserve BM25 keywords even if the persona paraphrases them.
        # Skills and the distilled query must precede verbose free text for E5's
        # 512-token limit. BM25 still receives the complete text.
        query = '\n'.join(x for x in [' '.join(profile['skills']),
                                      persona['retrieval_query'], profile['query']] if x)
        with timed_phase('retrieval'):
            candidates = engine.search(jobs, query, top_k=20)
        return {**rank_candidates(profile, persona, candidates, len(jobs), advisor,
                                   chat_message, {**(chat_context or {}), 'scope': 'new_search'}),
                '_persona_fingerprint': current_fingerprint,
                'chat_action': 'search'}

    def match(profile, **kwargs):
        return complete_operation(match_steps(profile, **kwargs))

    @app.get('/api/health')
    def health():
        return jsonify(status='ok', jobs=store.count(), openai_model='gpt-5.4',
                       embedding_model='intfloat/multilingual-e5-large-instruct',
                       openai_configured=bool(app.config['OPENAI_API_KEY']),
                       readiness='Modelle werden erst bei Suche oder warmup geladen.')

    @app.post('/api/search')
    def search():
        body, error = parse_body(SearchInput)
        if error:
            return error
        return jsonify(public_state(match(body.profile.model_dump(), advisor=body.advisor.model_dump())))

    @app.post('/api/onboard')
    def onboard():
        body, error = parse_body(SearchInput)
        if error:
            return error
        def operation():
            result = yield from match_steps(body.profile.model_dump(), advisor=body.advisor.model_dump())
            state = {**result, 'messages': [{'role': 'assistant', 'content': result['assistant_message'],
                                            'advisor_name': resolve_advisor(result['advisor'])['name']}]}
            session_id = sessions.create(state)
            return {'session_id': session_id, **public_state(state)}

        return operation_response(operation(), status=201)

    @app.get('/api/sessions/<session_id>')
    def get_session(session_id):
        saved = sessions.get(session_id)
        if not saved:
            return jsonify(error={'code': 'not_found', 'message': 'Chat nicht gefunden.'}), 404
        return jsonify(session_id=session_id, **public_state({**saved[0],
                       'advisor': saved[0].get('advisor', AdvisorConfig().model_dump())}))

    @app.delete('/api/sessions/<session_id>')
    def delete_session(session_id):
        if not sessions.delete(session_id):
            return jsonify(error={'code': 'not_found', 'message': 'Chat nicht gefunden.'}), 404
        return '', 204

    @app.post('/api/chat')
    def chat():
        body, error = parse_body(ChatInput)
        if error:
            return error
        saved = sessions.get(body.session_id)
        if not saved:
            return error_response({'code': 'not_found', 'message': 'Chat nicht gefunden.'}, 404)
        state, version = saved
        previous_advisor = AdvisorConfig.model_validate(state.get('advisor', {})).model_dump()
        advisor = body.advisor.model_dump() if body.advisor is not None else previous_advisor
        profile = body.profile.model_dump() if body.profile is not None else state['profile']
        context = {'messages': state['messages'][-12:], 'jobs': state['jobs'][:20]}
        action = 'answer'
        answer = 'Dein Suchprofil ist unverändert. Die bisherigen Empfehlungen bleiben erhalten.'
        if body.message:
            with timed_phase('chat_plan'):
                decision = language_model.plan_chat(profile, context['messages'], body.message,
                                                    jobs=context['jobs'], advisor=advisor,
                                                    mode=body.mode,
                                                    candidate_count=len(state.get('_candidates', [])))
            try:
                profile = merge_profile(profile, decision['profile_patch'])
            except ValidationError:
                raise LLMUnavailable('Die KI hat eine ungültige Profiländerung vorgeschlagen.') from None
            action, answer = decision['action'], decision['assistant_message']
        core_changed, preferences_changed = profile_changes(state['profile'], profile)
        advisor_changed = advisor != previous_advisor
        planned_action = action
        # The server, not the model, decides whether changed hard criteria may be
        # applied to cached jobs. A new search is mandatory for retrieval changes.
        if body.mode == 'search' or core_changed:
            action = 'search'
        elif body.mode == 'rerank':
            action = 'rerank'
        elif action != 'search' and (preferences_changed or advisor_changed):
            action = 'rerank'

        refresh_required = restricted_legacy_pool(state)
        if action == 'rerank' and refresh_required and body.mode != 'rerank':
            # Once, on an actual matching request, rebuild pools that were
            # previously narrowed by location, work model or hours. Plain
            # questions still leave stored results and scores untouched.
            action = 'search'

        if body.mode == 'rerank' and refresh_required:
            action = 'answer'
            answer = ('Deine bisherige Auswahl wurde noch nach Ort, Arbeitsmodell oder Stunden '
                      'vorab eingeschränkt. Starte einmal „Neue Suche“, damit auch andere '
                      'Stellen berücksichtigt werden. Danach kannst du wieder nur neu bewerten.')
            profile, advisor = state['profile'], previous_advisor
        elif body.mode == 'rerank' and (core_changed or planned_action == 'search'):
            action = 'answer'
            answer = ('Dafür ist eine neue Suche nötig, weil sich die Suchkriterien ändern '
                      'oder weitere Stellen benötigt werden. Wähle „Neue Suche“ oder „Automatisch“. '
                      'Dein bisheriges Profil und die Ergebnisse bleiben erhalten.')
            profile, advisor = state['profile'], previous_advisor
        elif action == 'rerank' and '_candidates' not in state:
            action = 'answer'
            answer = ('Für diesen älteren Chat wurden nur die angezeigten Empfehlungen gespeichert. '
                      'Wähle einmal „Neue Suche“, um die vollständige Auswahl für späteres '
                      'Nachsortieren zu speichern. Dein Profil und die Ergebnisse bleiben erhalten.')
            profile, advisor = state['profile'], previous_advisor
        elif action == 'rerank' and not state['_candidates']:
            action = 'answer'
            answer = ('Deine bisherige Suche hat keine passenden Stellen gefunden. '
                      'Zum Nachsortieren sind deshalb keine Jobs vorhanden. '
                      'Ändere dein Suchprofil oder starte eine neue Suche.')
            profile, advisor = state['profile'], previous_advisor

        def operation():
            if action == 'search':
                result = yield from match_steps(
                    profile, chat_message=body.message or 'Erkläre kurz die neue Auswahl.',
                    chat_context=context, advisor=advisor, persona=state.get('persona'),
                    saved_persona_fingerprint=state.get('_persona_fingerprint'))
            elif action == 'rerank':
                result = rank_candidates(profile, state.get('persona'), state['_candidates'],
                                         state['retrieval']['filtered_count'], advisor,
                                         body.message or 'Bewerte die vorhandene Auswahl neu und erkläre sie kurz.',
                                         {**context, 'scope': 'existing_candidates'},
                                         assessment_cache=state.get('_assessment_cache'))
                # The retained persona was generated for its original profile.
                # Never label it with the profile just used for soft reranking.
                if '_persona_fingerprint' in state:
                    result['_persona_fingerprint'] = state['_persona_fingerprint']
            else:
                # Questions preserve jobs, scores, pool and search persona exactly.
                result = {**state, 'profile': profile, 'advisor': advisor, 'assistant_message': answer}
            result['chat_action'] = action
            messages = state['messages'] + ([{'role': 'user', 'content': body.message}] if body.message else [])
            messages.append({'role': 'assistant', 'content': result['assistant_message'],
                             'advisor_name': resolve_advisor(result['advisor'])['name']})
            new_state = {**result, 'messages': messages[-100:]}
            sessions.update(body.session_id, new_state, version)
            return {'session_id': body.session_id, **public_state(new_state)}

        return operation_response(operation())

    @app.errorhandler(ValidationError)
    def bad_input(error):
        # Do not echo CV text or the complete request back in validation errors.
        fields = ['.'.join(str(part) for part in item['loc']) or 'profile'
                  for item in error.errors(include_input=False, include_context=False)]
        return error_response({'code': 'validation_error', 'message': 'Eingaben prüfen.',
                               'fields': fields}, 400)

    @app.errorhandler(LLMUnavailable)
    def llm_error(error):
        return error_response({'code': 'llm_unavailable', 'message': str(error)}, 503)

    @app.errorhandler(EmbeddingUnavailable)
    def embedding_error(error):
        return error_response({'code': 'embedding_unavailable',
                               'message': 'E5-Modell nicht verfügbar. Installation, Cache und Netzwerk prüfen.'}, 503)

    @app.errorhandler(SessionConflict)
    def conflict(error):
        return error_response({'code': 'session_conflict', 'message': str(error)}, 409)

    @app.errorhandler(HTTPException)
    def http_error(error):
        return error_response({'code': error.name, 'message': error.description}, error.code)

    @app.errorhandler(Exception)
    def unexpected_error(error):
        # Class only: SDK exception strings may contain submitted personal information.
        app.logger.error('Request failed (%s)', type(error).__name__)
        return error_response({'code': 'internal_error', 'message': 'Interner Verarbeitungsfehler.'}, 500)

    @app.cli.command('import-jobs')
    @click.argument('path', type=click.Path(exists=True, dir_okay=False, path_type=Path))
    @click.option('--allow-control-characters', is_flag=True,
                  help='Nur unescaped JSON-Steuerzeichen tolerieren; Originaldatei bleibt unverändert.')
    def import_jobs(path, allow_control_characters):
        """Import original-schema job JSON, upserting by jobId."""
        try:
            click.echo(store.import_json(path, allow_control_characters=allow_control_characters))
        except (ValueError, OSError) as error:
            raise click.ClickException(str(error)) from None

    @app.cli.command('warmup')
    def warmup():
        """Download E5 and cache embeddings before starting Gunicorn."""
        jobs = store.filter_jobs({})
        started = time.monotonic()
        completed = 0
        write_progress(db_path, 0, len(jobs), 'building', 0)

        def progress(done, total):
            nonlocal completed
            completed = done
            write_progress(db_path, done, total, 'building', time.monotonic() - started)
            click.echo(f'{done}/{total} Stellen vorbereitet.')

        try:
            engine.warmup(jobs, progress=progress)
        except Exception as error:
            write_progress(db_path, completed, len(jobs), 'failed', time.monotonic() - started)
            raise click.ClickException(f'Indexierung fehlgeschlagen ({type(error).__name__}). '
                                       'Gespeicherte Vektoren bleiben erhalten.') from None
        write_progress(db_path, len(jobs), len(jobs), 'ready', time.monotonic() - started)
        click.echo(f'E5 bereit: {len(jobs)} Stellen im Cache.')

    return app


if __name__ == '__main__':
    app = create_app()
    app.run(host='127.0.0.1', port=int(os.getenv('PORT', '5050')), debug=False)
