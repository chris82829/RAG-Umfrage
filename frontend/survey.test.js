import test from 'node:test';
import assert from 'node:assert/strict';
import { appPath, appSessionStorage, surveyRun } from './app-session.js';
import { changeSurveyAnswer, fieldVisible, visibleFields, demographics, emptyAnswers, loadSurveyState, newSurveyState, nextSurveyState, reachableStage, saveSurveyState, submitSurvey, surveyCategories, surveyErrors, surveyFields, surveyStages, SURVEY_STORAGE_KEY, suggestSearchGoal, waitingQuestionFields, waitingQuestionGroups } from './survey.js';

test('suggestions prefill and update automatic text while protecting manually edited or cleared answers', () => {
  let state=suggestSearchGoal(newSurveyState(), 'Python Werkstudent');
  assert.equal(state.answers.search_goal,'Python Werkstudent');
  state=suggestSearchGoal(state,'Software Praktikum');
  assert.equal(state.answers.search_goal,'Software Praktikum');
  for(const text of ['Eigene Antwort','']) {
    const edited={...state,searchGoalEdited:true,answers:{...state.answers,search_goal:text}};
    const updated=suggestSearchGoal(edited,'Neue Suche');
    assert.equal(updated.answers.search_goal,text);
    assert.equal(updated.searchGoalSuggestion,'Neue Suche');
    const storage=memoryStorage(); saveSurveyState(storage,updated);
    assert.equal(loadSurveyState(storage).searchGoalEdited,true);
    assert.equal(loadSurveyState(storage).answers.search_goal,text);
  }
  const legacy={...state,searchGoalEdited:undefined};
  assert.equal(suggestSearchGoal(legacy,'Neue Suche').answers.search_goal,state.answers.search_goal);
});

test('waiting questions concern only setup, retain drafts and never unlock final feedback early', () => {
  assert.deepEqual(waitingQuestionFields.map(field=>field.name),['search_goal','personality_customized','template_selection_ease','personality_setup']);
  assert.deepEqual(waitingQuestionGroups[0].fields,demographics.fields);
  const state={...validState(),stage:'system',systemCompleted:false};
  assert.equal(nextSurveyState(state),state);
  const storage=memoryStorage();saveSurveyState(storage,state);
  assert.deepEqual(loadSurveyState(storage).answers,state.answers);
  assert.equal(loadSurveyState(storage).systemCompleted,false);
});

function memoryStorage() {
  const values = new Map();
  return { getItem: key => values.get(key) ?? null, setItem: (key, value) => values.set(key, value), removeItem: key => values.delete(key) };
}
function validState() {
  return { ...newSurveyState(), systemOpened: true, systemCompleted: true, chatCompleted: true, answers: {
    ...emptyAnswers(),
    ...Object.fromEntries(surveyFields.filter(field => field.kind !== 'text').map(field => [field.name, field.kind === 'scale' ? 8 : field.options[0][0]])),
    study_arm:'C', template_selection_ease:null, age_group: '21_24', gender: 'not_specified', education: 'master', study_field: '', search_goal: 'Werkstudent Softwareentwicklung',
  } };
}

test('sixteen numeric evaluations use 1–10 and start with no answer', () => {
  const fields = surveyFields.filter(field => field.kind === 'scale');
  assert.equal(fields.length, 16);
  assert.equal(surveyCategories.length, 6);
  for (const field of fields) {
    assert.equal(emptyAnswers()[field.name], null);
    for (const value of [1, 10]) assert.deepEqual(surveyErrors({study_arm:field.visibleIf?.equals || 'B', [field.name]: value }, [field]), {});
    for (const value of [0, 11, '5', true, 5.5]) assert.ok(surveyErrors({study_arm:field.visibleIf?.equals || 'B', [field.name]: value }, [field])[field.name]);
  }
});

test('demographics allow no disclosure and a blank study field; search context is required', () => {
  const answers = { ...validState().answers, age_group: 'not_specified', gender: 'not_specified', education: 'not_specified' };
  assert.deepEqual(surveyErrors(answers), {});
  assert.ok(surveyErrors({ ...answers, search_goal: '   ' }).search_goal);
  assert.ok(surveyErrors({ ...answers, search_goal: 'x'.repeat(1001) }).search_goal);
  assert.ok(surveyErrors({ ...answers, study_field: 'x'.repeat(161) }).study_field);
});

