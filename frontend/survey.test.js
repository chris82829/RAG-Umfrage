import assert from 'node:assert/strict';
import test from 'node:test';
import {
  SURVEY_VERSION, SURVEY_STORAGE_KEY, applyStudyAssignment, changeSurveyAnswer, emptyAnswers,
  loadSurveyState, hasRequiredStudyChat, nextSurveyState, needsSystemPreparation, newSurveyState,
  remainingWaitingGroups, restoreServerDraft, saveSurveyState, startPreparedSystem, surveyConfiguration,
  surveyErrors, visibleFields, markWaitingFields, submitSurvey,
} from './survey.js';
import {createSurveyAutosave, draftPayload} from './survey-autosave.js';

const assigned = (arm = 'C', extra = {}) => applyStudyAssignment(newSurveyState(), {
  arm, questionnaire_version: SURVEY_VERSION, ...extra,
});
const names = fields => fields.map(field => field.name);
const prepare = state => startPreparedSystem({...state, answers:{...state.answers,
  previous_participation:'no',education:'bachelor',study_field:'',job_portal_experience:'weekly',ai_chat_experience:'daily',
}});
const memoryStorage = entries => {
  const values = new Map(entries);
  return {get length(){return values.size;},key:index=>[...values.keys()][index],getItem:key=>values.get(key)??null,
    removeItem:key=>values.delete(key),setItem:(key,value)=>values.set(key,value)};
};
const retired = ['age_group','gender','system_usefulness','usefulness_effective','usefulness_speed',
  'usefulness_overall','search_effort','personalized_search_usefulness','personality_clarity_search',
  'personality_clarity_explanations','template_selection_ease','personality_setup'];

test('V14 is the only active questionnaire and has the required arm-specific counts', () => {
  assert.equal(SURVEY_VERSION, 'diana-v14');
  for(const [arm,count] of [['A',26],['B',26],['C',26]]) {
    const state=assigned(arm), config=surveyConfiguration(state);
    assert.equal(state.version,SURVEY_VERSION);
    assert.equal(visibleFields(config.surveyFields,state.answers).filter(field=>!field.systemProvided).length,count);
    assert(!config.surveyFields.some(field=>retired.includes(field.name)));
    assert.equal(visibleFields(config.surveyFields,state.answers).some(field=>field.name==='personality_customized'),false);
    assert.equal(needsSystemPreparation(state),true);
  }
  for(const version of ['diana-v4','diana-v11','diana-v12','diana-v13','diana-v99']) {
    assert.throws(()=>surveyConfiguration(version),/Fragebogenversion ist nicht verfügbar/);
    assert.throws(()=>assigned('A',{questionnaire_version:version}),/Fragebogenversion ist nicht verfügbar/);
  }
  assert.throws(()=>assigned('A',{questionnaire_version:undefined}),/Fragebogenversion ist nicht verfügbar/);
});

test('four background answers precede use; only search context can be answered while waiting', () => {
  const state=assigned('B'), config=surveyConfiguration(state);
  assert.deepEqual(names(config.beforeSystemFields),['education','study_field','job_portal_experience','ai_chat_experience']);
  assert.equal(startPreparedSystem(state),state);
  const started=prepare(state);
  assert.equal(started.systemTaskStarted,true);
  assert.equal(needsSystemPreparation(started),false);
  assert.equal(started.answers.study_field,'');
  assert.deepEqual(remainingWaitingGroups(started).flatMap(group=>names(group.fields)),['search_goal']);
  assert.equal(needsSystemPreparation({...started,systemTaskStarted:false}),false);
});

test('browser restore removes retired keys and never migrates old answers into V14', () => {
  const old={...newSurveyState(),version:'diana-v12',submitted:true,answers:{system_usefulness:10,education:'master'}};
  const storage=memoryStorage([['diana-survey:diana-v12',JSON.stringify(old)],['unrelated','keep']]);
  const state=loadSurveyState(storage);
  assert.equal(state.version,SURVEY_VERSION);
  assert.notEqual(state.submissionId,old.submissionId);
  assert.equal(state.answers.education,'');
  assert.equal(state.submitted,false);
  assert.equal(storage.getItem('diana-survey:diana-v12'),null);
  assert.equal(storage.getItem('unrelated'),'keep');
  storage.setItem(SURVEY_STORAGE_KEY,JSON.stringify(old));
  assert.notEqual(loadSurveyState(storage).submissionId,old.submissionId);
  storage.removeItem(SURVEY_STORAGE_KEY);
  saveSurveyState(storage,old);
  assert.equal(storage.getItem(SURVEY_STORAGE_KEY),null);
});

