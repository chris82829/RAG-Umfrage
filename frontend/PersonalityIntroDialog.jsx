import React, { useEffect, useId, useRef } from 'react';
import { ArrowDown, ArrowDownWideNarrow, ArrowRight, Compass, MessagesSquare, X } from 'lucide-react';
import './personality-intro.css';

export default function PersonalityIntroDialog({ open, onboarding = false, onContinue, onClose }) {
  const dialog = useRef(null);
  const heading = useRef(null);
  const id = useId();
  useEffect(() => {
    const element = dialog.current;
    if (open && !element.open) {
      element.showModal();
      heading.current?.focus({ preventScroll: true });
    } else if (!open && element.open) element.close();
    return () => { if (element.open) element.close(); };
  }, [open]);
  function closeThen(callback) {
    dialog.current?.close();
    callback?.();
  }
  return <dialog ref={dialog} className="personality-intro-dialog" aria-labelledby={`${id}-title`} aria-describedby={`${id}-description`} onCancel={event => { event.preventDefault(); closeThen(onClose); }}>
    <button type="button" className="personality-intro-close" aria-label="Erklärung schließen" onClick={() => closeThen(onClose)}><X size={19} aria-hidden="true" /></button>
    <h2 ref={heading} id={`${id}-title`} tabIndex={-1}>KI-Suchpersönlichkeit</h2>
    <p id={`${id}-description`} className="personality-intro-description">Dein Profil beschreibt, was zu dir passt. Du gestaltest, wie deine KI mit dir spricht und Empfehlungen erklärt. Die Suche bleibt ausgewogen; die fachliche Passung zählt am stärksten.</p>
    <div className="personality-flow">
      <div className="personality-flow-source"><Compass size={22} aria-hidden="true" /><span>KI-Suchpersönlichkeit</span></div>
      <div className="personality-flow-branches" aria-hidden="true"><ArrowDown size={19} /><ArrowDown size={19} /></div>
      <div className="personality-effects">
      <section className="personality-effect personality-effect-search">
        <span className="personality-effect-icon"><ArrowDownWideNarrow size={22} aria-hidden="true" /></span>
        <div><h3>Ausgewogen suchen</h3><p>Dein Profil und deine Jobwünsche bestimmen die Passung. Die Gewichtung bleibt ausgewogen, unabhängig von den gewählten Gesprächseigenschaften.</p></div>
      </section>
      <section className="personality-effect personality-effect-chat">
        <span className="personality-effect-icon"><MessagesSquare size={22} aria-hidden="true" /></span>
        <div><h3>Mit dir sprechen</h3><p>Die gewählte Persönlichkeit bestimmt, wie die KI antwortet und ihre Empfehlungen erklärt.</p></div>
      </section>
      </div>
    </div>
    <button type="button" className={`personality-intro-continue${onboarding ? ' diana-action-motion' : ''}`} onClick={() => closeThen(onContinue)}>{onboarding ? 'Persönlichkeit gestalten' : 'Verstanden'}<ArrowRight className="diana-action-arrow" size={17} aria-hidden="true" /></button>
  </dialog>;
}
