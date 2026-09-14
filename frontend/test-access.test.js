import test from 'node:test';
import assert from 'node:assert/strict';
import {standaloneArm,leavesTestContext} from './test-access.js';
import {appSessionStorage,appPath} from './app-session.js';
import {consentToken,consentHeaders,rememberConsent,clearParticipation} from './privacy.js';

function storage() {return new Proxy({}, {get(t,k){if(k==='getItem')return n=>t[n]??null;if(k==='setItem')return(n,v)=>{t[n]=v};if(k==='removeItem')return n=>{delete t[n]};return t[k]}})}
test('only explicit test URLs select a fixed arm',()=>{
  assert.equal(standaloneArm('/test/a'),'A');assert.equal(standaloneArm('/test/c'),'C');assert.equal(standaloneArm('/test/c/datenschutz'),'C');assert.equal(standaloneArm('/test/b/datenschutz'),'B');
  for(const path of ['/suche','/umfrage','/test/d','/test/abc'])assert.equal(standaloneArm(path),null);
  assert.equal(appPath('search','', '/test/b'),'/test/b');
  assert.equal(leavesTestContext('about','/test/a'),true);
  assert.equal(leavesTestContext('about','/test/b'),true);
  assert.equal(leavesTestContext('search','/test/b'),false);
  assert.equal(leavesTestContext('about','/suche'),false);
});
test('test A, test B, test C and survey keep separate consent and chat state in the same browser',()=>{
  const previous=globalThis.window;
  const host={location:{pathname:'/suche',search:''},sessionStorage:storage(),localStorage:storage()};
  globalThis.window=host;
  try{
    rememberConsent('study');appSessionStorage(host).remember('study-chat');
    host.location.pathname='/test/a';rememberConsent('a');appSessionStorage(host).remember('chat-a');
    assert.deepEqual(consentHeaders(),{'X-Diana-Consent':'a','X-Diana-Test':'A'});
    host.location.pathname='/test/b';assert.equal(consentToken(),'');rememberConsent('b');appSessionStorage(host).remember('chat-b');
    host.location.pathname='/test/c';assert.equal(consentToken(),'');rememberConsent('c');appSessionStorage(host).remember('chat-c');
    assert.deepEqual(consentHeaders(),{'X-Diana-Consent':'c','X-Diana-Test':'C'});
    host.location.pathname='/test/a';assert.equal(appSessionStorage(host).read(),'chat-a');clearParticipation(host);
    assert.equal(consentToken(),'');assert.equal(appSessionStorage(host).read(),null);
    host.location.pathname='/test/b';assert.equal(consentToken(),'b');assert.equal(appSessionStorage(host).read(),'chat-b');clearParticipation(host);
    host.location.pathname='/test/c';assert.equal(consentToken(),'c');assert.equal(appSessionStorage(host).read(),'chat-c');clearParticipation(host);
    host.location.pathname='/suche';assert.equal(consentToken(),'study');assert.equal(appSessionStorage(host).read(),'study-chat');clearParticipation(host);
  }finally{globalThis.window=previous;}
});