test('V14 browser and server resume preserve preparation but sanitize unknown/hidden answers', () => {
  const initial=assigned('B'), prepared=prepare(initial);
  const storage=memoryStorage([]);
  saveSurveyState(storage,{...prepared,answers:{...prepared.answers,system_usefulness:10,personality_customized:'yes'}});
  const fromBrowser=loadSurveyState(storage);
  assert.equal(fromBrowser.submissionId,prepared.submissionId);
  assert.equal(needsSystemPreparation(fromBrowser),false);
  assert.equal(fromBrowser.answers.personality_customized,undefined);
  assert(!Object.hasOwn(fromBrowser.answers,'system_usefulness'));
  const fromServer=restoreServerDraft(initial,{version:SURVEY_VERSION,revision:prepared.draftRevision+1,
    answers:prepared.answers,waiting_answered:prepared.waitingAnswered});
  assert.equal(fromServer.answers.education,'bachelor');
  assert.equal(needsSystemPreparation(fromServer),false);
  const older=restoreServerDraft(fromServer,{version:SURVEY_VERSION,revision:1,answers:{education:'master'}});
  assert.equal(older,fromServer);
  assert.equal(restoreServerDraft(initial,{version:'diana-v12',completed:true}),initial);
  assert.equal(restoreServerDraft(initial,{completed:true}),initial);
  assert.equal(restoreServerDraft(initial,{version:SURVEY_VERSION,completed:true}).submitted,true);
});

test('all twenty rating items have seven full anchors and accept only 1–7 or explicit nonresponse', () => {
  const fields=surveyConfiguration().surveyFields.filter(field=>field.kind==='scale');
  assert.equal(fields.length,20);
  assert.equal(fields.filter(field=>field.framework==='DIANA').length,4);
  for(const field of fields) {
    assert.equal(field.presentation,'likert');
    assert.equal(field.scale.min,1);
    assert.equal(field.scale.max,7);
    assert.deepEqual(field.scale.labels,['Stimme überhaupt nicht zu','Stimme nicht zu','Stimme eher nicht zu',
      'Weder noch','Stimme eher zu','Stimme zu','Stimme voll und ganz zu']);
    for(const value of [1,2,3,4,5,6,7,'not_assessable'])assert.deepEqual(surveyErrors({[field.name]:value},[field]),{});
    for(const value of [0,8,10,null,'not_used',true,2.5])assert(field.name in surveyErrors({[field.name]:value},[field]));
  }
  const inherited={name:'temporary',kind:'scale'};
  assert.deepEqual(surveyErrors({temporary:7},[inherited]),{});
  assert('temporary' in surveyErrors({temporary:8},[inherited]));
});

test('retired customization question is absent for every group and waiting phase', () => {
  for (const arm of ['A','B','C']) {
    const config=surveyConfiguration(assigned(arm));
    assert(!config.surveyFields.some(field=>field.name==='personality_customized'));
    assert(!config.waitingQuestionFields.some(field=>field.name==='personality_customized'));
  }
});

test('navigation keeps the existing authoritative three-turn gate and skips answered waiting fields', () => {
  const initial={...prepare(assigned('A')),systemCompleted:true,chatCompleted:true,chatCount:99};
  for(const used of [0,1,2]) {
    const state=applyStudyAssignment(initial,{arm:'A',questionnaire_version:SURVEY_VERSION,chat_progress:{used,required:3,can_proceed:false}});
    assert.equal(state.chatCount,used);
    assert.equal(hasRequiredStudyChat(state),false);
    assert.equal(nextSurveyState(state),state);
  }
  const ready=applyStudyAssignment(initial,{arm:'A',questionnaire_version:SURVEY_VERSION,chat_progress:{used:3,required:3,can_proceed:true}});
  assert.equal(hasRequiredStudyChat(ready),true);
  const waitingFields=surveyConfiguration().waitingQuestionFields;
  const answered=markWaitingFields({...ready,answers:{...ready.answers,search_goal:'Softwareentwicklung als Werkstudent'}},waitingFields);
  assert.equal(nextSurveyState(answered).stage,'catalog_availability');
  assert.equal(hasRequiredStudyChat({...ready,chatCompleted:false}),false);
  assert.equal(hasRequiredStudyChat({...ready,chatCount:2}),false);
});

