import test from 'node:test';
import assert from 'node:assert/strict';
import {createSurveyAutosave,draftPayload} from './survey-autosave.js';
import {newSurveyState,reviseSurvey,markWaitingFields,finishWaitingIfReady,remainingWaitingGroups,waitingQuestionGroups,nextSurveyState,displaySurveyGroup,saveSurveyState,loadSurveyState,restoreServerDraft} from './survey.js';
const response=revision=>new Response(JSON.stringify({saved:true,completed:false,revision}),{status:200});
const state=(revision,answers={})=>({...newSurveyState(),draftRevision:revision,answers:{...newSurveyState().answers,study_arm:'B',...answers}});

test('autosave sends questionnaire values only, preserving partial text and explicit clearing',()=>{
 const source=state(1,{search_goal:'P',gender:'',chat_used:'no',chat_helpfulness:9,profile:{cv:'PRIVATE'}});
 const payload=draftPayload(source);
 assert.equal(payload.answers.search_goal,'P');assert.equal(payload.answers.gender,null);
 assert.equal(payload.answers.chat_helpfulness,9);assert.equal(payload.answers.profile,undefined);
 assert.equal(payload.runId,undefined);
});

test('serialized autosave includes answers entered during an active request without out-of-order writes',async()=>{
 const calls=[];let release;let active=0,maxActive=0;
 const saver=createSurveyAutosave({request:async(_,options)=>{
  active++;maxActive=Math.max(maxActive,active);const payload=JSON.parse(options.body);calls.push(payload);
  if(payload.revision===1)await new Promise(resolve=>release=resolve);
  active--;return response(payload.revision);
 }});
 saver.enqueue(state(1,{age_group:'21_24'}));const saving=saver.flush();
 saver.enqueue(state(2,{age_group:'21_24',gender:'not_specified'}));
 saver.enqueue(state(3,{age_group:'21_24',gender:'not_specified',education:'master'}));
 release();await saving;
 assert.deepEqual(calls.map(x=>x.revision),[1,3]);assert.equal(maxActive,1);
 assert.equal(calls[1].answers.gender,'not_specified');assert.equal(calls[1].answers.education,'master');
 await saver.flush();assert.equal(calls.length,2);
});

test('lost confirmation retries the identical payload and never reports success before acknowledgement',async()=>{
 let attempts=0;const payloads=[],statuses=[];
 const saver=createSurveyAutosave({onStatus:status=>statuses.push(status),request:async(_,options)=>{
  payloads.push(options.body);if(++attempts===1)throw new TypeError('Offline');return response(4);
 }});
 saver.enqueue(state(4,{search_goal:'Data Science'}));await assert.rejects(saver.flush());
 assert.equal(statuses.at(-1),'error');assert.ok(!statuses.includes('saved'));
 await saver.flush();assert.equal(payloads[0],payloads[1]);assert.equal(statuses.at(-1),'saved');
});

test('missing confirmation and mismatched revision do not count as a saved answer',async()=>{
 for(const data of [{},{saved:true,revision:9}]){
  const saver=createSurveyAutosave({request:async()=>new Response(JSON.stringify(data))});saver.enqueue(state(1));
  await assert.rejects(saver.flush(),/bestätigung/i);
 }
});

test('waiting answers skip demographics and search goal and only leave unasked personality questions',()=>{
 let source=state(1,{age_group:'21_24',gender:'not_specified',education:'master',study_field:'',search_goal:'Werkstudent',personality_customized:'yes',personality_setup:8});
 source={...source,systemCompleted:true,chatCompleted:true};
 source=markWaitingFields(source,waitingQuestionGroups[0].fields);
 source=finishWaitingIfReady(source);
 assert.equal(remainingWaitingGroups(source).length,0);
 const next=nextSurveyState(source);assert.equal(next.stage,'overall');
 assert.deepEqual(displaySurveyGroup(next,'personality').fields.map(f=>f.name),['personality_clarity_search','personality_clarity_chat','personality_consistency','personalized_chat_usefulness','personalized_search_usefulness']);
 const memory=new Map();const storage={getItem:key=>memory.get(key)||null,setItem:(key,value)=>memory.set(key,value)};
 saveSurveyState(storage,source);assert.deepEqual(loadSurveyState(storage).waitingAnswered,source.waitingAnswered);
 assert.equal(nextSurveyState(loadSurveyState(storage)).stage,'overall');
});

test('partly answered waiting blocks retain unanswered and optional questions; invalid fields are never skipped',()=>{
 let source=state(1,{age_group:'21_24'});
 source=markWaitingFields(source,waitingQuestionGroups[0].fields.filter(f=>f.name==='age_group'));
 assert.deepEqual(remainingWaitingGroups(source)[0].fields.map(f=>f.name),['gender','education','study_field']);
 source=markWaitingFields(source,waitingQuestionGroups[1].fields);
 assert.equal(source.waitingAnswered.includes('search_goal'),false);
 assert.equal(remainingWaitingGroups(source).length,2);
 const changed={...source,answers:{...source.answers,age_group:''}};
 assert.equal(remainingWaitingGroups(changed)[0].fields[0].name,'age_group');
});

test('revisions remain monotonic even when the clock does not advance',()=>{
 const initial=state(Date.now()+100000);const next=reviseSurvey(initial,{});assert.equal(next.draftRevision,initial.draftRevision+1);
});


test('v4 migration starts a fresh experiment and never reuses historical outcome ratings',()=>{
 const old={...state(20,{search_goal:'Data Science',personality_setup:'4',score_usefulness:7,personality_customized:'yes'}),version:'diana-v4',waitingAnswered:['personality_setup','personality_customized']};
 const storage={getItem:key=>key==='diana-survey:diana-v4'?JSON.stringify(old):null};
 const next=loadSurveyState(storage);
 assert.equal(next.version,'diana-v7');assert.equal(next.answers.personality_setup,null);
 assert.equal(next.answers.score_usefulness,null);assert.equal(next.answers.personality_customized,null);
 assert.ok(!next.waitingAnswered.includes('personality_setup'));assert.ok(next.draftRevision>20);
 const restored=restoreServerDraft(next,{version:'diana-v4',revision:next.draftRevision+100,answers:old.answers,waiting_answered:old.waitingAnswered});
 assert.equal(restored.answers.personality_setup,null);assert.equal(restored.draftRevision,next.draftRevision+101);
 assert.deepEqual(restoreServerDraft(next,{completed:true}).submitted,true);
});


test('server v6 drafts carry facts into v7 without carrying the old group or outcome ratings',()=>{
 const current=state(1,{study_arm:'A'});
 const restored=restoreServerDraft(current,{version:'diana-v6',revision:100,answers:{study_arm:'C',age_group:'21_24',search_goal:'Werkstudent',score_usefulness:8,personality_setup:9},waiting_answered:['age_group','personality_setup']});
 assert.equal(restored.version,'diana-v7');assert.equal(restored.answers.study_arm,'A');
 assert.equal(restored.answers.age_group,'21_24');assert.equal(restored.answers.search_goal,'Werkstudent');
 assert.equal(restored.answers.score_usefulness,null);assert.equal(restored.answers.personality_setup,null);
 assert.deepEqual(restored.waitingAnswered,['age_group']);assert.equal(restored.draftRevision,101);
});
