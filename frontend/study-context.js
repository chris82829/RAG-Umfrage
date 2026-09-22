import {consentHeaders} from './privacy.js';

// This is the breakpoint of the two-pane jobs/chat layout in mobile.css.
export const STUDY_MOBILE_QUERY = '(max-width: 850px)';

export function installStudyViewportCapture(host, request = globalThis.fetch) {
  const media = host.matchMedia(STUDY_MOBILE_QUERY);
  let stopped = false;
  let lastSaved;
  let saving = false;
  let requested;
  const flush = async () => {
    requested = media.matches ? 'mobile' : 'desktop';
    if (stopped || saving || requested === lastSaved) return;
    const value = requested;
    saving = true;
    try {
      const response = await request('/api/study-context', {
        method: 'PUT', headers: {...consentHeaders(), 'Content-Type': 'application/json'},
        body: JSON.stringify({viewport_class: value}),
      });
      if (response.ok) lastSaved = value;
    } catch { /* Retry on a layout change or when the connection returns. */ }
    finally {
      saving = false;
      if (!stopped && requested !== value) void flush();
    }
  };
  media.addEventListener('change', flush);
  host.addEventListener('online', flush);
  void flush();
  return () => {stopped = true;media.removeEventListener('change', flush);host.removeEventListener('online', flush);};
}

export const STUDY_STEP_LABELS = {
  consent: 'Einwilligung', profile: 'Suchprofil', first_search: 'Erste Suche',
  chat: 'Chat', questionnaire_started: 'Fragebogen begonnen', questionnaire_completed: 'Fragebogen abgeschlossen',
};
export const studyWaveLabel = value => ({pretest: 'Pretest', main: 'Hauptstudie'})[value] || 'Nicht erfasst';
export const viewportLabel = value => ({mobile: 'Mobil', desktop: 'Desktop'})[value] || 'Nicht erfasst';

export function studyContextPayload({study_wave, recruitment_batch, revision}) {
  if (!['pretest', 'main'].includes(study_wave)) throw new Error('Bitte wähle Pretest oder Hauptstudie.');
  let batch = null;
  if (recruitment_batch.trim()) {
    // datetime-local is displayed in local time; send an unambiguous UTC timestamp.
    const parsed = new Date(recruitment_batch);
    if (Number.isNaN(parsed.getTime())) throw new Error('Bitte gib einen gültigen Zeitpunkt für die Einladungswelle ein.');
    batch = parsed.toISOString();
  }
  return {study_wave, recruitment_batch: batch, revision};
}
export function localDateTime(value) {
  if (!value) return '';
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return '';
  const pad = number => String(number).padStart(2, '0');
  return `${date.getFullYear()}-${pad(date.getMonth()+1)}-${pad(date.getDate())}T${pad(date.getHours())}:${pad(date.getMinutes())}`;
}