test('flow opens DIANA first and collects missing demographics after completed search', () => {
  const fresh = newSurveyState();
  assert.equal(fresh.stage, 'system');
  assert.equal(fresh.systemOpened, true);
  assert.equal(nextSurveyState(fresh), fresh);
  const completed = {...fresh,systemCompleted:true,chatCompleted:true};
  const details=nextSurveyState(completed);
  assert.equal(details.stage,'demographics');
  assert.equal(nextSurveyState(details),details);
  const ready={...details,answers:{...details.answers,...Object.fromEntries(demographics.fields.map(field=>[field.name,field.optional?'':'not_specified']))}};
  assert.equal(nextSurveyState(ready).stage,'search_context');
  assert.equal(reachableStage(fresh,'demographics'),'system');
});

test('old demographic drafts keep their answers and now open the system', () => {
  const storage=memoryStorage();
  const old={...newSurveyState(),stage:'demographics',systemOpened:false,answers:{...emptyAnswers(),age_group:'21_24'}};
  saveSurveyState(storage,old);
  const restored=loadSurveyState(storage);
  assert.equal(restored.stage,'system');assert.equal(restored.systemOpened,true);
  assert.equal(restored.answers.age_group,'21_24');
});

test('question categories advance sequentially and retain all answers and the live run when returning', () => {
  let state = validState();
  const originalAnswers = state.answers;
  const run = state.runId;
  for (const stage of surveyStages.slice(1)) {
    state = nextSurveyState(state);
    assert.equal(state.stage, stage);
    assert.equal(state.answers, originalAnswers);
    assert.equal(state.runId, run);
  }
  assert.equal(nextSurveyState(state), state);
  assert.equal(reachableStage(state, 'system'), 'system');
  const changed = { ...state, stage: 'search_context', answers: { ...state.answers, search_goal: '' } };
  assert.equal(nextSurveyState(changed), changed);
  assert.equal(reachableStage(changed, 'overall'), 'search_context');
});

test('missing earlier answers and a never-opened system prevent jumping forward', () => {
  const state = validState();
  assert.equal(reachableStage({ ...state, systemOpened: false }, 'overall'), 'system');
  assert.equal(reachableStage({ ...state, systemCompleted: false }, 'overall'), 'system');
  assert.equal(reachableStage({ ...state, answers: { ...state.answers, personality_setup: null } }, 'feedback'), 'personality');
  assert.equal(reachableStage({ ...state, answers: { ...state.answers, age_group: '' } }, 'dialogue'), 'demographics');
  assert.equal(reachableStage(state, 'invented'), 'system');
});

test('session drafts restore answers, current category, submission state and independent tokens', () => {
  const storage = memoryStorage();
  const state = { ...validState(), stage: 'dialogue' };
  assert.match(state.runId, /^[a-f0-9]{32}$/);
  assert.match(state.submissionId, /^[a-f0-9]{32}$/);
  assert.notEqual(state.runId, state.submissionId);
  saveSurveyState(storage, state);
  assert.deepEqual(loadSurveyState(storage), state);
  saveSurveyState(storage, { ...state, submitted: true });
  assert.equal(loadSurveyState(storage).submitted, true);
});

test('restoration repairs an invalid later page and never turns v1 responses into 1–10 ratings', () => {
  const storage = memoryStorage();
  const fresh = newSurveyState();
  storage.setItem(SURVEY_STORAGE_KEY, JSON.stringify({ ...validState(), stage: 'feedback', answers: { ...validState().answers, personality_clarity_search: 11 } }));
  const restored = loadSurveyState(storage);
  assert.equal(restored.stage, 'personality');
  assert.equal(restored.answers.personality_clarity_search, null);
  storage.setItem(SURVEY_STORAGE_KEY, JSON.stringify({ ...validState(), version: 'diana-v1' }));
  assert.equal(loadSurveyState(storage, () => fresh), fresh);
});

test('invalid or disabled draft storage does not break the survey', () => {
  const fallback = newSurveyState();
  const storage = memoryStorage();
  storage.setItem(SURVEY_STORAGE_KEY, '{');
  assert.equal(loadSurveyState(storage, () => fallback), fallback);
  const blocked = { getItem() { throw new Error(); }, setItem() { throw new Error(); } };
  assert.equal(loadSurveyState(blocked, () => fallback), fallback);
  assert.doesNotThrow(() => saveSurveyState(blocked, fallback));
});

test('drafts without confirmed step 3 return to the system while keeping answers', () => {
  const storage = memoryStorage();
  const oldDraft = { ...validState(), stage: 'dialogue' };
  delete oldDraft.systemCompleted;
  saveSurveyState(storage, oldDraft);
  const restored = loadSurveyState(storage);
  assert.equal(restored.stage, 'system');
  assert.equal(restored.systemCompleted, false);
  assert.deepEqual(restored.answers, oldDraft.answers);
  saveSurveyState(storage, { ...restored, systemCompleted: true, stage: 'dialogue' });
  assert.equal(loadSurveyState(storage).stage, 'dialogue');
});

