import React, { useEffect, useId, useRef } from 'react';
import { BriefcaseBusiness, Clock3, Search } from 'lucide-react';
import './search-loading.css';

export default function SearchLoadingDialog({ open, elapsed = 0, assistantName = 'DIANA-KI', onDismiss }) {
  const dialog = useRef(null);
  const heading = useRef(null);
  const id = useId();
  const seconds = Math.max(0, Number.isFinite(elapsed) ? Math.floor(elapsed) : 0);
  const elapsedLabel = seconds < 60 ? `${seconds} Sek.` : `${Math.floor(seconds / 60)} Min. ${seconds % 60} Sek.`;

  useEffect(() => {
    const element = dialog.current;
    if (!element) return;
    if (open && !element.open) {
      element.showModal();
      heading.current?.focus({ preventScroll: true });
    } else if (!open && element.open) {
      element.close();
    }
    return () => { if (element.open) element.close(); };
  }, [open]);

  function dismiss() {
    dialog.current?.close();
    onDismiss?.();
  }

  return <dialog ref={dialog} className="search-loading-dialog" aria-labelledby={`${id}-title`} aria-describedby={`${id}-description`} onCancel={event => { event.preventDefault(); dismiss(); }}>
    <div className="search-loading-art" aria-hidden="true">
      <div className="search-loading-halo" />
      <div className="search-loading-card search-loading-card--back"><span className="search-loading-card-icon"><BriefcaseBusiness size={18} strokeWidth={1.6} /></span><i /><i /><i /></div>
      <div className="search-loading-card search-loading-card--front"><span className="search-loading-card-icon"><BriefcaseBusiness size={18} strokeWidth={1.6} /></span><i /><i /><i /></div>
      <span className="search-loading-lens"><Search size={23} strokeWidth={1.7} /></span>
      <span className="search-loading-dots"><i /><i /><i /></span>
    </div>
    <h2 ref={heading} id={`${id}-title`} tabIndex={-1}>{assistantName} sucht passende Stellen</h2>
    <p id={`${id}-description`} className="search-loading-description">Die Suche und persönliche Bewertung dauern meist etwa eine Minute. Manchmal dauert es etwas länger.</p>
    <p className="search-loading-elapsed" aria-live="off"><Clock3 size={16} aria-hidden="true" /><span>Bisher: {elapsedLabel}</span></p>
    {seconds >= 90 && <p className="search-loading-patience" role="status">Die Suche läuft weiter. Du kannst sie auch im Hintergrund weiterlaufen lassen.</p>}
    <button type="button" className="search-loading-dismiss" onClick={dismiss}>Im Hintergrund weiterlaufen lassen</button>
  </dialog>;
}
