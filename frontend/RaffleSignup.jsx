import React, {useEffect, useRef, useState} from 'react';
import {Gift, X} from 'lucide-react';
import {consentHeaders} from './privacy.js';
import './raffle.css';

export default function RaffleSignup() {
  const [open,setOpen]=useState(false),[status,setStatus]=useState(null);
  const [email,setEmail]=useState(''),[accepted,setAccepted]=useState(false);
  const [busy,setBusy]=useState(false),[error,setError]=useState('');
  const dialog=useRef(null),sending=useRef(false);
  useEffect(()=>{
    if(!open)return;
    const controller=new AbortController();
    dialog.current.showModal();setError('');setStatus(null);
    fetch('/api/raffle',{headers:consentHeaders(),signal:controller.signal}).then(async response=>{
      const data=await response.json();
      if(!response.ok)throw new Error('Die Gewinnspiel-Anmeldung konnte nicht geladen werden. Bitte versuche es erneut.');
      setStatus(data);
    }).catch(failure=>{if(failure.name!=='AbortError')setError(failure.message);});
    return()=>controller.abort();
  },[open]);
  function close(){if(!sending.current){setOpen(false);setEmail('');setAccepted(false);}}
  async function submit(event){
    event.preventDefault();
    if(sending.current || !status?.eligible || !accepted)return;
    sending.current=true;setBusy(true);setError('');
    try{
      const response=await fetch('/api/raffle',{method:'POST',headers:{...consentHeaders(),'Content-Type':'application/json'},body:JSON.stringify({email,accepted,notice_version:status.notice_version})});
      const data=await response.json();
      if(!response.ok || !data.registered)throw new Error(data.error?.message || 'Die Anmeldung konnte nicht gespeichert werden.');
      setStatus(previous=>({...previous,registered:true}));setEmail('');setAccepted(false);
    }catch(failure){setError(failure instanceof TypeError?'Die Verbindung wurde unterbrochen. Du kannst die Anmeldung erneut senden.':failure.message);}
    finally{sending.current=false;setBusy(false);}
  }
  return <><button type="button" className="raffle-open" onClick={()=>setOpen(true)}><Gift size={17} aria-hidden="true"/>Am Gewinnspiel teilnehmen</button>{open&&<dialog className="raffle-dialog" ref={dialog} aria-labelledby="raffle-title" onCancel={event=>{event.preventDefault();close();}}>
    <div className="raffle-heading"><h2 id="raffle-title">Am Gewinnspiel teilnehmen</h2><button type="button" aria-label="Gewinnspiel schließen" onClick={close} disabled={busy}><X size={20}/></button></div>
    {error&&<p className="raffle-error" role="alert">{error}</p>}
    {!status&&!error&&<p role="status">Anmeldung wird vorbereitet …</p>}
    {status?.registered?<><p role="status">Du bist für das Gewinnspiel eingetragen. Viel Glück!</p><p>Bei einem Gewinn melden wir uns per E-Mail.</p><button type="button" className="survey-primary" onClick={close}>Schließen</button></>:status&&!status.eligible?<p>Die Anmeldung ist nach einer vollständig abgeschlossenen Umfrage möglich.</p>:status&&!status.enabled?<p>Die Anmeldung zum Gewinnspiel ist geschlossen.</p>:status&&<form onSubmit={submit}>
      <p>Trage deine E-Mail-Adresse ein, damit wir dich im Gewinnfall erreichen können.</p>
      <label className="raffle-email">E-Mail-Adresse<input type="email" name="raffle_email" autoComplete="email" inputMode="email" required maxLength={254} value={email} onChange={event=>setEmail(event.target.value)} disabled={busy} placeholder="name@beispiel.de"/></label>
      <p className="raffle-separation">Deine E-Mail-Adresse wird getrennt von deinen Umfrageantworten und ohne Teilnahme-ID gespeichert.</p>
      <details><summary>Hinweise zum Gewinnspiel und Datenschutz</summary><p>{status.notice_text}</p><p>Kontakt: <a href="mailto:christoph.scharnagl@th-nuernberg.de">christoph.scharnagl@th-nuernberg.de</a></p></details>
      <label className="raffle-consent"><input type="checkbox" required checked={accepted} onChange={event=>setAccepted(event.target.checked)} disabled={busy}/><span>Ich habe die Hinweise gelesen und willige freiwillig ein, dass meine E-Mail-Adresse für das Gewinnspiel verwendet wird.</span></label>
      <div className="raffle-actions"><button type="button" onClick={close} disabled={busy}>Abbrechen</button><button type="submit" className="survey-primary" disabled={busy||!accepted}>{busy?'Wird gespeichert …':'Teilnahme bestätigen'}</button></div>
    </form>}
  </dialog>}</>;
}
