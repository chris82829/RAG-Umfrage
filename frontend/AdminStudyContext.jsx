import React, {useEffect, useState} from 'react';
import {localDateTime, studyContextPayload, studyWaveLabel, viewportLabel, STUDY_STEP_LABELS} from './study-context.js';

export function ParticipantStudyContext({context}) {
  if (!context) return null;
  return <details className="admin-personality-usage"><summary>Studienphase und Verlauf</summary><dl>
    <div><dt>Studienphase</dt><dd>{studyWaveLabel(context.study_wave)}</dd></div>
    <div><dt>Einladungswelle</dt><dd>{context.recruitment_batch ? new Date(context.recruitment_batch).toLocaleString('de-DE') : 'Nicht erfasst'}</dd></div>
    <div><dt>Ansicht beim ersten Erfassen</dt><dd>{viewportLabel(context.viewport_class)}</dd></div>{context.viewport_class_last && context.viewport_class_last!==context.viewport_class && <div><dt>Zuletzt erfasste Ansicht</dt><dd>{viewportLabel(context.viewport_class_last)}</dd></div>}
    <div><dt>Weitester Schritt</dt><dd>{STUDY_STEP_LABELS[context.furthest_step_reached] || 'Nicht erfasst'}</dd></div>
  </dl><p className="admin-small">Die Studienphase und Einladungswelle werden beim Start festgehalten. Ein späterer Wechsel in der Verwaltung ändert diese Teilnahme nicht.</p></details>;
}

export default function AdminStudyContext({request, csrf, onSaved}) {
  const [settings, setSettings] = useState(null);
  const [wave, setWave] = useState('pretest');
  const [batch, setBatch] = useState('');
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');
  const [saved, setSaved] = useState(false);
  function apply(value) {setSettings(value);setWave(value.study_wave);setBatch(localDateTime(value.recruitment_batch));}
  useEffect(() => {
    const controller = new AbortController();
    request('/study-context', {signal: controller.signal}).then(apply).catch(failure => {if (failure.name !== 'AbortError') setError(failure.message);});
    return () => controller.abort();
  }, [request]);
  async function save(event) {
    event.preventDefault();
    if (busy || !settings) return;
    setBusy(true);setError('');setSaved(false);
    try {
      const body = studyContextPayload({study_wave: wave, recruitment_batch: batch, revision: settings.revision});
      apply(await request('/study-context', {method: 'PUT', headers: {'Content-Type':'application/json', 'X-CSRF-Token': csrf}, body: JSON.stringify(body)}));
      setSaved(true);onSaved?.();
    } catch (failure) {setError(failure.message);}
    finally {setBusy(false);}
  }
  return <details className="admin-cohort-control"><summary>Studienphase für neue Teilnahmen: {settings ? studyWaveLabel(settings.study_wave) : 'Wird geladen …'}</summary>
    <form onSubmit={save}>
      <p>Pretest und Hauptstudie werden getrennt gespeichert. Nur Teilnahmen der Hauptstudie fließen in die geplanten Hypothesentests ein. Diese Einstellung gilt ausschließlich für neu begonnene Teilnahmen.</p>
      <div className="admin-cohort-fields"><label>Phase neuer Teilnahmen<select value={wave} onChange={event => {setWave(event.target.value);setSaved(false);}} disabled={busy || !settings}><option value="pretest">Pretest</option><option value="main">Hauptstudie</option></select></label>
        <label>Einladungswelle · Zeitpunkt der E-Mail {wave === 'main' ? '(Pflicht für Hauptstudie)' : '(optional)'}<input type="datetime-local" required={wave==='main'} value={batch} onChange={event => {setBatch(event.target.value);setSaved(false);}} disabled={busy || !settings}/><small>Deine lokale Zeitzone; Speicherung als UTC. Der Eintrag versendet keine E-Mail.</small></label>
        <button className="admin-primary" type="submit" disabled={busy || !settings}>{busy ? 'Wird gespeichert …' : 'Für neue Teilnahmen speichern'}</button></div>
      {error && <p className="admin-error" role="alert">{error}</p>}{saved && <p className="admin-saved" role="status">Gespeichert. Bestehende Teilnahmen behalten ihre Studienphase.</p>}
    </form>
  </details>;
}
