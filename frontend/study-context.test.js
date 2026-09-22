import assert from 'node:assert/strict';
import test from 'node:test';
import {readFileSync} from 'node:fs';
import {installStudyViewportCapture, STUDY_MOBILE_QUERY, studyContextPayload, localDateTime} from './study-context.js';

const tick = () => new Promise(resolve=>setTimeout(resolve,0));
function hostFixture(matches) {
  const listeners = new Map();
  const media = {matches, addEventListener(name,listener){listeners.set(name,listener);},removeEventListener(name){listeners.delete(name);}};
  const host = {matchMedia(query){assert.equal(query,STUDY_MOBILE_QUERY);return media;},addEventListener(name,listener){listeners.set(name,listener);},removeEventListener(name){listeners.delete(name);}};
  return {host,media,listeners};
}

test('viewport capture follows the actual mobile layout and sends only a coarse class after enrollment', async()=>{
  const css=readFileSync(new URL('./mobile.css',import.meta.url),'utf8');
  assert.match(css,/@media\(max-width:850px\)/);
  assert.equal(STUDY_MOBILE_QUERY,'(max-width: 850px)');
  const {host,media,listeners}=hostFixture(true), requests=[];
  const cleanup=installStudyViewportCapture(host,async(url,options)=>{requests.push([url,JSON.parse(options.body)]);return {ok:true};});
  await tick();
  assert.deepEqual(requests,[['/api/study-context',{viewport_class:'mobile'}]]);
  listeners.get('change')();await tick();assert.equal(requests.length,1);
  media.matches=false;listeners.get('change')();await tick();
  assert.deepEqual(requests[1][1],{viewport_class:'desktop'});
  cleanup();assert.equal(listeners.size,0);
});

test('failed capture retries when online and in-flight resize saves latest layout once', async()=>{
  const {host,media,listeners}=hostFixture(false), requests=[];
  let finish;
  const cleanup=installStudyViewportCapture(host,async(_url,options)=>{
    requests.push(JSON.parse(options.body));
    if(requests.length===1)return {ok:false};
    if(requests.length===2)return await new Promise(resolve=>{finish=resolve;});
    return {ok:true};
  });
  await tick();listeners.get('online')();await tick();
  media.matches=true;listeners.get('change')();finish({ok:true});await tick();
  assert.deepEqual(requests,[{viewport_class:'desktop'},{viewport_class:'desktop'},{viewport_class:'mobile'}]);
  cleanup();
});

test('cohort changes keep optimistic revision and normalize batch timestamps to UTC',()=>{
  assert.deepEqual(studyContextPayload({study_wave:'pretest',recruitment_batch:'',revision:4}),{study_wave:'pretest',recruitment_batch:null,revision:4});
  assert.deepEqual(studyContextPayload({study_wave:'main',recruitment_batch:'2026-09-22T14:00:00+02:00',revision:4}),{study_wave:'main',recruitment_batch:'2026-09-22T12:00:00.000Z',revision:4});
  assert.throws(()=>studyContextPayload({study_wave:'other',recruitment_batch:'',revision:4}));
  assert.throws(()=>studyContextPayload({study_wave:'main',recruitment_batch:'nonsense',revision:4}));
  assert.equal(localDateTime(null),'');
});
