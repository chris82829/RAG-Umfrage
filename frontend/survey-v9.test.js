import test from 'node:test';
import assert from 'node:assert/strict';
import React from 'react';
import {renderToStaticMarkup} from 'react-dom/server';
import {createServer} from 'vite';
import {newSurveyState, surveyConfiguration, needsSystemPreparation, startPreparedSystem, remainingWaitingGroups, displaySurveyGroup, restoreServerDraft, applyStudyAssignment, saveSurveyState} from './survey.js';
import {draftPayload} from './survey-autosave.js';

function assigned(arm) {
 return applyStudyAssignment(newSurveyState(),{arm,experiment_id:'diana-abc-v2',questionnaire_version:'diana-v9'});
}

test('all current arms require the same two factual experience answers before opening the system',()=>{
 for(const arm of ['A','B','C']) {
  const fresh=assigned(arm);
  assert.equal(needsSystemPreparation(fresh),true);
  assert.equal(startPreparedSystem(fresh),fresh);
  const answered={...fresh,answers:{...fresh.answers,job_portal_experience:'not_specified',ai_chat_experience:'weekly'}};
  const prepared=startPreparedSystem(answered);
  assert.equal(needsSystemPreparation(prepared),false);
  assert.equal(prepared.systemTaskStarted,true);
  assert.deepEqual(prepared.waitingAnswered,['job_portal_experience','ai_chat_experience']);
  assert.ok(remainingWaitingGroups(prepared).every(group=>group.fields.every(field=>!field.beforeSystem)));
  const draft=draftPayload(prepared);
  assert.equal(draft.answers.job_portal_experience,'not_specified');
  assert.equal(draft.answers.ai_chat_experience,'weekly');
  const resumed=restoreServerDraft(fresh,{...draft,waiting_answered:draft.waiting_answered});
  assert.equal(needsSystemPreparation(resumed),false);
 }
});

test('current waiting questions exclude every evaluation and only ask factual context',()=>{
 for(const arm of ['A','B','C']) {
  const state=assigned(arm), config=surveyConfiguration(state);
  assert.deepEqual(config.waitingQuestionFields.map(field=>field.name),['search_goal']);
  for(const group of remainingWaitingGroups(state))for(const field of group.fields) {
   assert.notEqual(field.kind,'scale');
   assert.ok(!['personality_customized','personality_setup','template_selection_ease'].includes(field.name));
  }
  if(arm!=='A')assert.ok(displaySurveyGroup(state,'personality').fields.length>0);
 }
});

test('ABC v1 resumes v8 including old waiting behavior and never becomes the conference trial',()=>{
 const old={...assigned('C'),version:'diana-v8',systemCompleted:true,chatCompleted:true,
  answers:{...assigned('C').answers,personality_setup:8,personality_customized:'yes'},waitingAnswered:['personality_setup','personality_customized']};
 const resumed=applyStudyAssignment(old,{arm:'C',experiment_id:'diana-abc-v1',questionnaire_version:'diana-v8'});
 assert.equal(resumed.version,'diana-v8');assert.equal(resumed.systemCompleted,true);
 assert.equal(resumed.answers.personality_setup,8);
 assert.ok(surveyConfiguration(resumed).waitingQuestionFields.some(field=>field.name==='personality_setup'));
 assert.equal(needsSystemPreparation(resumed),false);
});

test('preparation task and wording are identical across arms and do not require customization',async()=>{
 const vite=await createServer({server:{middlewareMode:true,hmr:false},appType:'custom'});
 try {
  const {SystemPreparation}=await vite.ssrLoadModule('/SurveyPage.jsx');
  const renders=['A','B','C'].map(arm=>renderToStaticMarkup(React.createElement(SystemPreparation,{state:assigned(arm),errors:{},onChange:()=>{},onStart:()=>{}})));
  assert.equal(renders[0],renders[1]);assert.equal(renders[1],renders[2]);
  assert.match(renders[0],/mindestens eine eigene inhaltliche Frage/);
  assert.match(renders[0],/deine Suchwünsche anschließend präzisieren/);
  assert.match(renders[0],/Keine Angabe/);
  assert.ok(!renders[0].includes('Selbst personalisieren'));
  assert.ok(!renders[0].includes('survey-rating-card'));
 }finally{await vite.close();}
});


test('reload hides saved question inputs until assignment and server draft have been restored',async()=>{
 const previous=globalThis.window;
 const data=new Map();
 const storage={getItem:key=>data.get(key)||null,setItem:(key,value)=>data.set(key,value)};
 const state={...assigned('C'),stage:'experience',systemOpened:true,systemCompleted:true,chatCompleted:true,systemTaskStarted:true};
 saveSurveyState(storage,state);
 globalThis.window={sessionStorage:storage,location:{pathname:'/umfrage',search:''}};
 const vite=await createServer({server:{middlewareMode:true,hmr:false},appType:'custom'});
 try {
  const {default:SurveyPage}=await vite.ssrLoadModule('/SurveyPage.jsx');
  const markup=renderToStaticMarkup(React.createElement(SurveyPage));
  assert.ok(markup.includes('Dein Systemtest wird vorbereitet'));
  assert.ok(!markup.includes('survey-rating-card'));
  assert.ok(!markup.includes('Wie hilfreich war das System'));
 }finally{await vite.close();if(previous===undefined)delete globalThis.window;else globalThis.window=previous;}
});
