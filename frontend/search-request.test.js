import assert from 'node:assert/strict';
import { test } from 'node:test';
import { readOperationResponse, requestOperation } from './search-request.js';

const encoder = new TextEncoder();

function streamResponse(chunks, status = 200) {
  return new Response(new ReadableStream({
    start(controller) {
      for (const chunk of chunks) controller.enqueue(typeof chunk === 'string' ? encoder.encode(chunk) : chunk);
      controller.close();
    },
  }), { status, headers: { 'Content-Type': 'application/x-ndjson; charset=utf-8' } });
}

function jsonResponse(data, status = 200) {
  return new Response(JSON.stringify(data), { status, headers: { 'Content-Type': 'application/json' } });
}

function line(event) {
  return `${JSON.stringify(event)}\n`;
}

function understandableError(error) {
  assert.ok(error instanceof Error);
  assert.ok(!(error instanceof SyntaxError), 'JSON parsing failures need a readable application error');
  assert.ok(error.message.trim().length > 5);
  return true;
}

test('NDJSON preserves UTF-8 and events when every byte arrives in a separate chunk', async () => {
  const data = { chat_action: 'search', jobs: [{ title: 'Werkstudent für München – Datenanalyse 🧪' }] };
  const encoded = encoder.encode(line({ type: 'phase', phase: 'search' }) + line({ type: 'result', data }));
  const chunks = Array.from(encoded, byte => Uint8Array.of(byte));
  const phases = [];
  assert.deepEqual(await readOperationResponse(streamResponse(chunks), phase => phases.push(phase)), data);
  assert.deepEqual(phases, ['search']);
});

test('only search phases are reported once and unrelated events are ignored', async () => {
  const phases = [];
  const data = { chat_action: 'search', jobs: [] };
  const events = [
    { type: 'phase', phase: 'answer' },
    { type: 'phase', phase: 'rerank' },
    { type: 'progress', phase: 'search' },
    { type: 'phase', phase: 'search' },
    { type: 'phase', phase: 'search' },
    { type: 'unknown', message: 'keepalive' },
    { type: 'result', data },
  ];
  assert.deepEqual(await readOperationResponse(streamResponse([events.map(line).join('')]),
    phase => phases.push(phase)), data);
  assert.deepEqual(phases, ['search']);
});

for (const action of ['answer', 'rerank']) {
  test(`${action} results work without announcing a search phase`, async () => {
    const data = { chat_action: action, assistant_message: 'Die bisherigen Stellen bleiben im Gespräch.' };
    const phases = [];
    const result = await readOperationResponse(streamResponse([line({ type: 'result', data })]),
      phase => phases.push(phase));
    assert.deepEqual(result, data);
    assert.deepEqual(phases, []);
  });
}

test('the search phase arrives before the result exists instead of waiting for the complete response',
  { timeout: 2000 }, async () => {
    let controller;
    const body = new ReadableStream({ start(value) { controller = value; } });
    const response = new Response(body, { headers: { 'Content-Type': 'application/x-ndjson' } });
    let phaseObserved;
    const phasePromise = new Promise(resolve => { phaseObserved = resolve; });
    let settled = false;
    const reading = readOperationResponse(response, phase => phaseObserved(phase));
    reading.then(() => { settled = true; }, () => { settled = true; });
    controller.enqueue(encoder.encode(line({ type: 'phase', phase: 'search' })));
    assert.equal(await phasePromise, 'search');
    assert.equal(settled, false);
    const data = { chat_action: 'search', jobs: [] };
    controller.enqueue(encoder.encode(line({ type: 'result', data })));
    controller.close();
    assert.deepEqual(await reading, data);
  });

test('a complete final result without a trailing newline is still parsed', async () => {
  const data = { chat_action: 'answer', assistant_message: 'Eine vollständige Antwort.' };
  const response = streamResponse(['\r\n', JSON.stringify({ type: 'result', data })]);
  assert.deepEqual(await readOperationResponse(response), data);
});

test('normal JSON responses remain supported without a phase event', async () => {
  const data = { session_id: 'session', chat_action: 'rerank', jobs: [] };
  const phases = [];
  assert.deepEqual(await readOperationResponse(jsonResponse(data), phase => phases.push(phase)), data);
  assert.deepEqual(phases, []);
});

test('EOF without a result is an error for both empty and phase-only streams', async () => {
  for (const chunks of [[], [line({ type: 'phase', phase: 'search' })]]) {
    await assert.rejects(readOperationResponse(streamResponse(chunks)), understandableError);
  }
});

test('malformed NDJSON and truncated result objects become readable errors', async () => {
  for (const malformed of ['not-json\n', '{"type":"result","data":', '{broken}\n']) {
    await assert.rejects(readOperationResponse(streamResponse([malformed])), understandableError);
  }
  await assert.rejects(readOperationResponse(new Response('{broken', {
    headers: { 'Content-Type': 'application/json' },
  })), understandableError);
});

for (const [status, message] of [
  [409, 'Der Chat wurde parallel geändert. Bitte neu laden.'],
  [503, 'Der Suchindex wird noch vorbereitet.'],
]) {
  test(`NDJSON error events preserve status ${status} and the server message`, async () => {
    const phases = [];
    const response = streamResponse([
      line({ type: 'phase', phase: 'search' }),
      line({ type: 'error', error: { message }, status }),
    ]);
    await assert.rejects(readOperationResponse(response, phase => phases.push(phase)), error => {
      assert.equal(error.status, status);
      assert.equal(error.message, message);
      return true;
    });
    assert.deepEqual(phases, ['search']);
  });

  test(`JSON HTTP errors preserve status ${status} and the server message`, async () => {
    await assert.rejects(readOperationResponse(jsonResponse({ error: { message } }, status)), error => {
      assert.equal(error.status, status);
      assert.equal(error.message, message);
      return true;
    });
  });
}

