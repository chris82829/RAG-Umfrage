import assert from 'node:assert/strict';
import test from 'node:test';
import { chatAllowance } from './chat-limit.js';
import { canSendChat } from './chat-actions.js';
import { hasChatMessage } from './survey-progress.js';
import { readOperationResponse } from './search-request.js';

const saved = used => ({
  session_id: 'q'.repeat(40), jobs: [],
  messages: [ { role: 'assistant', content: 'Hallo!' },
    ...Array.from({ length: used }, () => ({ role: 'user', content: 'Warum passt diese Stelle?' })) ],
  candidate_pool: { available: true, count: 20 },
});

test('survey sends at most three messages; assistant text and empty drafts do not consume slots', () => {
  for (let used = 0; used <= 4; used++) {
    const session = saved(used);
    session.messages.push({role: 'assistant', content: 'Eine Antwort.'}, {role: 'user', content: '  '});
    assert.equal(chatAllowance(session).used, used);
    assert.equal(chatAllowance(session).remaining, Math.max(0, 3 - used));
    assert.equal(canSendChat('auto', 'Eine Frage', session), used < 3);
    assert.equal(canSendChat('auto', ' ', session), false);
  }
});

test('server participation counts survive a new search with an empty chat history', () => {
  const session = {...saved(0), chat_usage: {limit:3, used:3, pending:0, remaining:0}};
  assert.equal(chatAllowance(session).exhausted, true);
  assert.equal(canSendChat('auto', 'Noch eine Frage', session), false);
  assert.equal(hasChatMessage(session), true);
  assert.equal(hasChatMessage(saved(0)), false);
  assert.equal(hasChatMessage({...session, session_id: 'invalid'}), false);
});

test('pending messages in other tabs reserve quota without counting as completed chats', () => {
  const session = {...saved(1), chat_usage: {limit:3, used:1, pending:2, remaining:0}};
  assert.deepEqual(chatAllowance(session), {limit:3, used:1, pending:2, remaining:0, blocked:true, exhausted:false});
  assert.equal(canSendChat('auto', 'Noch eine Frage', session), false);
  const failed = {...session, chat_usage: {limit:3, used:1, pending:1, remaining:1}};
  assert.equal(canSendChat('auto', 'Erneut versuchen', failed), true);
});

test('test pages remain unlimited beyond three messages', () => {
  for (const used of [0, 3, 4, 50]) {
    const session = {...saved(used), chat_usage: {limit:null, used, pending:0, remaining:null}};
    assert.equal(chatAllowance(session, {testPage:true}).limit, null);
    assert.equal(chatAllowance(session, {testPage:true}).blocked, false);
    assert.equal(canSendChat('auto', 'Noch eine Frage', session, {testPage:true}), true);
  }
});

test('mode changes do not bypass a message limit; actions without a message remain available', () => {
  const session = saved(3);
  for (const mode of ['auto','search','rerank']) assert.equal(canSendChat(mode, 'Neue Frage', session), false);
  assert.equal(canSendChat('search', '', session), true);
  assert.equal(canSendChat('rerank', '', session), true);
  assert.equal(canSendChat('auto', 'Hallo', null), false);
});

test('missing quota metadata falls back to history without resetting the visible count', () => {
  for (const usage of [undefined, {used:0,remaining:3}, {used:'3',remaining:null}, {limit:null,used:3,remaining:null}]) {
    assert.equal(chatAllowance({...saved(3), chat_usage:usage}).blocked, true);
  }
});

test('quota rejections retain authoritative usage for both JSON and streaming responses', async () => {
  const usage = {limit:3, used:3, pending:0, remaining:0};
  const error = {code:'chat_message_limit', message:'Drei Nachrichten genutzt.', chat_usage:usage};
  for (const response of [
    new Response(JSON.stringify({error}), {status:409,headers:{'content-type':'application/json'}}),
    new Response(JSON.stringify({type:'error',status:409,error})+'\n', {headers:{'content-type':'application/x-ndjson'}}),
  ]) {
    await assert.rejects(readOperationResponse(response), caught => {
      assert.equal(caught.code, 'chat_message_limit');
      assert.equal(caught.status, 409);
      assert.deepEqual(caught.chatUsage, usage);
      return true;
    });
  }
});
