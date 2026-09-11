import test from 'node:test';
import assert from 'node:assert/strict';
import { hasSearchResults, isSurveyResultsView, isSurveyCompletion, reportSurveyProgress, requestSurveyProgress, searchGoalSuggestion, readSurveySearchContext } from './survey-progress.js';

const runId = 'a'.repeat(32);
const origin = 'http://127.0.0.1:5050';

test('search suggestion uses only relevant profile fields and never the CV or conversation', () => {
  const text = searchGoalSuggestion({ query: 'Data Science', skills: ['Python'], preferences: ['Teamarbeit'],
    cv_text: 'PRIVATE CV', messages: ['PRIVATE CHAT'], filters: { employment_types: ['werkstudent'], locations: ['Nürnberg'], max_hours: 20 } });
  assert.match(text, /Data Science/); assert.match(text, /Werkstudent/); assert.match(text, /Nürnberg/);
  assert.ok(!text.includes('PRIVATE'));
  assert.equal(searchGoalSuggestion({query: 'x'.repeat(3000)}).length, 1000);
  assert.equal(searchGoalSuggestion(null), '');
});

test('search context is replayed for the current parent but never counts as completion', () => {
  const host = embeddedWindow();
  reportSurveyProgress(host, false, {searching: true, searchGoal: 'Python Werkstudent'});
  const data = host.posted[0].data;
  const frame = {};
  const event = {data, source: frame, origin};
  assert.deepEqual(readSurveySearchContext(event, frame, origin, runId), {searching:true, resultsVisible:false, searchGoal:'Python Werkstudent'});
  assert.equal(isSurveyCompletion(event, frame, origin, runId), false);
  for (const bad of [{...event,source:{}}, {...event,origin:'http://elsewhere.test'},
    {...event,data:{...data,runId:'b'.repeat(32)}}, {...event,data:{...data,searching:'true'}},
    {...event,data:{...data,searchGoal:'x'.repeat(1001)}}]) assert.equal(readSurveySearchContext(bad, frame, origin, runId), null);
  host.posted.length=0;
  host.receive({type:'diana:survey-progress-request',runId});
  assert.equal(host.posted.length,1);
  assert.deepEqual(Object.keys(data).sort(), ['type','runId','searching','searchGoal','resultsVisible'].sort());
});

test('follow-up visibility follows the current view, including waiting and editing after a completed search', () => {
  const view = {session:{session_id:'s'.repeat(32),jobs:[]},page:'search',booting:false,busy:false,editor:null,personalityIntro:null};
  assert.equal(isSurveyResultsView(view),true);
  for (const change of [{session:null},{page:'about'},{booting:true},{busy:true},{editor:'profile'},{editor:'advisor'},{personalityIntro:'help'}]) {
    assert.equal(isSurveyResultsView({...view,...change}),false);
  }
  const host=embeddedWindow();
  const frame={};
  for (const resultsVisible of [true,false,true]) {
    const cleanup=reportSurveyProgress(host,true,{searching:false,searchGoal:'',resultsVisible});
    host.posted.length=0;
    host.receive({type:'diana:survey-progress-request',runId});
    const data=host.posted.find(item=>item.data.type==='diana:survey-search-context').data;
    assert.equal(readSurveySearchContext({data,source:frame,origin},frame,origin,runId).resultsVisible,resultsVisible);
    cleanup();
  }
});
function embeddedWindow() {
  const listeners = new Set();
  const posted = [];
  const parent = { postMessage: (data, targetOrigin) => posted.push({ data, targetOrigin }) };
  return { parent, posted, listeners, location: { search: `?embed=survey&run=${runId}`, origin },
    addEventListener(type, listener) { assert.equal(type, 'message'); listeners.add(listener); },
    removeEventListener(type, listener) { assert.equal(type, 'message'); listeners.delete(listener); },
    receive(data, source = parent, eventOrigin = origin) { for (const listener of listeners) listener({ data, source, origin: eventOrigin }); },
  };
}

test('catalog, streamed previews and failed searches do not count as completed step 3', () => {
  for (const value of [null, undefined, {}, { jobs: [] }, { type: 'assistant_text', text: 'Suche läuft.' }, { error: 'Failed' }, { session_id: 'short', jobs: [] }]) {
    assert.equal(hasSearchResults(value), false);
  }
  // A completed search with zero jobs or hidden low scores still finishes step 3.
  assert.equal(hasSearchResults({ session_id: 's'.repeat(32), jobs: [] }), true);
  assert.equal(hasSearchResults({ session_id: 's'.repeat(32), jobs: [{ match: { score: 10 } }] }), true);
});

test('pending searches never announce completion, even when the parent requests status', () => {
  const host = embeddedWindow();
  const cleanup = reportSurveyProgress(host, false);
  requestSurveyProgress({ postMessage: data => host.receive(data) }, origin, runId);
  assert.deepEqual(host.posted, []);
  cleanup();
  assert.equal(host.listeners.size, 0);
});