test('autosave sends only active answer fields and serializes new ratings after each revision', async () => {
  let state=prepare(assigned('A'));
  state={...state,answers:{...state.answers,usefulness_ideal:6,system_usefulness:10,source_item:'not an answer'}};
  const payload=draftPayload(state);
  assert.equal(payload.version,SURVEY_VERSION);
  assert.equal(payload.answers.usefulness_ideal,6);
  assert(!Object.hasOwn(payload.answers,'personality_customized'));
  assert(!Object.hasOwn(payload.answers,'system_usefulness'));
  assert(!Object.hasOwn(payload.answers,'source_item'));
  const saved=[];
  const autosave=createSurveyAutosave({request:async(_url,options)=>{
    const body=JSON.parse(options.body);saved.push(body);
    return {ok:true,json:async()=>({saved:true,revision:body.revision})};
  }});
  autosave.enqueue(state);await autosave.flush();
  state={...state,draftRevision:state.draftRevision+1,answers:{...state.answers,usefulness_find_easy:7}};
  autosave.enqueue(state);await autosave.flush();
  assert.equal(saved.length,2);
  assert.equal(saved[0].answers.usefulness_ideal,6);
  assert.equal(saved[1].answers.usefulness_find_easy,7);
});

test('complete V14 submission exports neither retired answers nor framework/source metadata', async () => {
  const state={...assigned('C'),systemCompleted:true,chatCompleted:true,chatCount:3};
  for(const field of surveyConfiguration().surveyFields) {
    if(field.systemProvided)continue;
    state.answers[field.name]=field.kind==='scale'?4:field.kind==='choice'?field.options[0][0]:field.optional?'':'Entwicklung mit Python';
  }
  state.answers.system_usefulness=10;
  state.answers.framework='not an answer';
  let sent;
  await submitSurvey(state,{request:async(_url,options)=>{
    sent=JSON.parse(options.body);return {ok:true,json:async()=>({saved:true})};
  }});
  assert.equal(sent.version,SURVEY_VERSION);
  assert(!Object.hasOwn(sent,'personality_customized'));
  assert.equal(sent.usefulness_ideal,4);
  assert(!Object.hasOwn(sent,'system_usefulness'));
  assert(!Object.hasOwn(sent,'framework'));
});

test('V14 removes repeat screening and retains trust and manipulation checks', async()=>{
  const {default:old}=await import('../survey_definition_v13.json',{with:{type:'json'}});
  const original=[old.demographics,...old.categories].flatMap(group=>group.fields);
  const current=surveyConfiguration().surveyFields;
  for(const field of original.filter(item=>item.name!=='personality_customized')) {
    const active=current.find(item=>item.name===field.name);
    assert.equal(active.kind,field.kind);
    assert.equal(active.construct,field.construct);
  }
  assert(current.every(field=>!field.title?.includes('DIANA')));
  assert.equal(current.find(field=>field.name==='intention_reuse').title,'So ein System werde ich bei einer weiteren Jobsuche wieder nutzen.');
  const sequence=names(current);
  assert(!sequence.includes('previous_participation'));
  assert(sequence.indexOf('trust_fit')>sequence.indexOf('usefulness_suggestions'));
  assert(sequence.indexOf('trust_credibility')<sequence.indexOf('dialogue_understanding'));
  assert(sequence.indexOf('perceived_character')>sequence.indexOf('dialogue_attentiveness'));
  assert(sequence.indexOf('perceived_character')<sequence.indexOf('control_preferences'));
  const state=assigned('A');
  for(const name of ['trust_fit','trust_credibility','perceived_character']) {
    const field=current.find(item=>item.name===name);
    assert.equal(fieldVisibleForTest(field,state.answers),true);
    assert(name in surveyErrors({...state.answers,[name]:null},[field]));
  }
});
function fieldVisibleForTest(field,answers){return visibleFields([field],answers).length===1;}