test('requestOperation posts one JSON request and forwards incremental phases', async t => {
  const body = { session_id: 'existing-session', message: 'Bitte weitere Jobs.', mode: 'auto' };
  const data = { chat_action: 'search', jobs: [] };
  const fetch = t.mock.method(globalThis, 'fetch', async () => streamResponse([
    line({ type: 'phase', phase: 'search' }), line({ type: 'result', data }),
  ]));
  const phases = [];
  assert.deepEqual(await requestOperation('/chat', body, phase => phases.push(phase)), data);
  assert.deepEqual(phases, ['search']);
  assert.equal(fetch.mock.callCount(), 1);
  const [url, options] = fetch.mock.calls[0].arguments;
  assert.equal(url, '/api/chat');
  assert.equal(options.method, 'POST');
  const headers = new Headers(options.headers);
  assert.ok(headers.get('Accept').includes('application/x-ndjson'));
  assert.ok(headers.get('Content-Type').includes('application/json'));
  assert.deepEqual(JSON.parse(options.body), body);
});

test('requestOperation does not retry a conflict or a failed network request', async t => {
  const fetch = t.mock.method(globalThis, 'fetch', async () => jsonResponse({
    error: { message: 'Der Chat wurde parallel geändert.' },
  }, 409));
  await assert.rejects(requestOperation('/chat', { session_id: 'session' }), error => error.status === 409);
  assert.equal(fetch.mock.callCount(), 1);
  fetch.mock.mockImplementation(async () => { throw new TypeError('Verbindung unterbrochen.'); });
  await assert.rejects(requestOperation('/chat', { session_id: 'session' }), Error);
  assert.equal(fetch.mock.callCount(), 2);
});

test('chat text is visible before the terminal result and stays separate from persisted messages',
  { timeout: 2000 }, async () => {
    let controller;
    const response = new Response(new ReadableStream({ start(value) { controller = value; } }),
      { headers: { 'Content-Type': 'application/x-ndjson' } });
    let sawText;
    const preview = new Promise(resolve => { sawText = resolve; });
    let settled = false;
    const reading = readOperationResponse(response, () => assert.fail('No search phase'), sawText);
    reading.then(() => { settled = true; }, () => { settled = true; });
    controller.enqueue(encoder.encode(line({ type: 'assistant_text', text: 'Python passt' })));
    assert.equal(await preview, 'Python passt');
    assert.equal(settled, false);
    const data = { chat_action: 'answer', messages: [{ role: 'assistant', content: 'Python passt zu deinen Kenntnissen.' }] };
    controller.enqueue(encoder.encode(line({ type: 'result', data })));
    controller.close();
    assert.deepEqual(await reading, data);
  });

test('text snapshots survive split unicode chunks and replace rather than duplicate partial words', async () => {
  const data = { chat_action: 'answer', assistant_message: 'Grüße 🧭' };
  const bytes = encoder.encode([
    { type: 'assistant_text', text: 'Grü' },
    { type: 'assistant_text', text: data.assistant_message },
    { type: 'result', data },
  ].map(line).join(''));
  const texts = [];
  assert.deepEqual(await readOperationResponse(streamResponse(Array.from(bytes, byte => Uint8Array.of(byte))),
    undefined, text => texts.push(text)), data);
  assert.deepEqual(texts, ['Grü', 'Grüße 🧭']);
});

test('partial chat text never substitutes for a final result after failure or disconnection', async () => {
  for (const ending of ['', line({ type: 'error', status: 503, error: { message: 'Verbindung unterbrochen.' } })]) {
    const texts = [];
    await assert.rejects(readOperationResponse(streamResponse([
      line({ type: 'assistant_text', text: 'Eine unvollständige' }), ending,
    ]), undefined, text => texts.push(text)), understandableError);
    assert.deepEqual(texts, ['Eine unvollständige']);
  }
});

test('invalid text snapshots are rejected and requestOperation forwards valid previews', async t => {
  for (const text of [null, {}, 42]) {
    await assert.rejects(readOperationResponse(streamResponse([line({ type: 'assistant_text', text })])), understandableError);
  }
  const data = { assistant_message: 'Eine Antwort.' };
  t.mock.method(globalThis, 'fetch', async () => streamResponse([
    line({ type: 'assistant_text', text: 'Eine' }), line({ type: 'result', data }),
  ]));
  const texts = [];
  assert.deepEqual(await requestOperation('/chat', { message: 'Warum?' }, undefined, text => texts.push(text)), data);
  assert.deepEqual(texts, ['Eine']);
});

test('long general-assistant answers stream past 1800 characters and finish across consecutive requests', async () => {
  for (const length of [1801, 12000]) {
    const answer = 'Eine ausführliche Antwort mit Umlauten: äöü. '.repeat(300).slice(0, length);
    const data = {chat_action:'answer', assistant_message:answer, messages:[{role:'assistant',content:answer}]};
    const previews = [answer.slice(0,1700),answer.slice(0,1801),answer];
    const texts = [];
    const response = streamResponse([
      ...previews.map(text=>line({type:'assistant_text',text})),
      line({type:'result',data}),
    ]);
    assert.deepEqual(await readOperationResponse(response,()=>assert.fail('No new search'),text=>texts.push(text)),data);
    assert.deepEqual(texts,previews);
  }
});
