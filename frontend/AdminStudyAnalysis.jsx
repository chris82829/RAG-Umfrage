import React, {useState} from 'react';

const fmt = (value, digits = 2) => Number.isFinite(value) ? new Intl.NumberFormat('de-DE', {maximumFractionDigits:digits}).format(value) : '–';
const pValue = value => Number.isFinite(value) ? (value < 0.0001 ? value.toExponential(3) : fmt(value, 6)) : '–';
const interval = values => Array.isArray(values) && values.length === 2 && values.every(Number.isFinite) ? `[${fmt(values[0])}; ${fmt(values[1])}]` : '–';
const warningLabels = {
  'Incomplete questionnaires contribute whenever all endpoint items are valid.':'Unvollständige Fragebögen können beitragen, wenn alle Aussagen des jeweiligen Konstrukts gültig beantwortet sind.',
  'Recovered operation errors never automatically exclude a participant.':'Ein behobener Verarbeitungsfehler schließt eine Teilnahme nicht automatisch aus.',
  'A null manipulation test does not prove equivalence or absence of perception.':'Ein nicht signifikanter Manipulationscheck belegt weder Gleichwertigkeit noch fehlende Wahrnehmung.',
  'No subgroup causal claim: self-reported customization is self-selected.':'Die selbst gewählte Anpassung in C erlaubt keinen kausalen Vergleich innerhalb dieser Gruppe.',
  'Draft analysis plan: all findings are preliminary/exploratory, not preregistered confirmatory evidence.':'Der Analyseplan ist noch ein Entwurf. Alle Ergebnisse sind vorläufig und explorativ; sie sind keine präregistrierten Bestätigungsnachweise.',
};
const exclusionLabels = {not_v14:'Andere Fragebogenversion',not_main_wave:'Keine Hauptstudie',missing_or_invalid_arm:'Gruppenzuordnung fehlt',documented_terminal_technical_failure:'Dokumentierter endgültiger technischer Ausfall'};
const labels = {usefulness:'Nützlichkeit', control:'Kontrolle', transparency:'Transparenz', trust:'Vertrauen'};
function Contrast({value, title, corrected = false}) {
  if (!value) return null;
  return <section className="study-analysis-contrast"><h3>{title} · {value.contrast}</h3>
    <div className="admin-table-scroll"><table><thead><tr><th>Vergleich</th><th>n</th><th>Mittelwert</th><th>Standardabweichung</th></tr></thead><tbody>
      <tr><th>Erste Gruppe</th><td>{fmt(value.n_first,0)}</td><td>{fmt(value.mean_first)}</td><td>{fmt(value.sd_first)}</td></tr>
      <tr><th>Zweite Gruppe</th><td>{fmt(value.n_second,0)}</td><td>{fmt(value.mean_second)}</td><td>{fmt(value.sd_second)}</td></tr>
    </tbody></table></div>
    <dl className="study-analysis-values"><div><dt>Mittlere Differenz · 95-%-KI</dt><dd>{fmt(value.difference)} · {interval(value.difference_ci95)}</dd></div>
      <div><dt>Hedges’ g · 95-%-KI</dt><dd>{fmt(value.hedges_g)} · {interval(value.hedges_g_ci95)}</dd></div>
      <div><dt>Welch-Test · p</dt><dd>{pValue(value.p_value)}</dd></div>
      {corrected && <div><dt>p nach Holm-Korrektur</dt><dd>{pValue(value.p_holm)}</dd></div>}
      <div><dt>Mann-Whitney-Sensitivität · p</dt><dd>{pValue(value.mann_whitney_p)}</dd></div>
    </dl>{value.g_ci_warning && <p className="admin-small">Das Konfidenzintervall für Hedges’ g konnte nicht zuverlässig geschätzt werden; siehe den methodischen Hinweis im JSON-Export.</p>}{!Number.isFinite(value.p_value) && <p className="admin-small">Für diesen Vergleich sind noch keine ausreichenden gültigen Daten vorhanden.</p>}
  </section>;
}
export default function AdminStudyAnalysis({request}) {
  const [report, setReport] = useState(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');
  async function analyze() {
    setBusy(true);setError('');
    try {setReport(await request('/study-analysis'));}
    catch (failure) {setError(failure.message);}
    finally {setBusy(false);}
  }
  function download() {
    const url = URL.createObjectURL(new Blob([JSON.stringify(report,null,2)], {type:'application/json'}));
    const link = document.createElement('a');link.href = url;link.download = 'diana_v14_studienanalyse.json';link.click();
    setTimeout(() => URL.revokeObjectURL(url), 1000);
  }
  return <section className="admin-analysis admin-study-analysis" aria-label="Geplante Studienanalyse">
    <header><div><p className="admin-kicker">V14 · ANALYSEPLAN</p><h2>Hauptstudie auswerten</h2><p>Verwendet den vollständigen aktuellen V14-Datensatz der Hauptstudie. Die Filter der beschreibenden Ansichten gelten hier nicht. Pretest und frühere Fragebögen werden ausgeschlossen.</p></div></header>
    <aside className="telemetry-explanation"><strong>Vorläufige Auswertung</strong><p>Der Analyseplan ist ein Entwurf, solange er nicht vor Beginn der Hauptstudie verbindlich festgelegt wurde. Laufende Signifikanztests dürfen nicht darüber entscheiden, wann die Rekrutierung endet. Ergebnisse aus einer laufenden Erhebung sind vorläufig und explorativ.</p></aside>
    <div className="admin-detail-actions"><button className="admin-primary" disabled={busy} type="button" onClick={analyze}>{busy ? 'Wird berechnet …' : 'Analyse ausdrücklich berechnen'}</button>{report && <button type="button" onClick={download}>Analyse als JSON herunterladen</button>}</div>
    {error && <p className="admin-error" role="alert">{error}</p>}
    {report && <>
      <p className="admin-small">Analyseversion: {report.analysis_version} · Planstatus: {['frozen','frozen_before_main'].includes(report.plan_status) ? 'Festgelegt' : 'Entwurf'} · α = 0,05 · Haupttest zweiseitig</p>
      {report.warnings?.length > 0 && <ul className="study-analysis-warnings">{report.warnings.map((warning,index)=><li key={index}>{warningLabels[warning] || warning}</li>)}</ul>}
      <section><h3>Fallzahlen und Ausschlüsse</h3><div className="telemetry-summary"><div><strong>{fmt(report.sample_flow?.input_total,0)}</strong><span>Eingelesene Teilnahmen</span></div><div><strong>{fmt(report.sample_flow?.included_main,0)}</strong><span>Hauptstudie nach Ausschlüssen</span></div>{Object.entries(report.sample_flow?.arms || {}).map(([arm,n])=><div key={arm}><strong>{fmt(n,0)}</strong><span>Gruppe {arm}</span></div>)}</div>
        {Object.keys(report.sample_flow?.excluded_by_reason || {}).length > 0 && <dl className="study-analysis-values">{Object.entries(report.sample_flow.excluded_by_reason).map(([reason,n])=><div key={reason}><dt>{exclusionLabels[reason] || reason}</dt><dd>{fmt(n,0)}</dd></div>)}</dl>}
        <p className="admin-small">Die gültige Fallzahl kann je Konstrukt abweichen. Es werden nur vollständig beantwortete Skalen gemittelt; „Kann ich nicht beurteilen“ zählt nicht als 0.</p>
      </section>
      <Contrast value={report.primary} title="H1 · Nützlichkeit"/>
      <section><h3>Sekundäre Vergleiche · gemeinsame Holm-Korrektur</h3>{report.secondary?.map(item=><Contrast key={item.id || `${item.construct}-${item.contrast}`} value={item} title={labels[item.construct] || item.construct} corrected/>)}</section>
      <section><h3>Reliabilität der Skalen</h3><p className="admin-small">Niedrige Reliabilität wird als Einschränkung berichtet. Items und Haupttest werden deshalb nicht nachträglich entfernt. Die beiden Vertrauensitems bilden eine adaptierte Kurzskala.</p><div className="admin-table-scroll"><table><thead><tr><th>Konstrukt</th><th>n</th><th>Cronbachs α</th><th>Item-Korrelation</th><th>Spearman-Brown</th></tr></thead><tbody>{Object.entries(report.reliability || {}).map(([key,value])=><tr key={key}><th>{labels[key] || key}</th><td>{fmt(value.n,0)}</td><td>{fmt(value.alpha)}</td><td>{fmt(value.inter_item_correlation)}</td><td>{fmt(value.spearman_brown)}</td></tr>)}</tbody></table></div></section>
      <section><h3>Manipulationsprüfung · erkennbarer Charakter</h3><div className="admin-table-scroll"><table><thead><tr><th>Gruppe</th><th>n</th><th>Mittelwert</th><th>Standardabweichung</th></tr></thead><tbody>{Object.entries(report.manipulation?.groups || {}).map(([arm,value])=><tr key={arm}><th>{arm}</th><td>{fmt(value.n,0)}</td><td>{fmt(value.mean)}</td><td>{fmt(value.sd)}</td></tr>)}</tbody></table></div><p>Kruskal-Wallis: H = {fmt(report.manipulation?.h)} · p = {pValue(report.manipulation?.p_value)}</p><p className="admin-small">Erwartetes Muster: A niedriger als B und C. Diese Prüfung entscheidet nicht darüber, ob H1 ausgewertet wird. Ein nicht signifikanter Unterschied belegt weder eine gescheiterte Manipulation noch die Wirkungslosigkeit der Personalisierung.</p></section>
      {report.sensitivity_without_repeat && <details className="study-analysis-extra"><summary>Sensitivität ohne selbstberichtete Wiederholungsteilnahmen</summary><p>Diese Auswertung schließt Teilnahmen mit „Ja“ bei der Wiederholungsfrage aus; die Hauptauswertung bleibt separat sichtbar.</p><Contrast value={report.sensitivity_without_repeat.primary} title="H1 ohne Wiederholungsteilnahmen"/>{report.sensitivity_without_repeat.secondary?.map(item=><Contrast key={item.id || `${item.construct}-${item.contrast}`} value={item} title={labels[item.construct] || item.construct} corrected/>)}</details>}
      {report.exploratory?.length > 0 && <details className="study-analysis-extra"><summary>Explorative Vergleiche</summary><p>Diese Vergleiche dienen der Einordnung. Selbst ausgewählte Anpassungen in C erlauben keinen kausalen Vergleich.</p>{report.exploratory.map(item=><Contrast key={item.id || `${item.construct}-${item.contrast}`} value={item} title={labels[item.construct] || item.construct}/>)}</details>}
      {report.power && <section><h3>Stichprobenplanung</h3><p>Bei d = 0,35: {fmt(report.power.n_per_group_at_d_035,0)} gültige Teilnahmen je Gruppe für 80 % Power bei α = 0,05. Mit 130 je Gruppe erfassbarer Effekt: d ≈ {fmt(report.power.detectable_d_at_n_130,3)}.</p><p className="admin-small">Das ist eine Planung unter Modellannahmen, keine nachträglich aus dem beobachteten Effekt berechnete Power. Kleinster relevanter Effekt und Rekrutierungsende müssen vor dem Hauptstudienstart festgelegt werden.</p></section>}
    </>}
  </section>;
}
