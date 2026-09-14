import test from 'node:test';
import assert from 'node:assert/strict';
import React from 'react';
import {renderToStaticMarkup} from 'react-dom/server';
import {createServer} from 'vite';
import {newSurveyState, surveyConfiguration, visibleFields, applyStudyAssignment,
  loadSurveyState, saveSurveyState, restoreServerDraft, needsSystemPreparation,
  startPreparedSystem, remainingWaitingGroups, changeSurveyAnswer, submitSurvey} from './survey.js';
import {draftPayload} from './survey-autosave.js';

const removed=['search_ease','express_search_needs','adapt_search_ease','template_selection_ease','personality_setup'];
function complete(arm, version='diana-v10') {
  const fields=surveyConfiguration(version).surveyFields;
  const values=Object.fromEntries(fields.map(field=>[field.name,field.kind==='scale'?8:field.kind==='choice'?field.options[0][0]:field.optional?'':'Data Science']));
  return {...newSurveyState(),version,systemCompleted:true,chatCompleted:true,stage:'feedback',
    answers:changeSurveyAnswer(values,'study_arm',arm,version)};
}

test('short questionnaire removes only the five usability and setup fields',()=>{
  const old=surveyConfiguration('diana-v9'), current=surveyConfiguration('diana-v10');
  assert.deepEqual(current.surveyFields,old.surveyFields.filter(field=>!removed.includes(field.name)));
  for(const [arm,count] of [['A',15],['B',20],['C',21]]) {
    const fields=visibleFields(current.surveyFields,{study_arm:arm}).filter(field=>!field.systemProvided);
    assert.equal(fields.length,count);
    assert.equal(fields.filter(field=>field.optional).length,2);
  }
});

test('old v9 drafts and completed confirmations retain their version, ratings and assignment',()=>{
  for(const submitted of [false,true]) {
    const old={...complete('C','diana-v9'),submitted};
    const memory=new Map([['diana-survey:diana-v9',JSON.stringify(old)]]);
    const storage={getItem:key=>memory.get(key)||null,setItem:(key,value)=>memory.set(key,value)};
    const loaded=loadSurveyState(storage);
    assert.equal(loaded.version,'diana-v9');assert.deepEqual(loaded.answers,old.answers);
    const assigned=applyStudyAssignment(loaded,{arm:'C',experiment_id:'diana-abc-v2'});
    assert.equal(assigned.version,'diana-v9');assert.equal(assigned.runId,old.runId);
    assert.equal(assigned.answers.personality_setup,8);
    assert.equal(draftPayload(assigned).answers.template_selection_ease,null);
    saveSurveyState(storage,assigned);
    assert.equal(loadSurveyState(storage).version,'diana-v9');
    assert.equal(loadSurveyState(storage).submitted,submitted);
  }
});

test('v10 resumes after reload and preserves preparation and factual waiting questions',()=>{
  const fresh=applyStudyAssignment(newSurveyState(),{arm:'B',experiment_id:'diana-abc-v3',questionnaire_version:'diana-v10'});
  assert.equal(needsSystemPreparation(fresh),true);
  const prepared=startPreparedSystem({...fresh,answers:{...fresh.answers,job_portal_experience:'never',ai_chat_experience:'daily'}});
  const memory=new Map(), storage={getItem:key=>memory.get(key)||null,setItem:(key,value)=>memory.set(key,value)};
  saveSurveyState(storage,prepared);
  const loaded=loadSurveyState(storage);
  assert.equal(loaded.version,'diana-v10');assert.equal(loaded.submissionId,prepared.submissionId);
  assert.equal(needsSystemPreparation(loaded),false);
  assert.deepEqual(remainingWaitingGroups(loaded).flatMap(group=>group.fields).map(field=>field.name),['age_group','gender','education','study_field','search_goal']);
  const restored=restoreServerDraft(fresh,{...draftPayload(prepared),revision:prepared.draftRevision+1});
  assert.equal(needsSystemPreparation(restored),false);
});

test('removed answers are absent from v10 autosave and submission while v9 remains writable',async()=>{
  for(const version of ['diana-v9','diana-v10']) {
    const state=complete('C',version);
    const payload=draftPayload(state);
    for(const name of removed)assert.equal(Object.hasOwn(payload.answers,name),version==='diana-v9');
    await submitSurvey(state,{request:async(_,options)=>{
      const sent=JSON.parse(options.body);
      assert.equal(sent.version,version);
      assert.equal(sent.system_usefulness,8);
      for(const name of removed)assert.equal(Object.hasOwn(sent,name),version==='diana-v9');
      return new Response(JSON.stringify({saved:true}));
    }});
  }
});

test('rendered current forms omit the removed questions and historical v9 renders them',async()=>{
  const vite=await createServer({server:{middlewareMode:true,hmr:false},appType:'custom'});
  try {
    const {SurveyForm}=await vite.ssrLoadModule('/SurveyPage.jsx');
    for(const version of ['diana-v9','diana-v10'])for(const arm of ['A','B','C']) {
      const state=complete(arm,version), config=surveyConfiguration(version);
      const markup=config.surveyCategories.map(group=>renderToStaticMarkup(React.createElement(SurveyForm,{version,group,answers:state.answers,onChange:()=>{},onSubmit:()=>{},onBack:()=>{}}))).join('');
      assert.ok(markup.includes('Wie hilfreich war das System für die Durchführung deiner Suche?'));
      assert.equal(markup.includes('Wie einfach war es, das Suchsystem zu bedienen?'),version==='diana-v9');
      assert.equal(markup.includes('Wie einfach war es, eine KI-Vorlage auszuwählen?'),version==='diana-v9' && arm==='B');
      assert.equal(markup.includes('Wie einfach war es, deine KI-Suchpersönlichkeit selbst zu gestalten?'),version==='diana-v9' && arm==='C');
    }
  } finally {await vite.close();}
});
