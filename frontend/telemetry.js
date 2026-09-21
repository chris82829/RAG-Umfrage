import {consentHeaders} from './privacy.js';

const CLIENT_EVENTS = new Set(['dwell_justification', 'job_expand', 'job_detail']);
const ID = /^[A-Za-z0-9_-]{1,100}$/;
const MAX_DURATION_MS = 60000;
const MAX_SEND_ATTEMPTS = 2;

/** Best-effort study observations. Failure must never interrupt the participant. */
export async function sendStudyEvent(sessionId, eventType, metadata, {
  headers = consentHeaders(), fetchImpl = globalThis.fetch,
  eventId = globalThis.crypto?.randomUUID?.(),
} = {}) {
  if (!headers['X-Diana-Consent'] || headers['X-Diana-Test'] || !eventId
      || !/^[A-Za-z0-9_-]{32,100}$/.test(sessionId || '') || !CLIENT_EVENTS.has(eventType)) return false;
  if (!metadata || !ID.test(String(metadata.job_id || ''))
      || !Number.isInteger(metadata.rank) || metadata.rank < 1 || metadata.rank > 20) return false;
  const safeMetadata = {job_id: String(metadata.job_id), rank: metadata.rank};
  if (eventType === 'dwell_justification') {
    if (!Number.isInteger(metadata.duration_ms) || metadata.duration_ms < 1 || metadata.duration_ms > MAX_DURATION_MS) return false;
    safeMetadata.duration_ms = metadata.duration_ms;
  }
  const body = JSON.stringify({session_id: sessionId, event_id: eventId,
    event_type: eventType, metadata: safeMetadata});
  for (let attempt = 0; attempt < MAX_SEND_ATTEMPTS; attempt += 1) {
    try {
      const response = await fetchImpl('/api/track_event', {method: 'POST',
        headers: {...headers, 'Content-Type': 'application/json'}, body, keepalive: true});
      if (response.ok) return true;
      if (response.status < 500) return false;
    } catch { /* A single immediate retry uses the same ID and cannot duplicate a row. */ }
  }
  return false;
}

/** Pure clock used by the DOM observer and tests; active milliseconds only. */
export function createDwellClock({now = () => performance.now(), onDuration}) {
  let started = null;
  function flush() {
    if (started === null) return;
    const end = now();
    let duration = Math.max(0, Math.round(end - started));
    started = end;
    while (duration > 0) {
      const chunk = Math.min(duration, MAX_DURATION_MS);
      onDuration(chunk);
      duration -= chunk;
    }
  }
  return {
    update(active) {
      if (active && started === null) started = now();
      if (!active && started !== null) { flush(); started = null; }
    },
    flush,
    stop() { if (started !== null) { flush(); started = null; } },
  };
}

/** Check the embedded study too: a parent question/loading dialog masks jobs. */
export function hasVisibleStudySurface(element) {
  if (!element?.isConnected || !element.getClientRects().length) return false;
  let doc = element.ownerDocument;
  let current = element;
  try {
    while (doc) {
      if (doc.visibilityState !== 'visible' || current.closest('[hidden], [inert], [aria-hidden="true"]')
          || doc.querySelector('dialog[open]')) return false;
      const style = doc.defaultView.getComputedStyle(current);
      if (style.display === 'none' || style.visibility === 'hidden') return false;
      const frame = doc.defaultView.frameElement;
      if (!frame) break;
      if (!frame.getClientRects().length) return false;
      current = frame;
      doc = frame.ownerDocument;
    }
    return true;
  } catch { return false; }
}

/**
 * Observe actual justification area, not the whole mounted card. At least half
 * the element (or half a viewport for long text) must be visible. Flush each 15s,
 * on visibility changes and on unmount. No inference about reading/attention.
 */
export function observeJustification(element, {onDuration, isActive = () => true,
  now = () => performance.now(), Observer = globalThis.IntersectionObserver,
  windowObject = globalThis.window, documentObject = globalThis.document,
} = {}) {
  if (!element || !Observer || !windowObject || !documentObject) return () => {};
  const clock = createDwellClock({now, onDuration});
  let intersecting = false;
  const update = () => clock.update(intersecting && isActive() && hasVisibleStudySurface(element));
  const observer = new Observer(entries => {
    const entry = entries.find(item => item.target === element);
    if (entry) {
      const target = entry.boundingClientRect;
      const requiredHeight = Math.min(target.height / 2, (entry.rootBounds?.height || target.height) / 2);
      intersecting = entry.isIntersecting && entry.intersectionRect.height >= requiredHeight
        && entry.intersectionRect.width >= target.width / 2;
    }
    update();
  }, {threshold: [0, 0.1, 0.25, 0.5, 0.75, 1]});
  observer.observe(element);
  const onHide = () => clock.stop();
  documentObject.addEventListener('visibilitychange', update);
  windowObject.addEventListener('pagehide', onHide);
  // Also catches parent iframe overlays, mobile tab changes and CSS visibility.
  const visibilityTimer = windowObject.setInterval(update, 250);
  const flushTimer = windowObject.setInterval(() => { update(); clock.flush(); }, 15000);
  return () => {
    observer.disconnect();
    windowObject.clearInterval(visibilityTimer);
    windowObject.clearInterval(flushTimer);
    documentObject.removeEventListener('visibilitychange', update);
    windowObject.removeEventListener('pagehide', onHide);
    clock.stop();
  };
}