test('completed and restored searches announce only the step and survey run', () => {
  const host = embeddedWindow();
  reportSurveyProgress(host, true);
  assert.deepEqual(host.posted, [{ data: { type: 'diana:survey-search-completed', runId, completedStep: 3 }, targetOrigin: origin }]);
});

test('a load handshake recovers completion when the first message preceded the parent listener', () => {
  const host = embeddedWindow();
  reportSurveyProgress(host, true);
  host.posted.length = 0;
  requestSurveyProgress({ postMessage(data, targetOrigin) { assert.equal(targetOrigin, origin); host.receive(data); } }, origin, runId);
  assert.equal(host.posted.length, 1);
  const iframeWindow = {};
  assert.equal(isSurveyCompletion({ data: host.posted[0].data, source: iframeWindow, origin }, iframeWindow, origin, runId), true);
});

test('only the current iframe, origin, run and completed step unlock the questionnaire', () => {
  const iframeWindow = {};
  const data = { type: 'diana:survey-search-completed', runId, completedStep: 3 };
  const event = { data, source: iframeWindow, origin };
  for (const invalid of [
    { ...event, source: {} }, { ...event, origin: 'http://elsewhere.test' },
    { ...event, data: { ...data, runId: 'b'.repeat(32) } },
    { ...event, data: { ...data, completedStep: 2 } },
    { ...event, data: { ...data, completedStep: '3' } },
    { ...event, data: { ...data, type: 'diana:survey-progress-request' } },
    { ...event, data: null },
  ]) assert.equal(isSurveyCompletion(invalid, iframeWindow, origin, runId), false);
  assert.equal(isSurveyCompletion(event, null, origin, runId), false);
});

test('the reporter ignores requests from unrelated windows and removes its listener', () => {
  const host = embeddedWindow();
  const cleanup = reportSurveyProgress(host, true);
  host.posted.length = 0;
  const request = { type: 'diana:survey-progress-request', runId };
  host.receive(request, {});
  host.receive(request, host.parent, 'http://elsewhere.test');
  host.receive({ ...request, runId: 'b'.repeat(32) });
  host.receive({ ...request, type: 'other' });
  assert.deepEqual(host.posted, []);
  cleanup();
  host.receive(request);
  assert.deepEqual(host.posted, []);
});

test('the standalone jobs page never communicates survey progress', () => {
  const host = embeddedWindow();
  host.parent = host;
  reportSurveyProgress(host, true)();
  assert.equal(host.listeners.size, 0);
  assert.deepEqual(host.posted, []);
  const noSurvey = embeddedWindow();
  noSurvey.location.search = '';
  reportSurveyProgress(noSurvey, true)();
  assert.equal(noSurvey.listeners.size, 0);
  assert.deepEqual(noSurvey.posted, []);
});

test('only a committed nonempty user message counts; greeting, draft and preview do not', async () => {
  const {hasChatMessage}=await import('./survey-progress.js');
  const session={session_id:'s'.repeat(32),jobs:[]};
  for(const messages of [undefined,[],[{role:'assistant',content:'Hallo'}],[{role:'user',content:'   '}],[{role:'user',content:null}]]) {
    assert.equal(hasChatMessage({...session,messages}),false);
  }
  assert.equal(hasChatMessage({messages:[{role:'user',content:'Meine Frage'}]}),false);
  assert.equal(hasChatMessage({...session,messages:[{role:'user',content:'Meine Frage'}]}),true);
});

test('chat completion is replayed without content and only accepted from the active frame', async () => {
  const {isSurveyChatCompletion}=await import('./survey-progress.js');
  const host=embeddedWindow();
  reportSurveyProgress(host,true,{chatCompleted:true});
  const data=host.posted.find(item=>item.data.type==='diana:survey-chat-completed').data;
  assert.deepEqual(data,{type:'diana:survey-chat-completed',runId});
  host.posted.length=0;host.receive({type:'diana:survey-progress-request',runId});
  assert.ok(host.posted.some(item=>item.data.type==='diana:survey-chat-completed'));
  const frame={};const event={data,source:frame,origin};
  assert.equal(isSurveyChatCompletion(event,frame,origin,runId),true);
  for(const bad of [{...event,source:{}},{...event,origin:'https://other.test'},
    {...event,data:{...data,runId:'b'.repeat(32)}},{...event,data:{...data,type:'diana:survey-search-completed'}},
    {...event,data:null}])assert.equal(isSurveyChatCompletion(bad,frame,origin,runId),false);
});

test('open-chat request is scoped to the parent and current run', async () => {
  const {requestSurveyChat}=await import('./survey-progress.js');
  const host=embeddedWindow();let opened=0;
  const cleanup=reportSurveyProgress(host,true,{},()=>opened++);
  const data={type:'diana:survey-open-chat',runId};
  host.receive(data,{});host.receive(data,host.parent,'https://other.test');host.receive({...data,runId:'b'.repeat(32)});
  assert.equal(opened,0);
  requestSurveyChat({postMessage:(message,target)=>{assert.equal(target,origin);host.receive(message);}},origin,runId);
  assert.equal(opened,1);
  cleanup();host.receive(data);assert.equal(opened,1);
});
