import React,{useEffect,useState} from 'react';
import './raffle.css';

export default function AdminRaffle({request,csrf}){
 const [data,setData]=useState(null),[busy,setBusy]=useState(false),[error,setError]=useState('');
 const [email,setEmail]=useState(''),[confirmation,setConfirmation]=useState('');
 useEffect(()=>{let active=true;request('/raffle').then(value=>{if(active)setData(value);}).catch(failure=>{if(active)setError(failure.message);});return()=>{active=false;};},[request]);
 async function change(method,body){
  if(busy)return;setBusy(true);setError('');
  try{setData(await request('/raffle',{method,headers:{'Content-Type':'application/json','X-CSRF-Token':csrf},body:JSON.stringify(body)}));setEmail('');setConfirmation('');}
  catch(failure){setError(failure.message);}finally{setBusy(false);}
 }
 async function download(){
  if(busy)return;setBusy(true);setError('');
  try{
   const response=await fetch('/api/admin/raffle/export');
   if(!response.ok)throw new Error('Download fehlgeschlagen. Bitte prüfe deine Anmeldung.');
   const url=URL.createObjectURL(await response.blob()),link=document.createElement('a');
   link.href=url;link.download='diana_gewinnspiel_email.csv';link.click();setTimeout(()=>URL.revokeObjectURL(url),1000);
  }catch(failure){setError(failure.message);}finally{setBusy(false);}
 }
 return <section className="admin-raffle" aria-label="Gewinnspielverwaltung"><h2>Gewinnspiel</h2><p>Die E-Mail-Adressen liegen in einer eigenen Datenbank. Es gibt keine gemeinsame Kennung mit Umfrageantworten und keine Zuordnung zu A, B oder C. Die Umfragefilter gelten hier nicht.</p>
  {error&&<p role="alert" className="admin-error">{error}</p>}
  {!data?<p role="status">Wird geladen …</p>:<><p><strong>{data.count} E-Mail-Adressen</strong> · Anmeldung {data.enabled?'geöffnet':'geschlossen'}</p>
  <div className="admin-raffle-actions"><button disabled={busy} onClick={download}>E-Mail-Adressen als CSV</button><button disabled={busy} onClick={()=>change('PUT',{enabled:!data.enabled})}>{data.enabled?'Anmeldung schließen':'Anmeldung öffnen'}</button></div>
  <details><summary>Eine Gewinnspieladresse löschen</summary><form onSubmit={event=>{event.preventDefault();void change('DELETE',{email});}}><label>E-Mail-Adresse<input type="email" required maxLength={254} value={email} onChange={event=>setEmail(event.target.value)} disabled={busy}/></label><button className="admin-danger" disabled={busy||!email}>Adresse löschen</button></form></details>
  <details><summary>Nach Abschluss: alle Gewinnspieladressen löschen</summary><p>Schließt die Anmeldung und löscht alle Adressen aus der Gewinnspieldatenbank. Umfrageantworten bleiben erhalten. Heruntergeladene CSV-Dateien und Sicherungen separat bereinigen.</p><label>Zur Bestätigung ALLE GEWINNSPIELADRESSEN LÖSCHEN eingeben<input value={confirmation} onChange={event=>setConfirmation(event.target.value)} disabled={busy}/></label><button className="admin-danger" disabled={busy||confirmation!=='ALLE GEWINNSPIELADRESSEN LÖSCHEN'} onClick={()=>change('DELETE',{confirmation})}>Gewinnspieladressen endgültig löschen</button></details></>}
 </section>;
}
