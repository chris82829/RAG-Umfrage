import React,{useState} from 'react';
import {armLabel,promptSeriesLabel} from './admin-prompt-labels.js';

export {armLabel};

const format=value=>value==null?'–':new Intl.NumberFormat('de-DE',{maximumFractionDigits:2}).format(value);
const statusLabels={not_used:'Nicht genutzt',not_assessable:'Nicht beurteilbar',not_specified:'Keine Angabe',skipped:'Nicht gestellt',no_answer:'Leer',unanswered:'Noch offen',invalid:'Ungültiger Wert'};

export function QuestionChart({question,onSelect,seriesMeta={},version=''}){
 const {overall,groups}=question;
 const series=Object.keys(groups).length?Object.entries(groups):[['Gesamt',overall]];
 const meta=key=>key==='Gesamt'?{arm:'Gesamt'}:(seriesMeta[key]||{arm:key});
 const longLabel=key=>key==='Gesamt'?'Gesamt':promptSeriesLabel(meta(key),version);
 const shortLabel=key=>{const item=meta(key);return key==='Gesamt'?'Gesamt':`${item.arm}${item.revision!==''&&item.revision!=null?` · R${item.revision}`:''}`;};
 const isScale=question.kind==='scale';
 return <article className="analysis-question">
  <h3>{question.title}</h3>
  {question.framework && <p className="admin-small">{question.framework==='DIANA' ? (isScale?'Studienbezogenes DIANA-Zusatzitem':'Studienbezogene Angabe') : `Adaptiertes Item aus ${question.framework}`}{question.source_url && <> · <a href={question.source_url} target="_blank" rel="noreferrer">Quelle</a></>}</p>}
  {(question.reverse || question.direction==='higher_more_effort') && <p className="analysis-direction">Hohe Werte bedeuten mehr Aufwand.</p>}
  {question.visible_if && <p className="admin-small">Bedingte Frage: nur entsprechend der Fragebogenführung gestellt.</p>}
  <div className="analysis-question-meta"><span>{overall.n} gültige Antworten</span>{Object.entries(overall.statuses).filter(([key])=>key!=='answered').map(([key,value])=><span key={key}>{statusLabels[key]||key}: {value}</span>)}</div>
  {question.kind==='text'?<details><summary>Freitextantworten lesen ({overall.n})</summary><div className="analysis-texts">{overall.texts.map(text=><div key={text.id}><p>{text.text}</p><button onClick={()=>onSelect({id:text.id})}>{text.arm?`Variante ${text.arm} · `:''}Teilnahme ansehen</button></div>)}{overall.remaining_texts>0 && <p>Weitere {overall.remaining_texts} Texte sind in Einzelantworten und CSV verfügbar. Hier erscheinen die ersten 50.</p>}</div></details>:<>
   {isScale && <div className="analysis-means">{series.map(([key,result])=><div key={key} className={'analysis-arm arm-'+meta(key).arm}><strong>{longLabel(key)}</strong><span>Mittelwert <b>{format(result.mean)}</b></span><span>Median {format(result.median)} · n = {result.n}</span></div>)}</div>}
   {isScale && <p className="admin-small">1 = {question.scale.low} · {question.scale.max||10} = {question.scale.high}</p>}
   <div className="analysis-bars" aria-label="Antwortverteilung, Prozent der gültigen Antworten">
    {overall.distribution.map(option=><div className="analysis-bin" key={option.value}><span className="analysis-bin-label">{option.label}</span><div>{series.map(([key,result])=>{const point=result.distribution.find(item=>item.value===option.value);return <div className={'analysis-bar-row arm-'+meta(key).arm} key={key}><span className="analysis-series-label" title={longLabel(key)}>{shortLabel(key)}</span><div className="analysis-track" aria-hidden="true"><span style={{width:`${point.percent}%`}}/></div><span className="analysis-bar-number">{point.count} ({format(point.percent)} %)</span></div>;})}</div></div>)}
   </div>
   {overall.n===0 && <p>Noch keine gültige Antwort für diese Frage.</p>}
  </>}
 </article>;
}

function ConstructSummary({construct, seriesMeta, version}) {
 const series=Object.keys(construct.groups||{}).length?Object.entries(construct.groups):[['Gesamt',construct.overall]];
 return <article className="analysis-question analysis-construct">
  <h3>{construct.title}</h3>
  <p className="admin-small">{construct.role==='primary'?'Primärer Endpunkt':'Sekundärer Endpunkt'} · Mittelwert aus {construct.items.length} Aussagen · Skala {construct.min}–{construct.max}</p>
  <p className="analysis-construct-total">Gesamt: <strong>{format(construct.overall.mean)}</strong> · n = {construct.overall.n} · {construct.overall.missing} ohne vollständige Bewertung</p>
  <div className="analysis-means">{series.map(([key,result])=>{
   const meta=seriesMeta[key]||{arm:key};
   return <div key={key} className={'analysis-arm arm-'+meta.arm}>
    <strong>{key==='Gesamt'?'Gesamt':promptSeriesLabel(meta,version)}</strong>
    <span>Mittelwert <b>{format(result.mean)}</b></span>
    <span>Median {format(result.median)} · n = {result.n}</span>
   </div>;
  })}</div>
 </article>;
}

