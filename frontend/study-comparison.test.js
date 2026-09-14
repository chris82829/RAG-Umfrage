import test from 'node:test';
import assert from 'node:assert/strict';
import {applyStudyAssignment, surveyConfiguration, newSurveyState, surveyFields, fieldVisible, displaySurveyGroup, surveyErrors, remainingWaitingGroups, markWaitingFields, finishWaitingIfReady, nextSurveyState, loadSurveyState, saveSurveyState, submitSurvey, changeSurveyAnswer} from './survey.js';
import {draftPayload} from './survey-autosave.js';

function complete(arm='C',version='diana-v9') {
 const fields=surveyConfiguration(version).surveyFields;
 const answers=Object.fromEntries(fields.map(field=>[field.name,field.kind==='scale'?8:field.kind==='choice'?field.options[0][0]:field.optional?'':'Softwareentwicklung']));
 answers.study_arm=arm;
 return {...newSurveyState(),version,systemCompleted:true,chatCompleted:true,answers:changeSurveyAnswer(answers,'study_arm',arm,version)};
}

test('A B C share outcomes and score/reasons while setup matches actual capabilities',()=>{
 const a=complete('A'),b=complete('B'),c=complete('C');
 for(const state of [a,b,c])assert.deepEqual(surveyErrors(state.answers),{});
 assert.equal(displaySurveyGroup(a,'personality').fields.length,0);
 assert.deepEqual(displaySurveyGroup(a,'usefulness'),displaySurveyGroup(b,'usefulness'));
 assert.deepEqual(displaySurveyGroup(b,'usefulness'),displaySurveyGroup(c,'usefulness'));
 assert.ok(displaySurveyGroup(b,'personality').fields.some(field=>field.name==='template_selection_ease'));
 assert.ok(!displaySurveyGroup(b,'personality').fields.some(field=>field.name==='personality_customized'));
 assert.ok(displaySurveyGroup(c,'personality').fields.some(field=>field.name==='personality_customized'));
 assert.ok(!displaySurveyGroup(c,'personality').fields.some(field=>field.name==='template_selection_ease'));
 assert.equal(draftPayload(a).answers.score_usefulness,8);
 assert.equal(draftPayload(b).answers.personality_setup,null);
 assert.equal(draftPayload(c).answers.template_selection_ease,null);
 for(const name of ['search_ease','system_usefulness','chat_helpfulness','future_use'])assert.ok(!surveyFields.find(field=>field.name===name).visibleIf);
});

test('waiting questions contain only relevant setup and are skipped later for each arm',()=>{
 for(const arm of ['A','B','C']) {
  let state=complete(arm);
  for(const group of remainingWaitingGroups(state))state=markWaitingFields(state,group.fields);
  state=finishWaitingIfReady(state);
  assert.equal(remainingWaitingGroups(state).length,0);
  assert.equal(nextSurveyState(state).stage,'overall');
  assert.ok(!state.waitingAnswered.includes('study_arm'));
  if(arm==='B')assert.ok(!state.waitingAnswered.includes('personality_setup'));
  if(arm==='A')assert.ok(!state.waitingAnswered.includes('template_selection_ease'));
 }
});

test('new ABC assignment persists and cannot manufacture completed chat',()=>{
 const state=applyStudyAssignment({...newSurveyState(),systemCompleted:true},{arm:'C',experiment_id:'diana-abc-v2',questionnaire_version:'diana-v9'});
 const data=new Map(),storage={getItem:key=>data.get(key)??null,setItem:(key,value)=>data.set(key,value)};
 saveSurveyState(storage,state);const restored=loadSurveyState(storage);
 assert.equal(restored.answers.study_arm,'C');assert.equal(restored.chatCompleted,false);
 assert.equal(nextSurveyState(restored),restored);
 assert.throws(()=>applyStudyAssignment(state,{arm:'D'}));
});

test('unfinished historical v7 B keeps answers, free setup and its run',async()=>{
 const old={...complete('B','diana-v7'),stage:'feedback',waitingAnswered:['age_group','search_goal','personality_setup']};
 const storage={getItem:key=>key==='diana-survey:diana-v7'?JSON.stringify(old):null};
 const current=applyStudyAssignment(loadSurveyState(storage),{arm:'B',experiment_id:'diana-ab-v1',questionnaire_version:'diana-v7'});
 assert.equal(current.version,'diana-v7');assert.equal(current.runId,old.runId);
 assert.equal(current.stage,'feedback');assert.deepEqual(current.answers,old.answers);
 assert.deepEqual(current.waitingAnswered,old.waitingAnswered);
 assert.equal(draftPayload(current).version,'diana-v7');
 assert.equal(draftPayload(current).answers.personality_customized,'yes');
 await submitSurvey(current,{request:async(_,options)=>{
  const sent=JSON.parse(options.body);assert.equal(sent.version,'diana-v7');
  assert.equal(sent.personality_setup,8);assert.equal(sent.template_selection_ease,undefined);
  return new Response(JSON.stringify({saved:true}));
 }});
});

test('historical BC retains original v6 or already-migrated v7 without relabeling answers',()=>{
 for(const [version,storedArm] of [['diana-v6','C'],['diana-v7','B']]) {
  const old={...complete(storedArm,version),stage:'feedback',waitingAnswered:['age_group','search_goal','personality_setup']};
  const storage={getItem:key=>key===`diana-survey:${version}`?JSON.stringify(old):null};
  const current=applyStudyAssignment(loadSurveyState(storage),{arm:'B',experiment_id:'diana-bc-v1',questionnaire_version:'diana-v6'});
  assert.equal(current.version,version);assert.equal(current.answers.study_arm,storedArm);
  assert.equal(current.runId,old.runId);assert.deepEqual(current.answers,old.answers);
 }
});

test('completed old participants retain original confirmation and historical answers',()=>{
 for(const version of ['diana-v6','diana-v7']) {
  const completed={...complete(version==='diana-v6'?'C':'B',version),stage:'feedback',submitted:true};
  const storage={getItem:key=>key===`diana-survey:${version}`?JSON.stringify(completed):null};
  assert.deepEqual(loadSurveyState(storage),completed);
 }
});
