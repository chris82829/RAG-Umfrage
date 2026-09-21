import assert from 'node:assert/strict';
import test from 'node:test';

import {
  SURVEY_VERSION, applyStudyAssignment, emptyAnswers, loadSurveyState,
  needsSystemPreparation, newSurveyState, remainingWaitingGroups,
  restoreServerDraft, startPreparedSystem, surveyConfiguration,
} from './survey.js';

const assigned = (version, arm = 'C') => applyStudyAssignment(newSurveyState(), {
  arm, experiment_id: 'diana-abc-v4', questionnaire_version: version,
});
const names = fields => fields.map(field => field.name);

test('new participants accept the backend V11 assignment in all three arms', () => {
  assert.equal(SURVEY_VERSION, 'diana-v11');
  for (const arm of ['A', 'B', 'C']) {
    const state = assigned('diana-v11', arm);
    assert.equal(state.version, 'diana-v11');
    assert.equal(state.answers.study_arm, arm);
    assert.equal(state.assignment.questionnaire_version, 'diana-v11');
    assert.equal(needsSystemPreparation(state), true);
  }
  const armField = surveyConfiguration('diana-v11').surveyFields.find(field => field.name === 'study_arm');
  assert.equal(armField.options[0][1], 'A – Basissystem ohne KI-Suchpersönlichkeit');
  assert.throws(() => assigned('diana-v99'), /Fragebogenversion ist nicht verfügbar/);
});

test('V11 requires both experience answers before opening the system and skips them while waiting', () => {
  let state = assigned('diana-v11');
  const fields = surveyConfiguration(state).beforeSystemFields;
  assert.deepEqual(names(fields), ['job_portal_experience', 'ai_chat_experience']);
  assert.equal(startPreparedSystem(state), state);
  state = {...state, answers: {...state.answers, job_portal_experience: 'weekly'}};
  assert.equal(startPreparedSystem(state), state);
  state = {...state, answers: {...state.answers, ai_chat_experience: 'daily'}};
  const started = startPreparedSystem(state);
  assert.equal(started.systemTaskStarted, true);
  assert.equal(needsSystemPreparation(started), false);
  assert.deepEqual(started.waitingAnswered, names(fields));
  assert.deepEqual(remainingWaitingGroups(started).flatMap(group => names(group.fields)), [
    'age_group', 'gender', 'education', 'study_field', 'search_goal',
  ]);
  // Server drafts persist answered fields, not the browser's start flag.
  assert.equal(needsSystemPreparation({...started, systemTaskStarted: false}), false);
});

test('V11 only permits factual questions during search, leaving evaluations until afterwards', () => {
  const configuration = surveyConfiguration('diana-v11');
  assert.deepEqual(names(configuration.waitingQuestionFields), ['search_goal']);
  assert.deepEqual(configuration.waitingQuestionGroups.flatMap(group => names(group.fields)), [
    'age_group', 'gender', 'education', 'study_field', 'job_portal_experience', 'ai_chat_experience', 'search_goal',
  ]);
  assert(configuration.surveyFields.some(field => field.name === 'personality_customized'));
  assert(configuration.surveyFields.some(field => field.name === 'system_usefulness'));
});

test('V11 resumes browser and server drafts with the assigned version and completed preparation', () => {
  const initial = assigned('diana-v11', 'B');
  const prepared = startPreparedSystem({...initial, answers: {...initial.answers,
    job_portal_experience: 'never', ai_chat_experience: 'not_specified',
  }});
  const fromBrowser = loadSurveyState({getItem: key => key === 'diana-survey:diana-v11' ? JSON.stringify(prepared) : null});
  assert.equal(fromBrowser.submissionId, prepared.submissionId);
  assert.equal(fromBrowser.answers.study_arm, 'B');
  assert.equal(needsSystemPreparation(fromBrowser), false);

  const fromServer = restoreServerDraft(initial, {version: 'diana-v11', revision: prepared.draftRevision + 1,
    answers: prepared.answers, waiting_answered: prepared.waitingAnswered,
  });
  assert.equal(fromServer.answers.job_portal_experience, 'never');
  assert.equal(needsSystemPreparation(fromServer), false);
});

test('V10 remains independently assigned and restorable, with its preparation and waiting rules', () => {
  const state = assigned('diana-v10', 'A');
  assert.equal(state.version, 'diana-v10');
  assert.equal(needsSystemPreparation(state), true);
  assert.deepEqual(names(surveyConfiguration(state).waitingQuestionFields), ['search_goal']);
  const fromBrowser = loadSurveyState({getItem: key => key === 'diana-survey:diana-v10' ? JSON.stringify(state) : null});
  assert.equal(fromBrowser.version, 'diana-v10');
  assert.equal(fromBrowser.submissionId, state.submissionId);
  assert.deepEqual(fromBrowser.answers, state.answers);
});

test('earlier questionnaires retain their version-specific preparation and waiting behavior', () => {
  assert.equal(needsSystemPreparation(assigned('diana-v9')), true);
  assert.deepEqual(names(surveyConfiguration('diana-v9').waitingQuestionFields), ['search_goal']);
  const historical = assigned('diana-v8');
  assert.equal(needsSystemPreparation(historical), false);
  assert.deepEqual(names(surveyConfiguration(historical).waitingQuestionFields), [
    'search_goal', 'personality_customized', 'template_selection_ease', 'personality_setup',
  ]);
  for (const version of ['diana-v4', 'diana-v5', 'diana-v6', 'diana-v7', 'diana-v8', 'diana-v9', 'diana-v10']) {
    assert.equal(assigned(version).version, version);
    assert('search_goal' in emptyAnswers(version));
  }
});
