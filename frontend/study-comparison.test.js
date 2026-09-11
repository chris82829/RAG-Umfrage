import test from 'node:test';
import assert from 'node:assert/strict';
import {applyStudyAssignment,changeSurveyAnswer,emptyAnswers,newSurveyState,remainingWaitingGroups,markWaitingFields,waitingQuestionGroups,finishWaitingIfReady,surveyFields,surveyErrors,displaySurveyGroup,nextSurveyState,saveSurveyState,loadSurveyState} from './survey.js';
import {draftPayload} from './survey-autosave.js';
function complete(arm){
 let state=applyStudyAssignment({...newSurveyState(),systemCompleted:true,chatCompleted:true},{arm});
 for(const field of surveyFields){
  if(field.systemProvided)continue;
  state.answers=changeSurveyAnswer(state.answers,field.name,field.kind==='scale'?8:field.kind==='choice'?field.options[0][0]:field.optional?'':'Softwareentwicklung');
 }
 return state;
}
test('A and B share common outcomes; only B rates its personality, score and explanation features',()=>{
 const a=complete('A'),b=complete('B');
 assert.deepEqual(surveyErrors(a.answers),{});assert.deepEqual(surveyErrors(b.answers),{});
 assert.equal(displaySurveyGroup(a,'personality').fields.length,0);
 assert.equal(displaySurveyGroup(a,'usefulness').fields.length,0);
 assert.equal(displaySurveyGroup(b,'personality').fields.length,7);
 assert.equal(displaySurveyGroup(b,'usefulness').fields.length,2);
 assert.deepEqual(displaySurveyGroup(a,'overall').fields,displaySurveyGroup(b,'overall').fields);
 for(const f of surveyFields.filter(f=>f.visibleIf))assert.equal(draftPayload(a).answers[f.name],null);
 assert.equal(draftPayload(a).answers.study_arm,'A');
 const stages=[];let state=a;
 while(true){const next=nextSurveyState(state);if(next===state)break;state=next;stages.push(state.stage);}
 assert.ok(!stages.includes('personality'));assert.ok(!stages.includes('usefulness'));assert.equal(stages.at(-1),'feedback');
});
test('A waiting questions consist of demographics and search goal; all can be completed and skipped later',()=>{
 let state=complete('A');
 assert.deepEqual(remainingWaitingGroups(state)[1].fields.map(f=>f.name),['search_goal']);
 state=finishWaitingIfReady(markWaitingFields(state,waitingQuestionGroups[0].fields));
 assert.equal(remainingWaitingGroups(state).length,0);
 assert.ok(!state.waitingAnswered.includes('study_arm'));
 assert.ok(!state.waitingAnswered.includes('personality_setup'));
 assert.equal(nextSurveyState(state).stage,'overall');
});
test('assignment survives questionnaire reload and cannot manufacture a completed chat',()=>{
 const state=applyStudyAssignment(newSurveyState(),{arm:'A'});const data=new Map();const storage={getItem:key=>data.get(key),setItem:(key,value)=>data.set(key,value)};
 saveSurveyState(storage,state);const restored=loadSurveyState(storage);
 assert.equal(restored.answers.study_arm,'A');assert.equal(restored.chatCompleted,false);
 assert.equal(nextSurveyState(restored),restored);
 assert.throws(()=>applyStudyAssignment(state,{arm:'C'}));
});


test('unfinished v6 drafts preserve demographics and goal while clearing outcomes and starting a new test',()=>{
 const old={...complete('B'),version:'diana-v6',stage:'feedback',answers:{...complete('B').answers,study_arm:'C'},waitingAnswered:['age_group','search_goal','personality_setup']};
 const data=new Map([['diana-survey:diana-v6',JSON.stringify(old)]]);
 const storage={getItem:key=>data.get(key)??null,setItem:(key,value)=>data.set(key,value)};
 const current=loadSurveyState(storage);
 assert.equal(current.version,'diana-v7');assert.equal(current.stage,'system');
 assert.equal(current.systemCompleted,false);assert.equal(current.chatCompleted,false);
 assert.notEqual(current.runId,old.runId);assert.equal(current.submissionId,old.submissionId);
 assert.equal(current.answers.age_group,old.answers.age_group);assert.equal(current.answers.search_goal,old.answers.search_goal);
 assert.equal(current.answers.study_arm,'');assert.equal(current.answers.system_usefulness,null);
 assert.equal(current.answers.score_usefulness,null);assert.equal(current.answers.personality_setup,null);
 assert.deepEqual(current.waitingAnswered,['age_group','search_goal']);
});

test('completed v6 participants retain their original confirmation and historical answers',()=>{
 const completed={...complete('B'),version:'diana-v6',stage:'feedback',submitted:true,answers:{...complete('B').answers,study_arm:'C'}};
 const storage={getItem:key=>key==='diana-survey:diana-v6'?JSON.stringify(completed):null};
 assert.deepEqual(loadSurveyState(storage),completed);
});
