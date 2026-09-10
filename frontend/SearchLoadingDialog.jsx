import React, { useEffect, useId, useRef } from 'react';
import { BriefcaseBusiness, Search } from 'lucide-react';
import './search-loading.css';

export default function SearchLoadingDialog({ open, assistantName = 'DIANA-KI' }) {
  const dialog = useRef(null);
  const heading = useRef(null);
  const id = useId();

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

  return <dialog ref={dialog} className="search-loading-dialog" aria-labelledby={`${id}-title`} aria-describedby={`${id}-description`} onCancel={event => event.preventDefault()}>
    <div className="search-loading-art" aria-hidden="true">
      <div className="search-loading-halo" />
      <div className="search-loading-card search-loading-card--back"><span className="search-loading-card-icon"><BriefcaseBusiness size={18} strokeWidth={1.6} /></span><i /><i /><i /></div>
      <div className="search-loading-card search-loading-card--front"><span className="search-loading-card-icon"><BriefcaseBusiness size={18} strokeWidth={1.6} /></span><i /><i /><i /></div>
      <span className="search-loading-lens"><Search size={23} strokeWidth={1.7} /></span>
      <span className="search-loading-dots"><i /><i /><i /></span>
    </div>
    <h2 ref={heading} id={`${id}-title`} tabIndex={-1}>{assistantName} sucht passende Stellen</h2>
    <p id={`${id}-description`} className="search-loading-description">Deine Stellen werden gesucht und persönlich bewertet. Das kann bis zu zwei Minuten dauern.</p>
    <div className="search-loading-track" role="status"><span className="sr-only">Suche und Bewertung laufen.</span><i aria-hidden="true" /></div>
  </dialog>;
}
