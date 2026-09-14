"""Password-protected survey administration; opaque cookies plus CSRF protection."""
import hashlib
import secrets
import threading
import time
from functools import wraps

from flask import Blueprint, jsonify, request, make_response
from werkzeug.security import check_password_hash

from pydantic import ValidationError
from admin_store import AdminSurveyData, AdminAnswerCorrection
from survey_store import SURVEY_DEFINITION, SurveyConflict
from survey_analytics import analytics


def register_admin(app, surveys, privacy, releases, sessions, notice):
    bp=Blueprint('survey_admin',__name__,url_prefix='/api/admin')
    data=AdminSurveyData(surveys,privacy,releases,sessions)
    app.extensions['admin_data']=data
    lock=threading.Lock();logins={};attempts={}
    cookie='diana_admin';lifetime=8*60*60
    def error(message,status):return jsonify(error={'message':message}),status
    def active():
        digest=hashlib.sha256(request.cookies.get(cookie,'').encode()).hexdigest()
        with lock:
            now=time.monotonic()
            for key in list(logins):
                if logins[key]['expires']<=now:del logins[key]
            return logins.get(digest)
    def protected(fn):
        @wraps(fn)
        def wrapped(*args,**kwargs):
            session=active()
            if not session:return error('Bitte melde dich an.',401)
            if request.method not in ('GET','HEAD') and not secrets.compare_digest(request.headers.get('X-CSRF-Token',''),session['csrf']):
                return error('Die Sicherheitsbestätigung fehlt. Bitte neu anmelden.',403)
            return fn(*args,**kwargs)
        return wrapped
    @bp.get('/session')
    def status():
        session=active()
        return jsonify(configured=bool(app.config['ADMIN_PASSWORD_HASH']),authenticated=bool(session),csrf=session['csrf'] if session else None)
    @bp.post('/login')
    def login():
        password_hash=app.config['ADMIN_PASSWORD_HASH']
        if not password_hash:return error('Der Verwaltungszugang ist noch nicht eingerichtet.',503)
        body=request.get_json(silent=True)
        if not isinstance(body,dict) or set(body)!={'password'} or not isinstance(body['password'],str) or not 1<=len(body['password'])<=200:
            return error('Bitte das Passwort eingeben.',400)
        key=request.remote_addr or 'unknown';now=time.monotonic()
        with lock:
            for old in list(attempts):
                if attempts[old]['until']<now:del attempts[old]
            rate=attempts.setdefault(key,{'count':0,'until':now+600})
            if rate['count']>=5:return error('Zu viele Versuche. Bitte in zehn Minuten erneut versuchen.',429)
            if len(attempts)>1000:return error('Bitte später erneut versuchen.',429)
            rate['count']+=1
        if not check_password_hash(password_hash,body['password']):return error('Passwort nicht korrekt.',401)
        raw=secrets.token_hex(32);csrf=secrets.token_hex(32)
        with lock:
            attempts.pop(key,None)
            if len(logins)>=100:logins.clear()
            logins[hashlib.sha256(raw.encode()).hexdigest()]={'csrf':csrf,'expires':time.monotonic()+lifetime}
        response=jsonify(authenticated=True,csrf=csrf)
        response.set_cookie(cookie,raw,max_age=lifetime,httponly=True,samesite='Strict',secure=request.is_secure,path='/api/admin')
        return response
    @bp.post('/logout')
    @protected
    def logout():
        with lock:logins.pop(hashlib.sha256(request.cookies.get(cookie,'').encode()).hexdigest(),None)
        response=jsonify(logged_out=True);response.delete_cookie(cookie,path='/api/admin');return response
    @bp.get('/study-status')
    @protected
    def study_status():
        return jsonify(privacy.study_status(notice))

    @bp.put('/study-status')
    @protected
    def update_study_status():
        body = request.get_json(silent=True)
        if not isinstance(body, dict) or set(body) != {'enabled'} or type(body['enabled']) is not bool:
            return error('Bitte einen gültigen Freigabestatus angeben.', 400)
        try:
            return jsonify(privacy.set_study_enabled(body['enabled'], notice))
        except ValueError as failure:
            return error(str(failure), 409)
    def filters():
        query=request.args.get('q','').strip();version=request.args.get('version','')
        if len(query)>100 or version not in ('','diana-v1','diana-v2','diana-v3','diana-v4','diana-v5','diana-v6','diana-v7','diana-v8'):raise ValueError()
        status=request.args.get('status','')
        if status not in ('','completed','in_progress'):raise ValueError()
        arm=request.args.get('arm','')
        if arm not in ('','A','B','C'):raise ValueError()
        return query,version,status,arm
    @bp.get('/responses')
    @protected
    def responses():
        try:
            query,version,status,arm=filters();page=int(request.args.get('page','1'))
            if not 1<=page<=100000:raise ValueError()
        except ValueError:return error('Ungültiger Filter.',400)
        rows=data.filtered(query,version,status,arm);start=(page-1)*25
        return jsonify(total=len(rows),page=page,page_size=25,items=[{k:v for k,v in row.items() if k!='answers'} for row in rows[start:start+25]],
                       definition=SURVEY_DEFINITION,current_release=releases.manifest)
    @bp.get('/responses/<response_id>')
    @protected
    def detail(response_id):
        row=data.detail(response_id)
        return jsonify(row) if row else error('Antwort nicht gefunden.',404)
    @bp.put('/responses/<response_id>')
    @protected
    def correct_response(response_id):
        try:
            correction=AdminAnswerCorrection.model_validate(request.get_json(silent=True))
            data.correct(response_id,correction)
        except ValidationError:
            return error('Bitte die Antworten und den Korrekturgrund prüfen. Werte und Pflichtfelder müssen zur ursprünglichen Fragebogenversion passen.',400)
        except SurveyConflict as failure:
            return error(str(failure),409)
        except LookupError as failure:
            return error(str(failure),404)
        except ValueError as failure:
            return error(str(failure),400)
        row=data.detail(response_id)
        return jsonify(row) if row else error('Antwort nicht gefunden.',404)
    @bp.get('/analytics')
    @protected
    def analysis():
        try:query,version,status,arm=filters()
        except ValueError:return error('Ungültiger Filter.',400)
        return jsonify(analytics(data.filtered(query,version,status,arm),version))
    @bp.get('/deletion-preview')
    @protected
    def deletion_preview():
        return jsonify(data.deletion_preview())
    @bp.delete('/responses')
    @protected
    def delete_all():
        body=request.get_json(silent=True)
        if (not isinstance(body,dict) or set(body)!={'confirmation','fingerprint'}
            or body['confirmation']!='ALLE TEILNAHMEN LÖSCHEN' or not isinstance(body['fingerprint'],str)):
            return error('Bitte die vollständige Löschbestätigung eingeben.',400)
        try: result=data.delete_all(body['fingerprint'])
        except ValueError as failure:return error(str(failure),409)
        return jsonify(deleted=True,counts=result)
    @bp.delete('/responses/<response_id>')
    @protected
    def delete(response_id):
        body=request.get_json(silent=True)
        if not isinstance(body,dict) or set(body)!={'confirm_id'} or not isinstance(body['confirm_id'],str):return error('Teilnahme-ID zur Bestätigung fehlt.',400)
        if not data.delete(response_id,body['confirm_id']):return error('Antwort nicht gefunden oder ID stimmt nicht überein.',409)
        return jsonify(deleted=True)
    @bp.get('/export')
    @protected
    def export():
        try:query,version,status,arm=filters()
        except ValueError:return error('Ungültiger Filter.',400)
        rows=data.filtered(query,version,status,arm);kind=request.args.get('format','csv')
        columns=request.args.get('columns','readable')
        if columns not in ('readable','technical'):return error('Unbekannte Spaltenbenennung.',400)
        if kind=='csv':content=data.csv_data(rows,columns=columns);filename='diana_numiqo.csv';mime='text/csv; charset=utf-8'
        elif kind=='zip':content=data.package(rows,columns=columns);filename='diana_auswertung.zip';mime='application/zip'
        else:return error('Unbekanntes Exportformat.',400)
        response=make_response(content);response.headers['Content-Type']=mime
        response.headers['Content-Disposition']=f'attachment; filename="{filename}"'
        response.headers['X-Content-Type-Options']='nosniff';return response
    app.register_blueprint(bp)
