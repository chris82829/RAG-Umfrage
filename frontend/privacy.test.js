import test from 'node:test';
import assert from 'node:assert/strict';
import {consentHeaders,consentToken,rememberConsent,clearParticipation,CONSENT_KEY,privacyRequest} from './privacy.js';

function storage(){const data={};return new Proxy(data,{get(target,key){if(key==='getItem')return name=>target[name]??null;if(key==='setItem')return(name,value)=>{target[name]=value};if(key==='removeItem')return name=>{delete target[name]};return target[key]}})}
test('consent is carried in a header, and withdrawal clears only DIANA participation state',()=>{
 const original=globalThis.window;
 try {
  const host={sessionStorage:storage(),localStorage:storage()};globalThis.window=host;
  rememberConsent('a'.repeat(64));
  assert.deepEqual(consentHeaders(),{'X-Diana-Consent':'a'.repeat(64)});
  for(const key of ['diana-survey:diana-v3','diana-survey-chat:abc','other-tool'])host.sessionStorage.setItem(key,'value');
  host.localStorage.setItem('jobkompass-session-v1','old');host.localStorage.setItem('other-tool','keep');
  clearParticipation(host);
  assert.equal(consentToken(),'');assert.deepEqual(consentHeaders(),{});
  assert.equal(host.sessionStorage.getItem(CONSENT_KEY),null);
  assert.equal(host.sessionStorage.getItem('diana-survey:diana-v3'),null);
  assert.equal(host.sessionStorage.getItem('diana-survey-chat:abc'),null);
  assert.equal(host.sessionStorage.getItem('other-tool'),'value');
  assert.equal(host.localStorage.getItem('other-tool'),'keep');
 }finally{globalThis.window=original;rememberConsent('');}
});
test('failed privacy requests cannot be interpreted as active consent or withdrawal',async()=>{
 const original=globalThis.fetch;
 try {
  globalThis.fetch=async()=>new Response(JSON.stringify({error:{message:'Einwilligung fehlt'}}),{status:428});
  await assert.rejects(privacyRequest('/consent',{method:'DELETE'}),/Einwilligung fehlt/);
 }finally{globalThis.fetch=original;}
});
