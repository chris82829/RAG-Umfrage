import React,{useEffect,useState} from 'react';
import {RefreshCw,Save} from 'lucide-react';

const promptKeys=['unprompted','career_fixed','custom_career'];

function promptValue(value,key) {
  const entry=value?.prompts?.[key];
  if(typeof entry==='string')return {text:entry,revision:value?.revision,sha256:'',updated_at:null};
  return {text:entry?.text ?? '',revision:entry?.revision ?? value?.revision,sha256:entry?.sha256 ?? '',updated_at:entry?.updated_at ?? null};
}

export function normalizeSystemPrompts(value) {
  if(!value || typeof value!=='object' || !value.prompts)throw new Error('Die Systemprompts konnten nicht gelesen werden.');
  return {revision:value.revision,...Object.fromEntries(promptKeys.map(key=>[key,promptValue(value,key)]))};
}

function shortSha(value){return value?String(value).slice(0,12):'noch nicht verfügbar';}
function revisionLabel(value){return value===undefined||value===null||value===''?'–':String(value);}
function updatedLabel(value){if(!value)return '';const date=new Date(value);return Number.isNaN(date.valueOf())?'':date.toLocaleString('de-DE');}

export default function AdminSystemPrompts({request,csrf}) {
  const [record,setRecord]=useState(null),[drafts,setDrafts]=useState({unprompted:'',career_fixed:'',custom_career:''});
  const [loading,setLoading]=useState(true),[saving,setSaving]=useState(false),[error,setError]=useState(''),[saved,setSaved]=useState(false);
  function apply(value){const next=normalizeSystemPrompts(value);setRecord(next);setDrafts({unprompted:next.unprompted.text,career_fixed:next.career_fixed.text,custom_career:next.custom_career.text});setSaved(false);}
  async function load(signal){setLoading(true);setError('');try{apply(await request('/system-prompts',{signal}));}catch(failure){if(failure.name!=='AbortError')setError(failure.message);}finally{if(!signal?.aborted)setLoading(false);}}
  useEffect(()=>{const controller=new AbortController();void load(controller.signal);return()=>controller.abort();},[request]);
  const dirty=!!record && promptKeys.some(key=>drafts[key]!==record[key].text);
  const promptDirty=key=>!!record&&drafts[key]!==record[key].text;
  async function save(event){
    event.preventDefault();if(!dirty||saving||['career_fixed','custom_career'].some(key=>!drafts[key].trim()))return;
    setSaving(true);setError('');setSaved(false);
    try{
      const value=await request('/system-prompts',{method:'PUT',headers:{'Content-Type':'application/json','X-CSRF-Token':csrf},body:JSON.stringify({revision:record.revision,prompts:{unprompted:drafts.unprompted,career_fixed:drafts.career_fixed,custom_career:drafts.custom_career}})});
      apply(value);setSaved(true);
    }catch(failure){setError(failure.status===409?'Die Systemprompts wurden zwischenzeitlich geändert. Lade den aktuellen Stand neu und übernimm deine Änderungen erneut.':failure.message);}
    finally{setSaving(false);}
  }
  return <section className="admin-system-prompts" aria-labelledby="admin-system-prompts-title" aria-busy={loading||saving}>
    <header><div><p className="admin-kicker">LLM-STEUERUNG</p><h2 id="admin-system-prompts-title">Systemprompts</h2><p>A, B und C werden getrennt verwaltet. Ein leeres Feld bei A sendet weiterhin gar keine Systemnachricht. Änderungen gelten für neue Teilnahmen und neue unabhängige Testläufe; bereits zugeteilte Teilnahmen behalten ihren dokumentierten Stand. Jede Fassung erhält eine Revision und Prüfsumme.</p><p className="admin-small"><strong>Studienhinweis:</strong> Eine Änderung während der Rekrutierung erzeugt mehrere Behandlungsfassungen. Werte sie anhand von Prompt-Revision und SHA-256 getrennt aus.</p></div>{record&&<span className="admin-prompt-revision">Gesamtrevision {revisionLabel(record.revision)}</span>}</header>
    {loading&&!record?<p role="status">Systemprompts werden geladen …</p>:record&&<form onSubmit={save}>
      <div className="admin-prompt-grid">
        {[
          ['unprompted','A','Basissystem','Optionaler eigener Systemprompt. Leer lassen, um A ohne Systemprompt auszuführen.'],
          ['career_fixed','B','Top-Berufsberater','Fester Systemprompt für die Berufsberatung.'],
          ['custom_career','C','Selbst gestaltete Persönlichkeit','Basis-Systemprompt, der serverseitig um die persönliche Gestaltung ergänzt wird.'],
        ].map(([key,arm,title,description])=><article className="admin-prompt-card" key={key}><div className="admin-prompt-heading"><div><span className="admin-prompt-arm">{arm}</span><h3>{title}</h3></div><p>{description}</p></div><label htmlFor={`admin-prompt-${key}`}>Prompttext<textarea id={`admin-prompt-${key}`} required={key!=='unprompted'} rows={16} value={drafts[key]} disabled={saving} onChange={event=>{setDrafts(current=>({...current,[key]:event.target.value}));setSaved(false);}}/></label><p className="admin-prompt-meta">{promptDirty(key)?'Neue Prüfsumme wird beim Speichern berechnet':<>Gespeicherte Revision {revisionLabel(record[key].revision)} · SHA-256 {shortSha(record[key].sha256)}{key==='unprompted'&&!record[key].text.trim()?' · leer, daher keine Systemnachricht':''}{updatedLabel(record[key].updated_at)?` · ${updatedLabel(record[key].updated_at)}`:''}</>}</p></article>)}
      </div>
      {error&&<p className="admin-error" role="alert">{error}</p>}{saved&&<p className="admin-saved" role="status">Systemprompts gespeichert.</p>}
      <div className="admin-prompt-actions"><button type="button" disabled={loading||saving||dirty} onClick={()=>void load()}><RefreshCw size={16}/>Neu laden</button><button type="submit" className="admin-primary" disabled={!dirty||saving||['career_fixed','custom_career'].some(key=>!drafts[key].trim())}><Save size={16}/>{saving?'Wird gespeichert …':'Alle Prompts speichern'}</button></div>
    </form>}
    {!loading&&!record&&<>{error&&<p className="admin-error" role="alert">{error}</p>}<button type="button" onClick={()=>void load()}><RefreshCw size={16}/>Erneut laden</button></>}
  </section>;
}