test('filled answers alone cannot bypass the completed search requirement', async () => {
  const state = { ...validState(), systemCompleted: false };
  await assert.rejects(submitSurvey(state, { request: () => assert.fail('No submission before step 3') }), /erste Suche/);
});

test('sending uses only questionnaire fields, never the run or search/chat state', async () => {
  const state = validState();
  state.answers.profile = { cv: 'Not part of the survey' };
  let sent;
  const request = async (url, options) => {
    assert.equal(url, '/api/survey-responses');
    assert.equal(options.method, 'POST');
    sent = JSON.parse(options.body);
    return new Response(JSON.stringify({ saved: true }), { status: 201 });
  };
  await submitSurvey(state, { request });
  assert.equal(sent.version, 'diana-v8');
  assert.equal(sent.search_goal, state.answers.search_goal);
  assert.equal(sent.future_use, 8);
  assert.equal(sent.profile, undefined);
  assert.ok(!JSON.stringify(sent).includes(state.runId));
});

test('retry sends the same submission ID and answers after uncertain failure', async () => {
  const state = validState();
  const payloads = [];
  const request = async (url, options) => {
    payloads.push(options.body);
    if (payloads.length === 1) throw new TypeError('Connection lost');
    return new Response(JSON.stringify({ saved: true }), { status: 200 });
  };
  await assert.rejects(submitSurvey(state, { request }));
  await submitSurvey(state, { request });
  assert.equal(payloads[0], payloads[1]);
});

test('incomplete answers and invalid responses never produce a success state', async () => {
  await assert.rejects(submitSurvey(newSurveyState(), { request: () => assert.fail('No request for incomplete answers') }));
  for (const status of [400, 409, 500]) await assert.rejects(submitSurvey(validState(), { request: async () => new Response('{}', { status }) }));
  for (const body of ['{}', 'null', '<html>Offline</html>']) await assert.rejects(submitSurvey(validState(), { request: async () => new Response(body) }), /Speicherbestätigung/);
});

test('embedded searches use session storage separate from normal DIANA and other survey runs', () => {
  const host = { location: { search: '' }, localStorage: memoryStorage(), sessionStorage: memoryStorage() };
  const ordinary = appSessionStorage(host);
  ordinary.remember('original-chat');
  host.location.search = `?embed=survey&run=${'a'.repeat(32)}`;
  const embedded = appSessionStorage(host);
  assert.equal(embedded.read(), null);
  embedded.remember('survey-chat');
  assert.equal(appSessionStorage(host).read(), 'survey-chat');
  host.location.search = `?embed=survey&run=${'b'.repeat(32)}`;
  assert.equal(appSessionStorage(host).read(), null);
  assert.equal(ordinary.read(), 'original-chat');
  embedded.remember(null);
  assert.equal(ordinary.read(), 'original-chat');
});

test('internal app navigation retains a valid embedded run', () => {
  const search = `?embed=survey&run=${'a'.repeat(32)}`;
  assert.equal(appPath('about', search), `/${search}`);
  assert.equal(appPath('search', search), `/suche${search}`);
  assert.equal(appPath('search', '?embed=survey&run=invalid'), '/suche');
  assert.equal(surveyRun('?run=' + 'a'.repeat(32)), null);
});

test('blocked browser storage leaves the embedded session usable in memory', () => {
  const host = { location: { search: `?embed=survey&run=${'a'.repeat(32)}` }, get sessionStorage() { throw new Error('Blocked'); } };
  const access = appSessionStorage(host);
  assert.equal(access.read(), null);
  assert.doesNotThrow(() => access.remember('some-session'));
});


test('score and explanations are assessed in both full variants B and C, with meaningful endpoints after system use', () => {
  const fields = surveyCategories.find(group => group.id === 'usefulness').fields;
  assert.deepEqual(fields.map(field => field.name), ['score_usefulness', 'match_reasons_usefulness']);
  for (const field of fields) {
    assert.deepEqual(field.scale, {low: 'Gar nicht nützlich', high: 'Sehr nützlich'});
    assert.deepEqual(field.visibleIf,{field:'study_arm',in:['B','C']});
    assert.ok(!waitingQuestionFields.includes(field));
  }
  const state = validState();
  state.answers.score_usefulness = null;
  assert.equal(reachableStage(state, 'feedback'), 'usefulness');
});

