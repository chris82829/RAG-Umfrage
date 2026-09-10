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
test('B has the same common outcomes as C but no personality questions or hidden answers',()=>{
 const b=complete('B'),c=complete('C');
 assert.deepEqual(surveyErrors(b.answers),{});assert.deepEqual(surveyErrors(c.answers),{});
 assert.equal(displaySurveyGroup(b,'personality').fields.length,0);
 assert.equal(displaySurveyGroup(c,'personality').fields.length,7);
 assert.deepEqual(displaySurveyGroup(b,'overall').fields,displaySurveyGroup(c,'overall').fields);
 for(const f of surveyFields.filter(f=>f.visibleIf))assert.equal(draftPayload(b).answers[f.name],null);
 assert.equal(draftPayload(b).answers.study_arm,'B');
 const stages=[];let state=b;
 while(true){const next=nextSurveyState(state);if(next===state)break;state=next;stages.push(state.stage);}
 assert.ok(!stages.includes('personality'));assert.equal(stages.at(-1),'feedback');
});
test('B waiting questions consist of demographics and search goal; all can be completed and skipped later',()=>{
 let state=complete('B');
 assert.deepEqual(remainingWaitingGroups(state)[1].fields.map(f=>f.name),['search_goal']);
 state=finishWaitingIfReady(markWaitingFields(state,waitingQuestionGroups[0].fields));
 assert.equal(remainingWaitingGroups(state).length,0);
 assert.ok(!state.waitingAnswered.includes('study_arm'));
 assert.ok(!state.waitingAnswered.includes('personality_setup'));
 assert.equal(nextSurveyState(state).stage,'overall');
});
test('assignment survives questionnaire reload and cannot manufacture a completed chat',()=>{
 const state=applyStudyAssignment(newSurveyState(),{arm:'B'});const data=new Map();const storage={getItem:key=>data.get(key),setItem:(key,value)=>data.set(key,value)};
 saveSurveyState(storage,state);const restored=loadSurveyState(storage);
 assert.equal(restored.answers.study_arm,'B');assert.equal(restored.chatCompleted,false);
 assert.equal(nextSurveyState(restored),restored);
 assert.throws(()=>applyStudyAssignment(state,{arm:'A'}));
});
