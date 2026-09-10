import React, {useEffect,useRef,useState} from 'react';
import {Download,LogOut,Search,ShieldCheck,Trash2,X,Play,Pause} from 'lucide-react';
import './admin.css';

async function api(path,options={}){
 const response=await fetch('/api/admin'+path,options);
 const data=await response.json();
 if(!response.ok){const error=new Error(data.error?.message || 'Anfrage fehlgeschlagen.');error.status=response.status;throw error;}
 return data;
}
export function AdminDeleteDialog({row,busy,error,onClose,onDelete}){
 const ref=useRef(null);
 const [confirmation,setConfirmation]=useState('');
 useEffect(()=>{ref.current.showModal();},[]);
 return <dialog ref={ref} className="admin-delete" onCancel={event=>{event.preventDefault();if(!busy)onClose();}}><h2>Teilnahme löschen?</h2><p><strong>{row.participation_id}</strong></p><p>{row.deletion_count} gespeicherte Antwort{row.deletion_count===1?'':'en'} dieser Teilnahme werden gelöscht.{row.consent_linked?' Die Einwilligung wird widerrufen und weitere Anfragen werden gesperrt.':''}</p><p>Bereits heruntergeladene Exportdateien musst du gesondert bereinigen.</p><label>Teilnahme-ID zur Bestätigung<input autoComplete="off" value={confirmation} onChange={event=>setConfirmation(event.target.value)} disabled={busy}/></label>{error && <p role="alert" className="admin-error">{error}</p>}<div className="admin-dialog-actions"><button onClick={onClose} disabled={busy}>Abbrechen</button><button className="admin-danger" onClick={onDelete} disabled={busy || confirmation!==row.participation_id}>{busy?'Wird gelöscht …':'Teilnahme endgültig löschen'}</button></div></dialog>;
}
export function AdminAnswerDetail({row,definition,onClose,onDelete}){
 definition=row.definition || definition;
 const fields=[definition.demographics,...definition.categories].flatMap(group=>group.fields);
 function label(name){return fields.find(field=>field.name===name)?.title || name;}
 function value(name,raw){const field=fields.find(field=>field.name===name);return [...(field?.options || []),...(field?.nonresponse || [])].find(([key])=>key===raw)?.[1] ?? (raw===null?(row.response_status==='in_progress'?'Noch nicht beantwortet / nicht gestellt':'Übersprungen'):raw===''?'Keine Angabe':String(raw));}
 return <section className="admin-detail" aria-label="Einzelantwort"><div className="admin-detail-heading"><div><p className="admin-kicker">EINZELANTWORT</p><h2>{row.participation_id}</h2></div><button aria-label="Einzelantwort schließen" onClick={onClose}><X size={20}/></button></div><p>{row.response_status==='in_progress'?'Unvollständig · ':'Abgeschlossen · '}{row.survey_version}{row.study_arm ? ` · Variante ${row.study_arm}` : ''} · {row.openai_models.length?row.openai_models.join(', '):'Modellstand nicht dokumentiert'}</p><dl>{Object.entries(row.answers).map(([name,raw])=><div key={name}><dt>{row.survey_version==='diana-v1'?'V1 · ':''}{label(name)}</dt><dd>{value(name,raw)}</dd></div>)}</dl><button className="admin-danger" onClick={onDelete}><Trash2 size={16}/>Teilnahme löschen</button></section>;
}
export function AdminStudyControl({study,busy,onToggle}){
 return <section className={'admin-study '+(study?.enabled?'is-open':'is-paused')} aria-label="Teilnahme freigeben"><div><h2>Umfrage freigeben</h2><p role="status"><strong>{!study?'Status wird geladen …':study.closed?'Studie beendet':study.enabled?'Teilnahme freigegeben':'Teilnahme pausiert'}</strong></p><p>Du bestimmst, wann die Umfrage genutzt werden kann. Beim Pausieren bleiben gespeicherte Antworten erhalten; neue Teilnahmen und weitere Such-, Chat- und Antwortanfragen werden gesperrt.</p></div><button type="button" className={study?.enabled?'':'admin-primary'} disabled={busy || !study || study.closed || (!study.enabled && !study.can_enable)} onClick={onToggle}>{study?.enabled?<Pause size={18}/>:<Play size={18}/>} {busy?'Wird gespeichert …':study?.enabled?'Umfrage pausieren':'Umfrage freigeben'}</button></section>;
}
export default function AdminPage({initialAuth=null}){
 const [auth,setAuth]=useState(initialAuth),[password,setPassword]=useState(''),[busy,setBusy]=useState(false),[error,setError]=useState('');
 const [data,setData]=useState(null),[query,setQuery]=useState(''),[version,setVersion]=useState(''),[status,setStatus]=useState(''),[arm,setArm]=useState(''),[filter,setFilter]=useState({q:'',version:'',status:'',arm:'',page:1}),[refresh,setRefresh]=useState(0);
 const [row,setRow]=useState(null),[deleting,setDeleting]=useState(false),[deleteError,setDeleteError]=useState('');
 const [study,setStudy]=useState(null),[studyBusy,setStudyBusy]=useState(false);
 const selection=useRef(0);
 useEffect(()=>{document.title='DIANA · Umfrageverwaltung';api('/session').then(setAuth).catch(failure=>setError(failure.message));},[]);
 useEffect(()=>{
  if(!auth?.authenticated)return;
  const controller=new AbortController();setError('');
  api('/responses?'+new URLSearchParams(filter),{signal:controller.signal}).then(setData).catch(failure=>{if(failure.name==='AbortError')return;if(failure.status===401){setAuth({configured:true,authenticated:false});setData(null);setRow(null);}setError(failure.message);});
  return()=>controller.abort();
 },[auth?.authenticated,filter,refresh]);
 useEffect(()=>{
  if(!auth?.authenticated){setStudy(null);return;}
  const controller=new AbortController();
  api('/study-status',{signal:controller.signal}).then(setStudy).catch(failure=>{if(failure.name!=='AbortError')setError(failure.message);});
  return()=>controller.abort();
 },[auth?.authenticated]);
 async function toggleStudy(){
  if(!study || studyBusy)return;
  setStudyBusy(true);setError('');
  try{setStudy(await api('/study-status',{method:'PUT',headers:{'Content-Type':'application/json','X-CSRF-Token':auth.csrf},body:JSON.stringify({enabled:!study.enabled})}));}
  catch(failure){setError(failure.message);}
  finally{setStudyBusy(false);}
 }
 async function login(event){event.preventDefault();if(busy)return;setBusy(true);setError('');try{setAuth(await api('/login',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({password})}));setPassword('');}catch(failure){setError(failure.message);}finally{setBusy(false);}}
 async function logout(){try{await api('/logout',{method:'POST',headers:{'X-CSRF-Token':auth.csrf}});selection.current++;setAuth({configured:true,authenticated:false});setData(null);setRow(null);}catch(failure){setError(failure.message);}}
 async function select(item){const ticket=++selection.current;setError('');try{const selected=await api('/responses/'+item.id);if(ticket===selection.current)setRow(selected);}catch(failure){setError(failure.message);}}
 async function remove(){if(busy)return;setBusy(true);setDeleteError('');try{await api('/responses/'+row.id,{method:'DELETE',headers:{'Content-Type':'application/json','X-CSRF-Token':auth.csrf},body:JSON.stringify({confirm_id:row.participation_id})});setDeleting(false);setRow(null);selection.current++;setRefresh(value=>value+1);}catch(failure){setDeleteError(failure.message);}finally{setBusy(false);}}
 async function download(format){setBusy(true);setError('');try{const response=await fetch('/api/admin/export?'+new URLSearchParams({q:filter.q,version:filter.version,status:filter.status,arm:filter.arm,format}));if(!response.ok)throw new Error('Download fehlgeschlagen. Bitte Anmeldung prüfen.');const blob=await response.blob(),url=URL.createObjectURL(blob),link=document.createElement('a');link.href=url;link.download=format==='zip'?'diana_auswertung.zip':'diana_numiqo.csv';link.click();setTimeout(()=>URL.revokeObjectURL(url),1000);}catch(failure){setError(failure.message);}finally{setBusy(false);}}
 if(!auth?.authenticated)return <main className="admin-page"><form className="admin-login" onSubmit={login}><ShieldCheck size={30}/><h1>DIANA Umfrageverwaltung</h1><p>Geschützter Zugang zu deinen Forschungsergebnissen.</p>{auth?.configured===false?<p>Der Zugang muss auf dem Server eingerichtet werden.</p>:<><label>Passwort<input type="password" autoComplete="current-password" value={password} onChange={event=>setPassword(event.target.value)} required maxLength={200}/></label><button className="admin-primary" disabled={busy || !auth}>{busy?'Anmelden …':'Anmelden'}</button></>}{error && <p className="admin-error" role="alert">{error}</p>}<a href="/">Zur DIANA-Startseite</a></form></main>;
 return <main className="admin-page"><div className="admin-container"><header className="admin-heading"><div><p className="admin-kicker">DIANA · FORSCHUNG</p><h1>Umfrageergebnisse</h1></div><button onClick={logout}><LogOut size={16}/>Abmelden</button></header>{error && <p className="admin-error" role="alert">{error}</p>}
 <AdminStudyControl study={study} busy={studyBusy} onToggle={toggleStudy}/>
 <section className="admin-overview"><div><strong>{data?.total??'…'}</strong><span>Teilnahmen in der Auswahl</span></div><div><strong>{data?.current_release?.openai_model??'…'}</strong><span>Aktueller Modellstand · Denkaufwand none</span></div></section>
 <section className="admin-export"><div><h2>Für Numiqo herunterladen</h2><p>Abgeschlossene und unvollständige Teilnahmen sind über den Statusfilter getrennt auswählbar. Eine Zeile pro Teilnahme · numerische Bewertungen · leere Zellen für fehlende Werte. Das Paket enthält zusätzlich Codebuch und Systemstände.</p><p className="admin-small">In Numiqo unter „Import/Export“ die CSV-Datei öffnen. Der Download berücksichtigt deine Filter.</p></div><div><button className="admin-primary" disabled={busy || !data} onClick={()=>download('csv')}><Download size={17}/>CSV für Numiqo</button><button disabled={busy || !data} onClick={()=>download('zip')}><Download size={17}/>Auswertungspaket</button></div></section>
 <form className="admin-filters" onSubmit={event=>{event.preventDefault();setFilter({q:query.trim(),version,status,arm,page:1});}}><label>Teilnahme-ID<input value={query} onChange={event=>setQuery(event.target.value)} maxLength={100} placeholder="ID suchen …"/></label><label>Fragebogen<select value={version} onChange={event=>setVersion(event.target.value)}><option value="">Alle Versionen</option><option value="diana-v6">v6 · Vergleich B/C</option><option value="diana-v5">v5 · Bewertungen 1–10</option><option value="diana-v4">v4 · passende Fragetypen</option><option value="diana-v3">v3 · 13 Bewertungen</option><option value="diana-v2">v2 · 9 Bewertungen</option><option value="diana-v1">v1 · erste Umfrage</option></select></label><label>Studienvariante<select value={arm} onChange={event=>setArm(event.target.value)}><option value="">Alle Varianten</option><option value="B">B · Neutraler Chatbot</option><option value="C">C · Personalisierter Bot</option></select></label><label>Status<select value={status} onChange={event=>setStatus(event.target.value)}><option value="">Alle Teilnahmen</option><option value="completed">Abgeschlossen</option><option value="in_progress">Unvollständig</option></select></label><button type="submit"><Search size={16}/>Filtern</button></form>
 <div className="admin-results"><section className="admin-table-section"><div className="admin-table-scroll"><table><thead><tr><th>Teilnahme-ID</th><th>Zuletzt gespeichert</th><th>Status</th><th>Fragebogen</th><th>Variante</th><th><span className="sr-only">Aktion</span></th></tr></thead><tbody>{data?.items.map(item=><tr key={item.id} className={row?.id===item.id?'is-selected':''}><td>{item.participation_id}</td><td>{new Date(item.last_saved_at_utc || item.submitted_at_utc).toLocaleString('de-DE')}</td><td>{item.response_status==='in_progress'?'Unvollständig':'Abgeschlossen'}</td><td>{item.survey_version}</td><td>{item.study_arm || "–"}</td><td><button onClick={()=>select(item)}>Ansehen</button></td></tr>)}</tbody></table></div>{data?.items.length===0 && <p className="admin-empty">Keine Antworten in dieser Auswahl.</p>}<nav className="admin-pagination" aria-label="Ergebnisseiten"><button disabled={filter.page<=1} onClick={()=>setFilter({...filter,page:filter.page-1})}>Zurück</button><span>Seite {filter.page} von {Math.max(1,Math.ceil((data?.total||0)/25))}</span><button disabled={!data || filter.page*25>=data.total} onClick={()=>setFilter({...filter,page:filter.page+1})}>Weiter</button></nav></section>{row && data && <AdminAnswerDetail row={row} definition={data.definition} onClose={()=>{selection.current++;setRow(null);}} onDelete={()=>{setDeleteError('');setDeleting(true);}}/>}</div>
 <p className="admin-footnote">Modellstände werden nur zugeordnet, wenn sie während der Teilnahme dokumentiert wurden. Bei älteren Antworten bleibt die Zuordnung leer.</p>
 </div>{deleting && row && <AdminDeleteDialog row={row} busy={busy} error={deleteError} onClose={()=>setDeleting(false)} onDelete={remove}/>}</main>;
}
