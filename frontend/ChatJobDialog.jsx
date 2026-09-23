import React,{useEffect,useRef} from 'react';
import './chat-job-dialog.css';

export default function ChatJobDialog({onClose,children}) {
  const dialog=useRef(null);
  useEffect(()=>{dialog.current.showModal();},[]);
  return <dialog ref={dialog} className="chat-job-dialog" aria-label="Stelle aus dem bisherigen Gespräch" onCancel={event=>{event.preventDefault();onClose();}}>
    <header><span>Stelle aus dem bisherigen Gespräch</span><button type="button" onClick={onClose}>Schließen</button></header>
    <p>Diese Anzeige gehört zu einer früheren Auswahl. Deine aktuelle Ergebnisliste bleibt bestehen.</p>
    {children}
  </dialog>;
}
