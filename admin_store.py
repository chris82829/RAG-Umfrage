"""Read-only analysis exports plus explicit administrative deletion."""
import csv
import io
import json
import zipfile
from datetime import datetime, timezone

from survey_store import V5_SURVEY_DEFINITION, VERSIONED_FIELDS, V4_SURVEY_DEFINITION, SURVEY_FIELDS, LEGACY_SURVEY_FIELDS, SURVEY_DEFINITION, LEGACY_SURVEY_DEFINITION, choice_codes, answer_status, QUESTIONS, spreadsheet_text, ADDED_VALUE_LABELS, PREFERENCE_LABELS

LEGACY_FIELDS = ['chat_helpfulness','added_value','future_preference','feedback']
META_FIELDS = ['participation_id','submitted_at_utc','survey_version','study_release_ids','openai_models','reasoning_efforts','response_status','last_saved_at_utc','study_arm','experiment_id','assigned_at_utc','prior_exposure']


class AdminSurveyData:
    def __init__(self, surveys, privacy, releases, sessions):
        self.surveys,self.privacy,self.releases,self.sessions=surveys,privacy,releases,sessions

    def records(self):
        releases=self.releases.all()
        with self.surveys.connect() as db:
            rows=db.execute('''SELECT s.*, p.participation_id, m.metadata_json, a.arm, a.experiment_id, a.assigned_at, a.prior_exposure FROM (
                SELECT submission_id,created_at,created_at AS updated_at,answers_json,'completed' AS response_status FROM survey_responses
                UNION ALL
                SELECT submission_id,created_at,updated_at,answers_json,'in_progress' AS response_status FROM survey_drafts
                WHERE submission_id NOT IN (SELECT submission_id FROM survey_responses)) s
                LEFT JOIN privacy_links l ON l.record_id=s.submission_id AND l.kind='survey'
                LEFT JOIN privacy_consents p ON p.token_hash=l.token_hash
                LEFT JOIN study_assignments a ON a.token_hash=l.token_hash
                LEFT JOIN survey_response_metadata m ON m.submission_id=s.submission_id
                ORDER BY s.updated_at DESC, s.submission_id DESC''').fetchall()
        result=[]
        for row in rows:
            answers=json.loads(row['answers_json'])
            experiment=answers.get('version')=='diana-v6'
            ids=json.loads(row['metadata_json']).get('release_ids',[]) if row['metadata_json'] else []
            result.append(dict(id=row['submission_id'], participation_id=row['participation_id'] or row['submission_id'],
                               study_arm=row['arm'] if experiment else '', experiment_id=row['experiment_id'] if experiment else '', assigned_at_utc=row['assigned_at'] if experiment else '', prior_exposure=row['prior_exposure'] if experiment else '',
                               consent_linked=bool(row['participation_id']), submitted_at_utc=row['created_at'] if row['response_status']=='completed' else '',
                               response_status=row['response_status'],last_saved_at_utc=row['updated_at'],
                               survey_version=answers.pop('version'), answers=answers, study_release_ids=ids,
                               openai_models=sorted({releases[key]['openai_model'] for key in ids if key in releases}),
                               reasoning_efforts=sorted({releases[key]['reasoning_effort'] for key in ids if key in releases})))
        return result

    def filtered(self, query='', version='', status='', arm=''):
        return [row for row in self.records() if (not query or query.casefold() in row['participation_id'].casefold())
                and (not version or row['survey_version']==version) and (not status or row['response_status']==status) and (not arm or row['study_arm']==arm)]

    def detail(self, response_id):
        row=next((row for row in self.records() if row['id']==response_id),None)
        if row:
            links=self.privacy.participant_records(row['participation_id']) if row['consent_linked'] else None
            row['deletion_count']=links.get('survey',1) if links is not None else 1
            row['definition']=SURVEY_DEFINITION if row['survey_version']=='diana-v6' else V5_SURVEY_DEFINITION if row['survey_version']=='diana-v5' else V4_SURVEY_DEFINITION if row['survey_version']=='diana-v4' else LEGACY_SURVEY_DEFINITION
            if row['survey_version']=='diana-v1':
                row['definition']={'version':'diana-v1','demographics':{'fields':[
                    dict(name=name,title=title,options=list(ADDED_VALUE_LABELS.items()) if name=='added_value'
                         else list(PREFERENCE_LABELS.items()) if name=='future_preference' else [])
                    for name,title in zip(LEGACY_FIELDS,QUESTIONS)]},'categories':[]}
        return row

    def delete(self, response_id, confirmation_id):
        row=self.detail(response_id)
        if not row or row['participation_id']!=confirmation_id:
            return False
        if row['consent_linked']:
            for sid in self.privacy.delete_participant(row['participation_id']):self.sessions.delete(sid)
        else:
            with self.surveys.connect() as db:
                db.execute('DELETE FROM survey_response_metadata WHERE submission_id=?',(response_id,))
                db.execute('DELETE FROM survey_responses WHERE submission_id=?',(response_id,))
                db.execute('DELETE FROM survey_drafts WHERE submission_id=?',(response_id,))
        return True

    def codebook(self):
        result=[dict(variable=key,question=key,level='nominal',codes={},missing='empty',versions=['diana-v1','diana-v2','diana-v3','diana-v4','diana-v5','diana-v6']) for key in META_FIELDS]
        for item in result:
            if item['variable']=='study_arm': item['codes']={'B':'Chatbot ohne wählbare Persönlichkeit','C':'Personalisierter Chat- und Suchbot'}
            if item['variable']=='prior_exposure': item['codes']={'0':'Keine frühere DIANA-Suchsitzung unter dieser Teilnahme-ID','1':'Frühere DIANA-Suchsitzung vorhanden'}
        for field in LEGACY_SURVEY_FIELDS:
            scale=field.get('scale',{'low':'Trifft überhaupt nicht zu','high':'Trifft voll und ganz zu'})
            result.append(dict(variable=field['name'],question=field['title'],
                versions=['diana-v3'] if field['name'].endswith('_usefulness') else ['diana-v2','diana-v3'],
                level='ordinal' if field['kind']=='scale' or field['name']=='age_group' else 'nominal' if field['kind']=='choice' else 'text',
                codes={str(i):label for i,(code,label) in enumerate(field.get('options',[]),1) if code!='not_specified'} if field['kind']=='choice' else {},
                original_codes={str(i):code for i,(code,_) in enumerate(field.get('options',[]),1) if code!='not_specified'},
                minimum=1 if field['kind']=='scale' else None,maximum=10 if field['kind']=='scale' else None,
                endpoints=scale if field['kind']=='scale' else None,missing='empty; not asked in this questionnaire version, missing, or explicit Keine Angabe'))
        for name,question in zip(LEGACY_FIELDS,QUESTIONS):
            result.append(dict(variable='v1_'+name,question=question,versions=['diana-v1'],level='ordinal' if name=='chat_helpfulness' else 'text',minimum=1 if name=='chat_helpfulness' else None,maximum=5 if name=='chat_helpfulness' else None,missing='empty for v2/v3/v4',codes=ADDED_VALUE_LABELS if name=='added_value' else PREFERENCE_LABELS if name=='future_preference' else {}))
        for version, fields in VERSIONED_FIELDS.items():
            for field in fields:
                codes=choice_codes(field)
                result.append(dict(variable=version[6:]+'_' +field['name'], question=field['title'],
                    level=field.get('level', 'ordinal' if field['kind']=='scale' or field['name']=='age_group' else 'nominal' if field['kind']=='choice' else 'text'),
                    codes={str(codes[code]):label for code,label in field.get('options',[]) if code in codes},
                    original_codes={str(value):code for code,value in codes.items()},
                    minimum=1 if field['kind']=='scale' else None, maximum=10 if field['kind']=='scale' else None,
                    endpoints=field.get('scale'), visible_if=field.get('visibleIf'), versions=[version],
                    missing='empty; see companion _status column. No=0 is a valid answer.'))
                result.append(dict(variable=version[6:]+'_' +field['name']+'_status', question='Antwortstatus: '+field['title'], level='nominal',
                    codes=dict(answered='Beantwortet', not_used='Nicht genutzt', not_assessable='Kann ich nicht beurteilen',
                        not_specified='Keine Angabe', skipped='Durch Filterführung übersprungen', no_answer='Optionales Feld leer', not_asked='Andere Fragebogenversion', unanswered='Noch nicht beantwortet'),
                    missing='none', visible_if=field.get('visibleIf'), versions=[version]))
        return result

    def csv_data(self, rows, delimiter=';'):
        stream=io.StringIO(newline='');writer=csv.writer(stream,delimiter=delimiter)
        writer.writerow(META_FIELDS+[field['name'] for field in LEGACY_SURVEY_FIELDS]+['v1_'+name for name in LEGACY_FIELDS]+[column for version, fields in VERSIONED_FIELDS.items() for field in fields for column in (version[6:]+'_'+field['name'], version[6:]+'_'+field['name']+'_status')])
        for row in rows:
            values=[row['participation_id'],row['submitted_at_utc'],row['survey_version'],
                    '|'.join(row['study_release_ids']),'|'.join(row['openai_models']),'|'.join(row['reasoning_efforts']),row['response_status'],row['last_saved_at_utc'],row['study_arm'],row['experiment_id'],row['assigned_at_utc'],row['prior_exposure']]
            for field in LEGACY_SURVEY_FIELDS:
                value=row['answers'].get(field['name'],'') if row['survey_version'] in ('diana-v2','diana-v3') else ''
                if field['kind']=='choice' and value!='':
                    value=next((i for i,(key,_) in enumerate(field['options'],1) if key==value and key!='not_specified'),'')
                values.append(value)
            values.extend(row['answers'].get(name,'') if row['survey_version']=='diana-v1' else '' for name in LEGACY_FIELDS)
            for version, fields in VERSIONED_FIELDS.items():
                for field in fields:
                    status=answer_status(field,row['answers']) if row['survey_version']==version else 'not_asked'
                    value=row['answers'].get(field['name'],'') if status=='answered' else ''
                    if field['kind']=='choice' and status=='answered': value=choice_codes(field)[value]
                    values.extend([value,status])
            writer.writerow([spreadsheet_text(value) if isinstance(value,str) else value for value in values])
        return stream.getvalue().encode('utf-8-sig')

    def package(self, rows):
        stream=io.BytesIO();book=self.codebook();csvbook=io.StringIO(newline='');writer=csv.writer(csvbook,delimiter=';')
        writer.writerow(['variable','question','measurement_level','codes','minimum','maximum','endpoints','missing','visible_if','versions'])
        for field in book:writer.writerow([field['variable'],field['question'],field['level'],json.dumps(field.get('codes',{}),ensure_ascii=False),field.get('minimum'),field.get('maximum'),json.dumps(field.get('endpoints'),ensure_ascii=False),field['missing'],json.dumps(field.get('visible_if'),ensure_ascii=False),json.dumps(field.get('versions', ['diana-v1'] if field['variable'].startswith('v1_') else ['diana-v2','diana-v3']),ensure_ascii=False)])
        ids={key for row in rows for key in row['study_release_ids']};releases=self.releases.all()
        manifest=dict(exported_at=datetime.now(timezone.utc).isoformat(),rows=len(rows),
                      observed_releases={key:releases[key] for key in ids if key in releases},
                      current_configuration=self.releases.manifest,
                      note='Current configuration is not assigned retrospectively to old answers. Empty metadata means unknown, not the current model.')
        with zipfile.ZipFile(stream,'w',zipfile.ZIP_DEFLATED) as archive:
            archive.writestr('diana_numiqo.csv',self.csv_data(rows))
            archive.writestr('codebook.csv',csvbook.getvalue().encode('utf-8-sig'))
            archive.writestr('codebook.json',json.dumps(book,ensure_ascii=False,indent=2))
            archive.writestr('study_manifest.json',json.dumps(manifest,ensure_ascii=False,indent=2))
            archive.writestr('README.txt','In Numiqo: Import/Export > Datei auswählen > diana_numiqo.csv. UTF-8, Semikolon. Eine Zeile pro Teilnahme. response_status unterscheidet completed (abgeschlossen) und in_progress (unvollständig); für reine Abschlussauswertungen completed filtern. last_saved_at_utc ist der letzte Speicherzeitpunkt, submitted_at_utc bleibt bei Entwürfen leer. Codes im Codebuch. V6 / diana-bc-v1: study_arm dokumentiert die serverseitige 50:50-Zufallszuordnung B oder C. prior_exposure=1 kennzeichnet eine bereits vorhandene Suchsitzung vor der Zuordnung. Gemeinsame Ergebnisfragen stehen in v6_-Spalten. Persönlichkeitsfragen sind in B skipped. search_effort ist gegenläufig: hohe Werte bedeuten hohen Aufwand. Keine Zusammenfassung aller Bewertungen zu einem ungeprüften Gesamtwert. V5: Alle Bewertungen ordinal 1–10, Ja=1 und Nein=0; getrennte v5_-Spalten. Die Frage zur Chatnutzung entfällt. V4: Ja=1, Nein=0; beschriftete Abstufungen ordinal 1–5, Nützlichkeit und Chat-Hilfe ordinal 1–10. V4-Variablen beginnen mit v4_, ältere Antworten stehen unverändert in getrennten Spalten. _status unterscheidet Nicht genutzt, Nicht beurteilbar, übersprungen und andere Fragebogenversionen. Die neutrale Wiederverwendungsantwort Unentschieden ist ein gültiger Wert 3. Frageformulierung und Filterführung im Codebuch berücksichtigen; Versionen nicht ungeprüft zusammenfassen. Leere Zellen sind fehlende Werte, nicht Null; auch „Keine Angabe“ wird leer exportiert. ID/Datum/Modellspalten als nominal behandeln. Keine automatische Datenübertragung. CSV-Freitext mit Formelpräfix erhält ein führendes Apostroph als Schutz für Tabellenprogramme. Die Daten sind pseudonymisiert, nicht anonym.\n')
        return stream.getvalue()
