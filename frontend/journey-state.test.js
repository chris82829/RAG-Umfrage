import assert from 'node:assert/strict';
import { test } from 'node:test';
import { canVisitJourneyStep, currentJourneyStep } from './journey-state.js';

test('onboarding tracks its form and shows matching only during an active onboard request', () => {
  assert.equal(currentJourneyStep(), 1);
  assert.equal(currentJourneyStep({ onboardingStep: 2 }), 2);
  assert.equal(currentJourneyStep({ onboardingStep: 2, busy: true, operation: { kind: 'onboard' } }), 3);
  assert.equal(currentJourneyStep({ onboardingStep: 2, busy: false, operation: { kind: 'onboard' } }), 2);
  assert.equal(currentJourneyStep({ onboardingStep: 2, busy: true, operation: null }), 2);
});

test('a session is required before stale activity or a future onboarding value can show the final steps', () => {
  for (const onboardingStep of [1, 3, 4, 99]) {
    assert.equal(currentJourneyStep({ onboardingStep, activity: 'chat' }), 1);
  }
  assert.equal(currentJourneyStep({ hasSession: false, activity: 'chat', editor: 'advisor' }), 1);
  assert.equal(currentJourneyStep({ hasSession: false, busy: true, operation: { kind: 'refresh' } }), 1);
});

test('restored sessions open on results and editors retain priority while saving', () => {
  assert.equal(currentJourneyStep({ hasSession: true }), 3);
  for (const [editor, expected] of [['profile', 1], ['advisor', 2]]) {
    const state = Object.freeze({ hasSession: true, editor, activity: 'chat', busy: true,
      operation: Object.freeze({ kind: 'rerank' }) });
    assert.equal(currentJourneyStep(state), expected);
    assert.equal(currentJourneyStep({ ...state, busy: false }), expected);
  }
});

test('answer loading keeps the chat active and only explicit rerank or refresh operations select matching', () => {
  const chatting = { hasSession: true, activity: 'chat', busy: true };
  assert.equal(currentJourneyStep(chatting), 4);
  assert.equal(currentJourneyStep({ ...chatting, operation: { kind: 'chat' } }), 4);
  assert.equal(currentJourneyStep({ ...chatting, operation: { kind: 'chat', mode: 'rerank' } }), 4);
  for (const kind of ['rerank', 'refresh']) {
    assert.equal(currentJourneyStep({ ...chatting, operation: { kind } }), 3);
    assert.equal(currentJourneyStep({ ...chatting, busy: false, operation: { kind } }), 4);
  }
  assert.equal(currentJourneyStep({ hasSession: true, activity: 'results' }), 3);
});

test('navigation permits only the active step and earlier steps in sequence', () => {
  assert.equal(canVisitJourneyStep(1), true);
  for (const step of [2, 3, 4]) assert.equal(canVisitJourneyStep(step), false);
  for (const activeStep of [1, 2, 3, 4]) {
    const state = { hasSession: activeStep >= 3, activeStep };
    for (const step of [1, 2, 3, 4]) {
      assert.equal(canVisitJourneyStep(step, state), step <= activeStep,
        `active step ${activeStep}, target ${step}`);
    }
  }
});

test('a restored session does not unlock later cards after returning to the first step', () => {
  const state = { hasSession: true, activeStep: 1 };
  assert.equal(canVisitJourneyStep(1, state), true);
  for (const step of [2, 3, 4]) assert.equal(canVisitJourneyStep(step, state), false);
});

test('results and chat still require a session even if the active step is later', () => {
  const state = { hasSession: false, activeStep: 4 };
  for (const step of [1, 2]) assert.equal(canVisitJourneyStep(step, state), true);
  for (const step of [3, 4]) assert.equal(canVisitJourneyStep(step, state), false);
});

test('loading and boot restoration block navigation regardless of the chosen destination', () => {
  for (const step of [1, 2, 3, 4]) {
    assert.equal(canVisitJourneyStep(step, { hasSession: true, activeStep: 4, busy: true }), false);
    assert.equal(canVisitJourneyStep(step, { hasSession: true, activeStep: 4, booting: true }), false);
    assert.equal(canVisitJourneyStep(step, { hasSession: false, activeStep: 4, busy: true, booting: true }), false);
  }
});

test('navigation rejects invalid, fractional, coerced and future step values', () => {
  for (const step of [-1, 0, 1.5, 5, 99, NaN, Infinity, '1', '4', null, undefined, true, {}, []]) {
    assert.equal(canVisitJourneyStep(step, { hasSession: true, activeStep: 4 }), false, String(step));
  }
});

test('invalid active steps block every destination without coercion', () => {
  for (const activeStep of [-1, 0, 1.5, 5, 99, NaN, Infinity, '1', '4', null, true, {}, []]) {
    for (const step of [1, 2, 3, 4]) {
      assert.equal(canVisitJourneyStep(step, { hasSession: true, activeStep }), false, String(activeStep));
    }
  }
});
