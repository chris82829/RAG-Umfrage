import React, {useState} from 'react';

const number = (value, digits = 1) => value == null || !Number.isFinite(value)
  ? 'Nicht erfasst'
  : new Intl.NumberFormat('de-DE', {maximumFractionDigits: digits}).format(value);
const seconds = value => value == null ? 'Nicht erfasst' : `${number(value)} s`;
const timestamp = value => {
  if (!value) return 'Nicht erfasst';
  const parsed = new Date(/(?:Z|[+-]\d\d:\d\d)$/.test(value) ? value : `${value.replace(' ', 'T')}Z`);
  return Number.isNaN(parsed.getTime()) ? 'Nicht erfasst' : parsed.toLocaleString('de-DE');
};
const metrics = [
  {key: 'dwell_seconds', label: 'Sichtbare Begründungsdauer', format: seconds},
  {key: 'viewed_job_count', label: 'Stellen mit erfasster Interaktion', format: number},
  {key: 'job_expand_count', label: 'Begründungen aufgeklappt', format: number},
  {key: 'job_detail_count', label: 'Stellendetails geöffnet', format: number},
  {key: 'successful_chat_count', label: 'Erfolgreiche Chatnachrichten', format: number},
];
const statusLabel = value => value === 'completed' ? 'Abgeschlossen'
  : value === 'in_progress' || value === 'draft' ? 'Unvollständig' : 'Ohne Abschluss';

function MetricCard({value, label, note}) {
  return <div><strong>{value}</strong><span>{label}</span>{note && <small>{note}</small>}</div>;
}

function Participant({participant, onSelectParticipant}) {
  return <details className="telemetry-participant">
    <summary>
      <span className="telemetry-participant-identity"><strong>{participant.participation_id}</strong>
        <small>Gruppe {participant.study_arm || 'nicht erfasst'} · {statusLabel(participant.response_status)}</small></span>
      <span className="telemetry-participant-preview"><span>{seconds(participant.dwell_seconds)}<small>Begründungen sichtbar</small></span>
        <span>{number(participant.successful_chat_count, 0)}<small>Chatnachrichten</small></span></span>
      <span className="telemetry-disclosure" aria-hidden="true">⌄</span>
    </summary>
    <div className="telemetry-participant-content">
      <dl className="telemetry-participant-metrics">
        <div><dt>Stellen mit erfasster Interaktion</dt><dd>{number(participant.viewed_job_count, 0)}</dd></div>
        <div><dt>Begründungen aufgeklappt</dt><dd>{number(participant.job_expand_count, 0)}</dd></div>
        <div><dt>Stellendetails geöffnet</dt><dd>{number(participant.job_detail_count, 0)}</dd></div>
        <div><dt>Erfasste Ereignisse</dt><dd>{number(participant.event_count, 0)}</dd></div>
      </dl>
      <p className="admin-small">Erstes Ereignis: {timestamp(participant.first_event_at)} · Letztes Ereignis: {timestamp(participant.last_event_at)}</p>
      {participant.jobs?.length > 0 ? <table className="telemetry-table telemetry-job-table">
        <caption>Nutzung einzelner Stellen</caption>
        <thead><tr><th scope="col">Stellen-ID</th><th scope="col">Begründung sichtbar</th><th scope="col">Aufgeklappt</th><th scope="col">Details geöffnet</th><th scope="col">Angezeigte Ränge</th></tr></thead>
        <tbody>{participant.jobs.map(job => <tr key={job.job_id}>
          <th scope="row" data-label="Stellen-ID">{job.job_id}</th>
          <td data-label="Begründung sichtbar">{seconds(job.dwell_seconds)}</td>
          <td data-label="Aufgeklappt">{number(job.job_expand_count, 0)}</td>
          <td data-label="Details geöffnet">{number(job.job_detail_count, 0)}</td>
          <td data-label="Angezeigte Ränge">{job.displayed_ranks?.length ? job.displayed_ranks.join(', ') : 'Nicht erfasst'}</td>
        </tr>)}</tbody>
      </table> : <p className="telemetry-no-observation">Für diese Teilnahme sind noch keine Ereignisse zu einzelnen Stellen erfasst.</p>}
      {onSelectParticipant && <button type="button" onClick={() => onSelectParticipant(participant)}>Umfrageantworten ansehen</button>}
    </div>
  </details>;
}

