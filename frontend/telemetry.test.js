import assert from 'node:assert/strict';
import test from 'node:test';
import {createDwellClock, hasVisibleStudySurface, observeJustification, sendStudyEvent} from './telemetry.js';

const headers = {'X-Diana-Consent': 'a'.repeat(64)};
const sessionId = 'b'.repeat(43);
const metadata = {job_id: '123', rank: 1};
const eventId = '00000000-0000-4000-8000-000000000000';

test('dwell counts only active intervals, flushes incrementally and stops once', () => {
  let time = 0;
  const observed = [];
  const clock = createDwellClock({now: () => time, onDuration: value => observed.push(value)});
  time = 1000; clock.update(false);
  time = 2000; clock.update(true);
  time = 2500; clock.update(true);
  time = 3100; clock.flush();
  time = 3600; clock.update(false);
  time = 16000; clock.flush();
  time = 17000; clock.update(true);
  time = 17900; clock.stop();
  clock.stop();
  assert.deepEqual(observed, [1100, 500, 900]);
});

test('long foreground intervals are split into bounded duration chunks', () => {
  let time = 0;
  const observed = [];
  const clock = createDwellClock({now: () => time, onDuration: value => observed.push(value)});
  clock.update(true); time = 130000; clock.stop();
  assert.deepEqual(observed, [60000, 60000, 10000]);
});

test('sender retries the same event ID once and strips arbitrary metadata', async () => {
  const calls = [];
  const ok = await sendStudyEvent(sessionId, 'job_expand', {...metadata, text: 'do not store'}, {
    headers, eventId, fetchImpl: async (...args) => {calls.push(args); return {ok: calls.length === 2, status: 503};},
  });
  assert.equal(ok, true);
  assert.equal(calls.length, 2);
  assert.equal(calls[0][1].body, calls[1][1].body);
  assert.deepEqual(JSON.parse(calls[0][1].body), {session_id: sessionId, event_id: eventId,
    event_type: 'job_expand', metadata});
  assert.equal(calls[0][1].keepalive, true);
});

test('client cannot send chat turns, absent consent, test telemetry or invalid metadata', async () => {
  let calls = 0;
  const fetchImpl = async () => {calls++; return {ok: true};};
  const options = {headers, eventId, fetchImpl};
  assert.equal(await sendStudyEvent(sessionId, 'chat_turn', metadata, options), false);
  assert.equal(await sendStudyEvent(sessionId, 'job_expand', metadata, {...options, headers: {}}), false);
  assert.equal(await sendStudyEvent(sessionId, 'job_expand', metadata, {...options,
    headers: {...headers, 'X-Diana-Test': 'A'}}), false);
  assert.equal(await sendStudyEvent(sessionId, 'job_detail', {...metadata, rank: 21}, options), false);
  assert.equal(await sendStudyEvent(sessionId, 'dwell_justification', {...metadata, duration_ms: 60001}, options), false);
  assert.equal(calls, 0);
});

test('consent and rate limit rejection are not retried', async () => {
  let calls = 0;
  assert.equal(await sendStudyEvent(sessionId, 'job_detail', metadata, {headers, eventId,
    fetchImpl: async () => {calls++; return {ok: false, status: 428};}}), false);
  assert.equal(calls, 1);
});

function surface() {
  const doc = {visibilityState: 'visible', querySelector: () => null,
    defaultView: {getComputedStyle: () => ({display: 'block', visibility: 'visible'}), frameElement: null}};
  const element = {isConnected: true, getClientRects: () => [{}], closest: () => null, ownerDocument: doc};
  return {doc, element};
}

test('hidden pages, hidden ancestors and parent question dialogs pause exposure', () => {
  const {doc, element} = surface();
  assert.equal(hasVisibleStudySurface(element), true);
  doc.visibilityState = 'hidden';
  assert.equal(hasVisibleStudySurface(element), false);
  doc.visibilityState = 'visible'; element.closest = () => ({});
  assert.equal(hasVisibleStudySurface(element), false);
  element.closest = () => null;
  const parent = surface();
  doc.defaultView.frameElement = parent.element;
  assert.equal(hasVisibleStudySurface(element), true);
  parent.doc.querySelector = () => ({});
  assert.equal(hasVisibleStudySurface(element), false);
});

test('intersection observer ignores offscreen cards and stops on unmount', () => {
  const {doc, element} = surface();
  const listeners = new Map();
  doc.addEventListener = (name, callback) => listeners.set(name, callback);
  doc.removeEventListener = name => listeners.delete(name);
  const timers = new Map();
  const win = {addEventListener: (name, callback) => listeners.set(name, callback),
    removeEventListener: name => listeners.delete(name),
    setInterval: (callback, ms) => {timers.set(ms, callback); return ms;},
    clearInterval: id => timers.delete(id)};
  let emit, disconnected = false, time = 0;
  class Observer { constructor(callback) {emit = callback;} observe() {} disconnect() {disconnected = true;} }
  const durations = [];
  const stop = observeJustification(element, {onDuration: ms => durations.push(ms),
    now: () => time, Observer, windowObject: win, documentObject: doc});
  const entry = {target: element, boundingClientRect: {height: 200, width: 200}, rootBounds: {height: 800},
    intersectionRect: {height: 0, width: 0}, isIntersecting: false};
  emit([entry]); time = 5000;
  emit([{...entry, isIntersecting: true, intersectionRect: {height: 150, width: 200}}]);
  time = 5500; doc.visibilityState = 'hidden'; listeners.get('visibilitychange')();
  time = 10000; doc.visibilityState = 'visible'; listeners.get('visibilitychange')();
  time = 10300; stop();
  assert.deepEqual(durations, [500, 300]);
  assert.equal(disconnected, true); assert.equal(timers.size, 0); assert.equal(listeners.size, 0);
});
