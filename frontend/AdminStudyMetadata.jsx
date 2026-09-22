import React, {useState} from 'react';
import {STUDY_STEP_LABELS, studyWaveLabel, viewportLabel} from './study-context.js';

const num = value => Number.isFinite(value) ? new Intl.NumberFormat('de-DE').format(value) : '–';
const weightText = value => Array.isArray(value) ? value.join(' / ') : value && typeof value === 'object' ? Object.values(value).join(' / ') : 'Nicht erfasst';
export default function AdminStudyMetadata({data, busy, error, downloading, onDownload}) {
  const [query, setQuery] = useState('');
  const [page, setPage] = useState(0);
  if (busy) return <p role="status">Studienverlauf wird geladen …</p>;
  if (error) return <p role="alert" className="admin-error">{error}</p>;
  if (!data) return null;
  const participants = data.participants || [];
  const filtered = participants.filter(item => item.participation_id?.toLocaleLowerCase().includes(query.trim().toLocaleLowerCase()));
  const pages = Math.ceil(filtered.length / 20);
  const currentPage = Math.min(page, Math.max(0, pages - 1));
  return <section className="admin-analysis admin-study-metadata" aria-label="Studienverlauf und technische Metadaten">
    <h2>Studienverlauf und technische Metadaten</h2>
    <p>Enthält auch Teilnahmen ohne gespeicherte Fragebogenantwort. Hier gelten Studienphase und Gruppe; Antwortstatus, ID- und Promptfilter werden für diese vollständige Verlaufssicht nicht verwendet. Die Verteilung zeigt den jeweils weitesten erreichten Schritt, keine addierbaren Durchlaufzahlen. Eine noch laufende Teilnahme ist kein nachgewiesener Abbruch.</p>
    <button type="button" disabled={downloading} onClick={onDownload}>Studienverlauf, Fehler und Scoring als ZIP herunterladen</button>
    <div className="telemetry-summary">{Object.entries(data.wave_counts || {}).map(([wave,count])=><div key={wave}><strong>{num(count)}</strong><span>{studyWaveLabel(wave)}</span></div>)}{Object.entries(data.viewport_counts || {}).map(([viewport,count])=><div key={viewport}><strong>{num(count)}</strong><span>Ansicht: {viewportLabel(viewport)}</span></div>)}</div>
    <div className="admin-table-scroll"><table><caption>Weitester Schritt je Teilnahme</caption><thead><tr><th>Schritt</th><th>Teilnahmen</th></tr></thead><tbody>{Object.entries(STUDY_STEP_LABELS).map(([step,label])=><tr key={step}><th>{label}</th><td>{num(data.step_counts?.[step] ?? 0)}</td></tr>)}</tbody></table></div>
    <details className="study-analysis-extra"><summary>Fehler und tatsächlich verwendete Gewichte</summary>
      <p>Fehlercodes und Verarbeitungsschritte enthalten keine Such- oder Chattexte. Ein früherer Fehler kann durch einen späteren erfolgreichen Versuch behoben worden sein.</p>
      {data.errors?.length ? <div className="admin-table-scroll"><table><thead><tr><th>Fehlercode</th><th>Verarbeitungsschritt</th><th>Anzahl</th></tr></thead><tbody>{data.errors.map((item,index)=><tr key={index}><td>{item.error_code || 'Nicht erfasst'}</td><td>{item.error_stage || 'Nicht erfasst'}</td><td>{num(item.count)}</td></tr>)}</tbody></table></div> : <p>Keine erfassten Fehler in dieser Auswahl.</p>}
      <p>Scoring-Aufrufe: <strong>{num(data.scoring?.call_count)}</strong>. Reihenfolge der Gewichte: fachliche Passung, Profilpräferenzen, fachliche Tiefe, Lernen/Entwicklung, Gestaltung/Innovation, Klarheit.</p>
      {data.scoring?.weight_vectors?.length ? <div className="admin-table-scroll"><table><thead><tr><th>Tatsächliche Gewichte in %</th><th>Aufrufe</th></tr></thead><tbody>{data.scoring.weight_vectors.map((item,index)=><tr key={index}><td>{weightText(item.applied_weights)}</td><td>{num(item.count)}</td></tr>)}</tbody></table></div> : <p>Es sind noch keine Scoring-Aufrufe erfasst.</p>}
    </details>
    <details className="study-analysis-extra"><summary>Verlauf einzelner Teilnahmen ({num(participants.length)})</summary>
      <label className="study-metadata-search">Teilnahme-ID<input type="search" value={query} onChange={event=>{setQuery(event.target.value);setPage(0);}} placeholder="ID suchen"/></label>
      <div className="admin-table-scroll"><table><thead><tr><th>Teilnahme-ID</th><th>Gruppe</th><th>Studienphase</th><th>Ansicht</th><th>Weitester Schritt</th><th>Einladungswelle</th></tr></thead><tbody>{filtered.slice(currentPage*20,(currentPage+1)*20).map(item=><tr key={item.participation_id}><td>{item.participation_id}</td><td>{item.study_arm || '–'}</td><td>{studyWaveLabel(item.study_wave)}</td><td>{viewportLabel(item.viewport_class)}</td><td>{STUDY_STEP_LABELS[item.furthest_step_reached] || 'Nicht erfasst'}</td><td>{item.recruitment_batch ? new Date(item.recruitment_batch).toLocaleString('de-DE') : 'Nicht erfasst'}</td></tr>)}</tbody></table></div>
      {!filtered.length && <p>Keine Teilnahmen in dieser Auswahl.</p>}
      {pages > 1 && <nav className="admin-pagination" aria-label="Seiten der Studienverläufe"><button disabled={currentPage===0} onClick={()=>setPage(currentPage-1)}>Zurück</button><span>Seite {currentPage+1} von {pages}</span><button disabled={currentPage+1>=pages} onClick={()=>setPage(currentPage+1)}>Weiter</button></nav>}
    </details>
  </section>;
}