export default function AdminTelemetry({data, busy = false, error, onSelectParticipant}) {
  const [selectedMetric, setSelectedMetric] = useState('dwell_seconds');
  const [query, setQuery] = useState('');
  const [page, setPage] = useState(0);
  if (busy) return <section className="admin-analysis" role="status">Nutzungsdaten werden geladen …</section>;
  if (error) return <p role="alert" className="admin-error">{error}</p>;
  if (!data) return null;
  const {summary, coverage, participants = [], groups = []} = data;
  const metric = metrics.find(item => item.key === selectedMetric) || metrics[0];
  const groupMax = Math.max(0, ...groups.map(group => group.metrics?.[metric.key]?.mean ?? 0));
  const filtered = participants.filter(item => String(item.participation_id).toLocaleLowerCase().includes(query.trim().toLocaleLowerCase()));
  const pageCount = Math.ceil(filtered.length / 10);
  const activePage = Math.min(page, Math.max(0, pageCount - 1));
  const totals = summary?.metrics || {};
  return <section className="admin-analysis admin-telemetry" aria-label="Auswertung der Nutzungsdaten">
    <header><div><p className="admin-kicker">NUTZUNGSANALYSE</p><h2>Was wurde tatsächlich genutzt?</h2>
      <p>Betrachtungszeiten, geöffnete Stellen und Chatnachrichten für die ausgewählten Teilnahmen. Die Filter oben gelten auch hier.</p>
    </div></header>
    <div className="telemetry-summary">
      <MetricCard value={number(coverage?.with_events, 0)} label="Teilnahmen mit Ereignissen" note={`von ${number(summary?.participant_count, 0)} ausgewählten Teilnahmen`}/>
      <MetricCard value={seconds(totals.dwell_seconds?.median)} label="Begründungsdauer · Median je Teilnahme" note={`${number(totals.dwell_seconds?.n, 0)} Teilnahmen mit Zeitmessung`}/>
      <MetricCard value={number(totals.viewed_job_count?.mean)} label="Stellen mit erfasster Interaktion · Mittelwert" note={`${number(totals.viewed_job_count?.n, 0)} Teilnahmen mit Messung`}/>
      <MetricCard value={number(totals.successful_chat_count?.total, 0)} label="Erfolgreiche Chatnachrichten insgesamt" note={`${number(totals.successful_chat_count?.n, 0)} Teilnahmen mit Chat-Zähler`}/>
    </div>
    <aside className="telemetry-explanation"><strong>So liest du diese Daten</strong>
      <p>Die Zeit misst, wie lange eine Begründung sichtbar war – nicht, ob sie aufmerksam gelesen wurde. Zeiten mehrerer gleichzeitig sichtbarer Stellen können sich überschneiden. Ihre Summe ist deshalb keine gesamte Nutzungsdauer.</p>
      <p>„Nicht erfasst“ wird bei Mittelwert und Median ausgelassen, nicht als 0 gezählt. Browserereignisse können fehlen. Chatnachrichten stammen aus dem erfolgreichen Server-Zähler.</p>
    </aside>
    {!summary?.participant_count ? <div className="admin-empty"><h3>Noch keine Nutzungsdaten in dieser Auswahl</h3><p>Nach neuen Teilnahmen erscheinen hier Kennzahlen, der Gruppenvergleich und die Details je Teilnahme.</p></div> : <>
      <section className="telemetry-group-section" aria-labelledby="telemetry-group-title">
        <div className="telemetry-section-heading"><div><h3 id="telemetry-group-title">A, B und C vergleichen</h3><p>Mittelwerte je Teilnahme; die Anzahl gültiger Messungen steht bei jeder Gruppe.</p></div>
          <label>Kennzahl<select aria-label="Kennzahl" value={metric.key} onChange={event => setSelectedMetric(event.target.value)}>{metrics.map(item => <option key={item.key} value={item.key}>{item.label}</option>)}</select></label></div>
        <div className="telemetry-group-bars" aria-label={`${metric.label}: Mittelwert je Teilnahme`}>
          {groups.map(group => {const values = group.metrics?.[metric.key]; return <div key={group.study_arm} className={`telemetry-group-bar arm-${group.study_arm}`}>
            <span>Gruppe {group.study_arm}</span><span className="telemetry-bar-track" aria-hidden="true"><span style={{width: `${groupMax > 0 ? ((values?.mean || 0) / groupMax) * 100 : 0}%`}}/></span>
            <span className="telemetry-bar-value"><strong>{metric.format(values?.mean)}</strong><small>n = {number(values?.n, 0)}</small></span>
          </div>;})}
        </div>
        <table className="telemetry-table telemetry-group-table"><caption>{metric.label} je Teilnahme</caption>
          <thead><tr><th scope="col">Gruppe</th><th scope="col">Teilnahmen</th><th scope="col">Mit Messung</th><th scope="col">Mittelwert</th><th scope="col">Median</th></tr></thead>
          <tbody>{groups.map(group => {const values = group.metrics?.[metric.key]; return <tr key={group.study_arm}>
            <th scope="row" data-label="Gruppe">{group.study_arm}</th><td data-label="Teilnahmen">{number(group.participant_count, 0)}</td>
            <td data-label="Mit Messung">{number(values?.n, 0)}</td><td data-label="Mittelwert">{metric.format(values?.mean)}</td><td data-label="Median">{metric.format(values?.median)}</td>
          </tr>;})}</tbody>
        </table>
        <p className="admin-small">Deskriptiver Vergleich, kein Signifikanztest. Unterschiede in der Zeit oder Klickzahl belegen für sich allein keine bessere Empfehlung.</p>
      </section>
      <section className="telemetry-participant-section" aria-labelledby="telemetry-participant-title">
        <div className="telemetry-section-heading"><div><h3 id="telemetry-participant-title">Einzelne Teilnahmen</h3><p>Öffne eine Teilnahme, um die Zeiten und Klicks jeder Stelle zu sehen.</p></div>
          <label>Teilnahme-ID suchen<input type="search" value={query} onChange={event => {setQuery(event.target.value);setPage(0);}} placeholder="ID eingeben"/></label></div>
        <div className="telemetry-participant-list">{filtered.slice(activePage * 10, (activePage + 1) * 10).map(participant => <Participant key={participant.participation_id} participant={participant} onSelectParticipant={onSelectParticipant}/>)}</div>
        {!filtered.length && <p className="admin-empty">Keine passende Teilnahme gefunden.</p>}
        {pageCount > 1 && <nav className="telemetry-pagination" aria-label="Seiten der Nutzungsdaten"><button type="button" disabled={activePage === 0} onClick={() => setPage(activePage - 1)}>Zurück</button><span>Seite {activePage + 1} von {pageCount}</span><button type="button" disabled={activePage + 1 >= pageCount} onClick={() => setPage(activePage + 1)}>Weiter</button></nav>}
      </section>
    </>}
    <p className="admin-footnote">Für eigene Analysen: „Nutzungsverhalten pro Teilnahme“ enthält eine Zeile je Teilnahme mit Summen in Sekunden. „Nutzungsereignisse als CSV“ enthält die einzelnen Ereignisse mit Stellen-ID und Dauer in Millisekunden. Beide Dateien lassen sich über die Teilnahme-ID mit den Umfrageantworten verknüpfen.</p>
  </section>;
}
