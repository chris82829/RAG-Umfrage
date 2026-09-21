"""Offline endpoint tests: frontend flags and posted counts cannot bypass eligibility."""
import unittest
from test_survey_chat_limit import SurveyChatLimitTests
from survey_store import VERSIONED_FIELDS, field_visible

class StudyProgressTests(SurveyChatLimitTests):
    # Reuse fixture helpers only; unittest also runs inherited allowance checks.
    def answers(self, version, arm):
        values={'study_arm': arm}
        for field in VERSIONED_FIELDS[version]:
            key=field['name']
            if key=='study_arm': continue
            if not field_visible(field, values): values[key]=None
            elif field['kind']=='scale': values[key]=3
            elif field['kind']=='choice': values[key]=field['options'][0][0]
            else: values[key]='Python-Stelle gesucht' if not field.get('optional') else ''
        return values

    def test_proceed_and_direct_submission_require_three_successful_exchanges(self):
        headers=self.grant('C')
        assignment=self.client.post('/api/study-assignment',headers=headers).json
        version=assignment['questionnaire_version']
        state=self.onboard(headers)
        answers=self.answers(version,'C')
        submission=dict(submission_id='1'*32, version=version, **answers)
        for count in range(3):
            result=self.client.post('/api/proceed_to_survey',headers=headers,
                json=dict(messageCount=99, session_id=state['session_id']))
            self.assertEqual(result.status_code,403,result.json)
            self.assertEqual(result.json['error']['chat_progress']['used'],count)
            result=self.client.post('/api/survey-responses',headers=headers,json=submission)
            self.assertEqual(result.status_code,403,result.json)
            draft=dict(submission_id='2'*32,version=version,revision=count+1,
                waiting_answered=[],answers={'study_arm':'C','search_effort':3})
            result=self.client.put('/api/survey-drafts',headers=headers,json=draft)
            self.assertEqual(result.status_code,403,result.json)
            state=self.chat(headers,state).json
        self.assertEqual(self.client.post('/api/proceed_to_survey',headers=headers).status_code,200)
        result=self.client.post('/api/survey-responses',headers=headers,json=submission)
        self.assertEqual(result.status_code,201,result.json)

    def test_background_and_search_goal_can_autosave_before_chat(self):
        headers=self.grant()
        version=self.client.post('/api/study-assignment',headers=headers).json['questionnaire_version']
        payload=dict(submission_id='3'*32,version=version,revision=1,waiting_answered=[],
            answers={'study_arm':'A','age_group':'25_29','ai_chat_experience':'never','search_goal':'Python Entwickler'})
        response=self.client.put('/api/survey-drafts',headers=headers,json=payload)
        self.assertEqual(response.status_code,200,response.json)

    def test_other_participation_and_test_header_cannot_borrow_eligibility(self):
        headers=self.grant()
        state=self.onboard(headers)
        for _ in range(3):state=self.chat(headers,state).json
        other=self.grant()
        self.assertEqual(self.client.post('/api/proceed_to_survey',headers=other,
            json={'session_id':state['session_id']}).status_code,403)
        standalone=self.grant('A',standalone=True)
        self.assertEqual(self.client.post('/api/proceed_to_survey',headers=standalone).status_code,428)

if __name__=='__main__':unittest.main()