export default function AdminAnalytics({data,loading,error,onSelect}){
 const [category,setCategory]=useState('');
 if(loading)return <section className="admin-analysis" role="status">Diagramme werden geladen …</section>;
 if(error)return <p role="alert" className="admin-error">{error}</p>;
 if(!data)return null;
 const titles=[...new Set(data.cohorts.flatMap(cohort=>cohort.categories.map(item=>item.title)))];
 const selected=titles.includes(category)?category:'';
 return <section className="admin-analysis" aria-label="Grafische Auswertung"><header><div><p className="admin-kicker">GRAFISCHE AUSWERTUNG</p><h2>Antworten im Überblick</h2><p>Alle Antworten deiner Filterauswahl, unabhängig von der Tabellenseite. Prozentwerte beziehen sich auf gültige Antworten je Frage und Variante.</p></div>{titles.length>0 && <label>Kategorie<select value={selected} onChange={event=>setCategory(event.target.value)}><option value="">Alle Kategorien</option>{titles.map(title=><option key={title}>{title}</option>)}</select></label>}</header>
 <div className="analysis-summary"><div><strong>{data.total}</strong><span>Gespeicherte Teilnahmen</span></div><div><strong>{data.completed}</strong><span>Abgeschlossen</span></div><div><strong>{data.in_progress}</strong><span>Unvollständig</span></div></div>
 <p className="admin-small">Deskriptive Auswertung, kein Signifikanztest und kein Gesamtwert über alle Konstrukte. Unterschiedliche Experiment- und Promptfassungen werden getrennt dargestellt. Starts ohne gespeicherte Antworten sind hier nicht enthalten.</p>
 {data.message && <p>{data.message}</p>}
 {data.cohorts.map(cohort=>{const series=Object.keys(cohort.series||{}).length?cohort.series:Object.fromEntries(Object.entries(cohort.arms).map(([arm,count])=>[arm,{arm,count}]));return <section className="analysis-cohort" key={cohort.experiment_id+JSON.stringify(cohort.presentation_versions)}><h3>{data.version} · {cohort.experiment_id||'Ohne dokumentierte Experimentkennung'}</h3><p className="admin-small">Darstellungsstand: {(cohort.presentation_versions||[]).map(value=>value==='undocumented'?'Älterer / nicht dokumentierter Stand':value==='ranked_insights'?'Alle Varianten mit Ranking, Scores und Begründungen':value==='fair-standard-advice-v1'?'A: sachliche Standardberatung mit Ranking, Scores und Begründungen':value==='random-order-generic-chat-v2'?'A: Zufallsreihenfolge, Ein-Satz-Prompt':value==='random-order-generic-chat-v1'?'A: Zufallsreihenfolge und allgemeiner Chat':value).join(' + ')}{cohort.presentation_versions?.length>1?' · Mehrere Stände genutzt; gesondert auswerten.':''}</p><p className="analysis-legend">{Object.entries(series).map(([key,item])=><span key={key} className={'arm-'+item.arm}><i/> {promptSeriesLabel(item,data.version)}: {item.count}</span>)}</p>
 {cohort.mixed_prompt_arms?.length>0&&<p className="admin-prompt-warning" role="status"><strong>Mehrere Promptfassungen erkannt:</strong> Variante {cohort.mixed_prompt_arms.join(', ')} wird in den Diagrammen getrennt nach Revision und Basis-SHA dargestellt. Bei C bezeichnet sie den Berufsberater-Basisprompt; die selbst gestaltete Persönlichkeit wird dynamisch ergänzt. Mit dem Promptfilter kannst du eine exakte Basisfassung isolieren.</p>}
 <p className="admin-small">A: Basissystem ohne wählbare KI-Suchpersönlichkeit. B: fester Top-Berufsberater. C: selbst gestaltbare Persönlichkeit auf Basis einer eigenen Systemanweisung. Alle Varianten verwenden Ranking, Scores und Begründungen.</p>
 {cohort.constructs?.length>0 && <section className="analysis-constructs" aria-label="Zusammenfassung der Konstrukte">
  <h3 className="analysis-category-title">Nutzen, Kontrolle und Nachvollziehbarkeit</h3>
  <p className="admin-small">Je Teilnahme zählt der Mittelwert einer Itemgruppe nur dann, wenn alle zugehörigen Aussagen numerisch beantwortet wurden. „Kann ich nicht beurteilen“ und fehlende Antworten werden nicht als 0 gewertet. Die drei Itemgruppen bleiben getrennt; diese Adaptation ist keine eigenständig validierte deutsche Gesamtskala.</p>
  <div className="analysis-grid">{cohort.constructs.map(construct=><ConstructSummary key={construct.id} construct={construct} seriesMeta={series} version={data.version}/>)}</div>
 </section>}
 {cohort.categories.filter(item=>!selected||item.title===selected).map(item=><section key={item.title}><h3 className="analysis-category-title">{item.title}</h3><div className="analysis-grid">{item.questions.map(question=><QuestionChart key={question.name} question={question} onSelect={onSelect} seriesMeta={series} version={data.version}/>)}</div></section>)}
 </section>;})}
 </section>;
}
