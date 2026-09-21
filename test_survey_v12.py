"""Offline contracts for the exact V12 questionnaire and non-destructive storage."""
import csv
import io
import json
import sqlite3
import tempfile
import unittest
from pathlib import Path

from pydantic import ValidationError
from admin_store import AdminSurveyData, displayed_study_arm
from export_columns import export_name
from survey_analytics import analytics
from survey_store import (SURVEY_VERSION, SURVEY_FIELDS, VERSIONED_FIELDS, SurveyStore,
                          SurveyRequest, SurveyDraftRequest, field_visible)
from survey_migrations import USEFULNESS_ITEMS


def answers(version='diana-v12', arm='C'):
    result={'version':version, 'study_arm':arm}
    for field in VERSIONED_FIELDS[version]:
        name=field['name']
        if name=='study_arm': continue
        if not field_visible(field,result): result[name]=None
        elif field['kind']=='choice': result[name]=field['options'][0][0]
        elif field['kind']=='scale': result[name]=field.get('scale',{}).get('max',10)
        else: result[name]='' if field.get('optional') else 'Data Science Werkstudent'
    return result


class SurveyV12Tests(unittest.TestCase):
    def test_appendix_counts_and_exact_items(self):
        self.assertEqual(SURVEY_VERSION,'diana-v12')
        for arm,count in [('A',17),('B',21),('C',22)]:
            self.assertEqual(sum(not f.get('systemProvided') and field_visible(f,{'study_arm':arm}) for f in SURVEY_FIELDS),count)
            SurveyRequest.model_validate(dict(submission_id='a'*32,**answers(arm=arm)))
        fields={f['name']:f for f in SURVEY_FIELDS}
        self.assertEqual(sum(f.get('beforeSystem',False) for f in SURVEY_FIELDS),6)
        self.assertEqual(fields['personality_clarity_explanations']['title'],'Wie klar war dir, wie deine KI-Suchpersönlichkeit den Sprachstil und die Formulierung der Begründungen beeinflusst?')
        for old in ('system_usefulness','personalized_search_usefulness','personality_clarity_search'):
            self.assertNotIn(old,fields)
            self.assertIn(old,{f['name'] for f in VERSIONED_FIELDS['diana-v11']})
        self.assertEqual([fields[name]['title'] for name in USEFULNESS_ITEMS],[
            'Die Nutzung des Systems hat meine Stellensuche effektiver gemacht.',
            'Das System hat mir geholfen, passende Stellen schneller zu finden.',
            'Insgesamt fand ich das System nützlich für meine Stellensuche.'])
        self.assertEqual(fields['usefulness_effective']['scale']['labels'],[
            'Stimme gar nicht zu','Stimme eher nicht zu','Neutral','Stimme eher zu','Stimme voll zu'])

    def test_api_rejects_out_of_range_items_and_keeps_legacy_scales(self):
        for name in USEFULNESS_ITEMS:
            for value in (0,6,10,True,2.5):
                with self.subTest(name=name,value=value),self.assertRaises(ValidationError):
                    SurveyRequest.model_validate(dict(submission_id='a'*32,**{**answers(),name:value}))
            for value in (1,5,'not_assessable'):
                SurveyRequest.model_validate(dict(submission_id='a'*32,**{**answers(),name:value}))
        SurveyRequest.model_validate(dict(submission_id='a'*32,**answers('diana-v11')))
        with self.assertRaises(ValidationError):
            SurveyRequest.model_validate(dict(submission_id='a'*32,**answers(),personalized_search_usefulness=10))

    def test_migration_is_idempotent_and_preserves_old_answers(self):
        with tempfile.TemporaryDirectory() as directory:
            path=Path(directory)/'survey.db'
            # Real old schema and answers before application startup / migration.
            original=json.dumps(answers('diana-v11'),ensure_ascii=False)
            with sqlite3.connect(path) as db:
                db.execute('CREATE TABLE survey_responses(submission_id TEXT PRIMARY KEY, created_at TEXT NOT NULL, answers_json TEXT NOT NULL)')
                db.execute('INSERT INTO survey_responses VALUES(?,?,?)',('old','2026-09-01',original))
            store=SurveyStore(path);SurveyStore(path)
            with store.connect() as db:
                row=db.execute('SELECT * FROM survey_responses WHERE submission_id="old"').fetchone()
                self.assertEqual(row['answers_json'],original)
                self.assertTrue(all(row[name] is None for name in USEFULNESS_ITEMS))
            submitted=SurveyRequest.model_validate(dict(submission_id='a'*32,**answers())).root
            self.assertTrue(store.save(submitted))
            self.assertFalse(store.save(submitted))
            draft=SurveyDraftRequest.model_validate(dict(submission_id='b'*32,version='diana-v12',revision=1,
                answers={'study_arm':'A','usefulness_speed':3,'usefulness_effective':'not_assessable'})).root
            store.save_draft(draft)
            with store.connect() as db:
                row=db.execute('SELECT * FROM survey_drafts').fetchone()
                self.assertEqual(row['usefulness_speed'],3)
                self.assertIsNone(row['usefulness_effective'])
                db.execute("UPDATE survey_drafts SET answers_json=json_set(answers_json,'$.usefulness_speed',4)")
                self.assertEqual(db.execute('SELECT usefulness_speed FROM survey_drafts').fetchone()[0],4)
                with self.assertRaises(sqlite3.IntegrityError):
                    db.execute("UPDATE survey_drafts SET answers_json=json_set(answers_json,'$.usefulness_speed',9)")
            stream=io.StringIO();store.export_csv(stream,columns='technical')
            rows=list(csv.DictReader(io.StringIO(stream.getvalue()),delimiter=';'))
            self.assertEqual(rows[0]['v11_personalized_search_usefulness'],'10')
            self.assertEqual(rows[0]['v12_usefulness_effective'],'')
            self.assertEqual(rows[1]['v12_usefulness_effective'],'5')
            self.assertNotIn('v12_personalized_search_usefulness',rows[1])

    def test_codebook_and_analytics_use_five_point_anchors(self):
        store=object.__new__(AdminSurveyData)
        book={item['technical_variable']:item for item in store.codebook()}
        item=book['v12_usefulness_effective']
        self.assertEqual(item['maximum'],5)
        self.assertEqual(item['codes']['3'],'Neutral')
        self.assertIn('deprecated',book['v11_personalized_search_usefulness']['notes'])
        self.assertEqual(export_name('v12_personality_clarity_explanations'),'v12_ki_wirkung_sprachstil_begruendungen_verstaendnis')
        data=answers();self.assertEqual(displayed_study_arm(data),'C')
        row=dict(id='one',participation_id='p',survey_version='diana-v12',response_status='completed',
            study_arm='C',experiment_id='v12-test',presentation_versions=['ranked_insights'],answers=data)
        result=analytics([row],'diana-v12')
        fields={q['name']:q for c in result['cohorts'][0]['categories'] for q in c['questions']}
        field=fields['usefulness_effective']
        self.assertEqual(len(field['overall']['distribution']),5)
        self.assertEqual(field['overall']['distribution'][2]['label'],'Neutral')
        self.assertEqual(field['overall']['mean'],5)
        self.assertEqual(len(fields['search_effort']['overall']['distribution']),10)
        self.assertNotIn('personalized_search_usefulness',fields)


if __name__=='__main__': unittest.main()
