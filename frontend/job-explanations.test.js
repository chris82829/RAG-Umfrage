import test from 'node:test';
import assert from 'node:assert/strict';
import {hasJobExplanation, requireExplanationSession, revealedAfterExplanation} from './job-explanations.js';
import {resultVisibilityKey} from './result-visibility.js';

const previous={session_id:'session-a',advisor:{name:'Berufsberater'},chat_usage:{used:2},
  jobs:Array.from({length:20},(_,index)=>({id:String(index),match:{score:90-index,reasons:[],reason:'',matched_skills:[]}}))};
const explained=structuredClone(previous);
explained.jobs[12].match.reasons=['Deine Python-Kenntnisse passen zu den genannten Aufgaben.'];

test('scores alone do not count as generated explanations',()=>{
  assert.equal(hasJobExplanation(previous.jobs[12].match),false);
  assert.equal(hasJobExplanation({...previous.jobs[12].match,reasons:[' ']}),false);
  assert.equal(hasJobExplanation(explained.jobs[12].match),true);
  assert.equal(hasJobExplanation({reason:'Vorhandene Begründung'}),true);
  assert.equal(hasJobExplanation({matched_skills:['Python']}),true);
  assert.equal(hasJobExplanation(null),false);
});

test('explanation responses must belong to the requested session',()=>{
  assert.equal(requireExplanationSession(explained,'session-a'),explained);
  assert.throws(()=>requireExplanationSession(explained,'session-b'));
  assert.throws(()=>requireExplanationSession({session_id:'session-a'},'session-a'));
  assert.throws(()=>requireExplanationSession(null,'session-a'));
});

test('on-demand explanations keep all twenty already-revealed results visible',()=>{
  const revealed=resultVisibilityKey(previous);
  assert.notEqual(revealed,resultVisibilityKey(explained));
  assert.equal(revealedAfterExplanation(previous,explained,revealed),resultVisibilityKey(explained));
  assert.deepEqual(explained.jobs.map(job=>[job.id,job.match.score]),previous.jobs.map(job=>[job.id,job.match.score]));
  assert.deepEqual(explained.chat_usage,previous.chat_usage);
});

test('loading an explanation does not expand a collapsed list',()=>{
  assert.equal(revealedAfterExplanation(previous,explained,null),null);
});

test('changed ranking, scores or session cannot carry stale expansion into fresh results',()=>{
  const revealed=resultVisibilityKey(previous);
  for(const next of [
    {...explained,session_id:'session-b'},
    {...explained,jobs:[...explained.jobs].reverse()},
    {...explained,jobs:explained.jobs.slice(0,10)},
    {...explained,jobs:explained.jobs.map((job,index)=>index===0?{...job,match:{...job.match,score:1}}:job)},
  ]){
    assert.notEqual(revealedAfterExplanation(previous,next,revealed),resultVisibilityKey(next));
  }
  assert.equal(revealedAfterExplanation(null,null,null),null);
});