test('unfinished v2 drafts migrate without inventing new answers; completed v2 participants keep confirmation', () => {
  const old = {...validState(), version: 'diana-v2', stage: 'overall'};
  for (const field of surveyCategories.find(group => group.id === 'usefulness').fields) delete old.answers[field.name];
  const storage = memoryStorage();
  storage.setItem('diana-survey:diana-v2', JSON.stringify(old));
  const migrated = loadSurveyState(storage);
  assert.equal(migrated.version, 'diana-v8');
  assert.equal(migrated.stage, 'system');
  assert.equal(migrated.answers.score_usefulness, null);
  assert.equal(migrated.answers.chat_helpfulness, null);
  assert.notEqual(migrated.runId, old.runId);
  assert.equal(migrated.submissionId, old.submissionId);
  saveSurveyState(storage, migrated);
  assert.deepEqual(loadSurveyState(storage), migrated);
  storage.removeItem(SURVEY_STORAGE_KEY);
  storage.setItem('diana-survey:diana-v2', JSON.stringify({...old, submitted: true}));
  const completed = loadSurveyState(storage);
  assert.equal(completed.submitted, true);
  assert.equal(completed.version, 'diana-v2');
  saveSurveyState(storage, completed);
  assert.equal(loadSurveyState(storage).submitted, true);
});


test('binary facts use yes/no; graduated experiences and uncertain future preference stay graded', () => {
  for (const name of ['search_refinement','personality_customized']) {
    const field=surveyFields.find(field=>field.name===name);
    assert.deepEqual(field.options,[['yes','Ja'],['no','Nein']]);
    assert.deepEqual(field.codes,{yes:1,no:0});
    for (const value of ['yes','no']) assert.deepEqual(surveyErrors({study_arm:field.visibleIf?.equals || 'B',[name]:value},[field]),{});
    for (const value of [1,0,true,false,'maybe']) assert.ok(surveyErrors({study_arm:field.visibleIf?.equals || 'B',[name]:value},[field])[name]);
  }
  assert.equal(surveyFields.find(field=>field.name==='future_use').kind,'scale');
});

test('chat self-report is absent and chat evaluations remain visible', async () => {
  const state=validState();
  assert.ok(!surveyFields.some(field=>field.name==='chat_used'));
  assert.ok(visibleFields(surveyFields,state.answers).some(field=>field.name==='chat_helpfulness'));
  assert.ok(!visibleFields(surveyFields,state.answers).some(field=>field.name==='template_selection_ease'));
  await submitSurvey(state,{request:async (_,options)=>{
    const sent=JSON.parse(options.body);
    assert.equal(sent.chat_used,undefined);
    assert.equal(sent.chat_helpfulness,8);
    return new Response(JSON.stringify({saved:true}),{status:201});
  }});
});

test('explicit non-use and inability to judge are valid answers, not low ratings', () => {
  for (const field of surveyFields.filter(field=>field.nonresponse)) {
    for (const [value] of field.nonresponse) assert.deepEqual(surveyErrors({study_arm:field.visibleIf?.equals || 'B',[field.name]:value},[field]),{});
    assert.ok(surveyErrors({study_arm:field.visibleIf?.equals || 'B',[field.name]:'unknown'},[field])[field.name]);
  }
});

test('v3 migration never turns numeric agreement into usage facts', () => {
  const storage=memoryStorage(); const old={...validState(),version:'diana-v3',stage:'overall'};
  old.answers.search_refinement=8; old.answers.personality_setup=8;
  storage.setItem('diana-survey:diana-v3',JSON.stringify(old));
  const restored=loadSurveyState(storage);
  assert.equal(restored.answers.search_refinement,'');
  assert.equal(restored.answers.personality_setup,null);
  assert.equal(restored.answers.chat_used,undefined);
  assert.equal(restored.answers.search_goal,old.answers.search_goal);
  assert.equal(restored.submissionId,old.submissionId);
});


test('search results alone do not unlock the questionnaire; a confirmed chat does', async () => {
  const state={...validState(),stage:'system',chatCompleted:false};
  assert.equal(nextSurveyState(state),state);
  assert.equal(reachableStage(state,'overall'),'system');
  await assert.rejects(submitSurvey(state,{request:()=>assert.fail('No request before chat')}),/Nachricht/);
  assert.equal(nextSurveyState({...state,chatCompleted:true}).stage,'demographics');
  const storage=memoryStorage();saveSurveyState(storage,state);
  assert.equal(loadSurveyState(storage).chatCompleted,false);
  saveSurveyState(storage,{...state,chatCompleted:true});
  assert.equal(loadSurveyState(storage).chatCompleted,true);
});

test('old drafts cannot substitute survey self-reports for actual chat completion', () => {
  const state={...validState(),stage:'overall'};delete state.chatCompleted;
  state.answers.chat_used='yes';
  const storage=memoryStorage();saveSurveyState(storage,state);
  const restored=loadSurveyState(storage);
  assert.equal(restored.stage,'system');assert.equal(restored.chatCompleted,false);
  assert.equal(restored.answers.chat_used,undefined);
});
