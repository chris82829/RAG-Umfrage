import React, { useEffect, useId, useRef, useState } from 'react';
import { ArrowRight } from 'lucide-react';
import './search-loading.css';

export function SearchLoadingArt() {
  const [boost, setBoost] = useState(false);
  const timer = useRef(null);
  useEffect(() => () => clearTimeout(timer.current), []);
  function launch() {
    clearTimeout(timer.current);
    setBoost(true);
    timer.current = setTimeout(() => setBoost(false), 1100);
  }
  function follow(event) {
    if (event.pointerType !== 'mouse' || window.matchMedia('(prefers-reduced-motion: reduce)').matches) return;
    const box = event.currentTarget.getBoundingClientRect();
    event.currentTarget.style.setProperty('--flight-x', `${((event.clientX - box.left) / box.width - .5) * 16}px`);
    event.currentTarget.style.setProperty('--flight-y', `${((event.clientY - box.top) / box.height - .5) * 10}px`);
  }
  function center(event) {
    event.currentTarget.style.setProperty('--flight-x', '0px');
    event.currentTarget.style.setProperty('--flight-y', '0px');
  }
  return <button type="button" className={`search-loading-art search-flight${boost ? ' is-boosting' : ''}`} aria-label="Fluganimation kurz beschleunigen" title="Tippen für Schub – nur die Animation wird beschleunigt" onClick={launch} onPointerMove={follow} onPointerLeave={center}>
    <svg className="search-flight-scene" viewBox="0 0 300 134" fill="none" aria-hidden="true">
      <ellipse cx="151" cy="64" rx="128" ry="58" fill="#e9f7fc"/>
      <g className="flight-cloud flight-cloud--one" fill="#fff"><ellipse cx="45" cy="39" rx="18" ry="8"/><circle cx="43" cy="33" r="9"/><circle cx="54" cy="36" r="7"/></g>
      <g className="flight-cloud flight-cloud--two" fill="#fff"><ellipse cx="253" cy="90" rx="21" ry="8"/><circle cx="248" cy="84" r="9"/><circle cx="261" cy="86" r="6"/></g>
      <g className="flight-job-cards">
        <g transform="translate(247 60) rotate(9)"><rect width="29" height="39" rx="5" fill="white" stroke="#bbd8ed"/><path d="M11 9V7h7v2m-10 0h13v9H8z" stroke="#5087b5" strokeWidth="1.4" strokeLinejoin="round"/><path d="M8 25h13m-13 5h9" stroke="#c3dbec" strokeWidth="2" strokeLinecap="round"/></g>
        <g transform="translate(43 16) rotate(-10)"><rect width="25" height="33" rx="5" fill="white" stroke="#c4ddef"/><path d="M9 9V7h6v2m-9 0h12v8H6z" stroke="#6a9cbf" strokeWidth="1.3" strokeLinejoin="round"/><path d="M7 23h11m-11 4h7" stroke="#c3dbec" strokeWidth="2" strokeLinecap="round"/></g>
      </g>
      <g className="flight-streaks" stroke="#91c6e2" strokeWidth="2.5" strokeLinecap="round"><path d="M36 73h23M27 87h17M228 30h21"/><path d="M240 113h15"/></g>
      <g className="flight-parallax"><g className="flight-pilot">
        <g className="flight-flame"><path d="M104 71C84 72 66 85 60 96c18 0 35-5 49-16z" fill="#ffb44c"/><path d="M105 74C91 77 82 84 77 89c13-1 22-4 31-10z" fill="#ffe5a1"/></g>
        <path d="M116 70l-11 23-39 7-10-8 34-17 9-20z" fill="#234877"/>
        <path d="M130 76l-15 31-42 4-9-9 34-14 8-25z" fill="#315c8b"/>
        <path d="M65 94l7 13-11 7c-7 3-13-1-12-7zM76 104l4 10-15 7c-6 1-10-2-9-6z" fill="#173553"/>
        <path d="M113 53c17-4 39 2 51 12l-18 32c-16-2-31-9-43-20z" fill="#fff"/>
        <path d="M131 64l22 11-8 19c-12-2-23-6-32-12z" fill="#ddebf6"/>
        <path d="M146 69l12 12 38-19 22-14-7-12-31 13-22 3z" fill="#dbeafa"/>
        <path d="M207 37l7-7c4-5 10-5 13-1l8 7c4 4 3 10-2 13l-11 4-12-6z" fill="#ffb89f"/>
        <path d="M225 34l-9 12" stroke="#254f7c" strokeWidth="5" strokeLinecap="round"/>
        <circle cx="232" cy="25" r="12" fill="#d1f1fb" fillOpacity=".9" stroke="#326f9e" strokeWidth="3"/>
        <path d="M227 22c1-3 4-4 7-3" stroke="white" strokeWidth="2.5" strokeLinecap="round"/>
        <path d="M115 66L91 56l-7-21 13-14 29 15 6 21z" fill="#326f9e"/>
        <path d="M96 57L83 62l-9-7 9-18z" fill="#184777"/>
        <path d="M99 25l15-9 17 17-2 23-13 7z" fill="#eaf4ff"/>
        <path d="M120 29l9 4-1 18-8 6z" fill="#285b88"/>
        <circle cx="102" cy="44" r="4" fill="#8bc7e9"/>
        <path d="M96 65l8 14-10 9-10-15z" fill="#ef7b68"/>
        <path d="M161 49l-7 17-11-5 6-18z" fill="#f5a58f"/>
        <path d="M153 26c11-7 25-4 30 9l-1 19c-3 10-16 13-25 5-10-9-11-23-4-33z" fill="#ffc5ac"/>
        <path d="M150 46c-10-5-14-17-7-27 8-13 27-15 37-4 6-3 11-1 10 4-1 9-10 16-23 16l-5 14-6 1z" fill="#214c79"/>
        <path d="M143 13l20-9 25 10-22 10z" fill="#326f9e"/>
        <path d="M150 18v8c8 5 17 6 24 1v-7l-8 4z" fill="#254f7c"/>
        <path d="M164 14l-20 2-2 14" stroke="#f5bd69" strokeWidth="1.5" strokeLinecap="round"/>
        <path d="M151 44c-7-4-9 7-2 10l7-1" fill="#ffc5ac"/>
        <path d="M175 42v4" stroke="#254562" strokeWidth="3" strokeLinecap="round"/>
        <path d="M171 52c3 4 7 4 9 0" stroke="#ce746c" strokeWidth="2" strokeLinecap="round"/>
        <path d="M139 70l-12 19 15 15 10-7-10-12 8-13z" fill="#eaf2fb"/>
        <g transform="translate(145 82) rotate(15)"><rect x="-2" y="-2" width="27" height="33" rx="4" fill="#527eb4"/><rect width="21" height="28" rx="2" fill="white"/><circle cx="7" cy="7" r="2.5" fill="#9db8d8"/><path d="M4 13c1-4 5-4 6 0" fill="#9db8d8"/><path d="M13 7h4M13 11h4M4 18h13M4 22h10" stroke="#c5d7ea" strokeWidth="1.5" strokeLinecap="round"/></g>
        <path d="M141 100c-2 5 1 10 6 12l7 3c6 1 11-5 8-10l-8-9-7-1z" fill="#ffb89f"/>
        <path d="M133 56l11 7 10 2" stroke="#ec826e" strokeWidth="5" strokeLinecap="round"/>
      </g></g>
      <g className="flight-stars" stroke="#7cadd5" strokeWidth="2" strokeLinecap="round"><path d="M242 52v8m-4-4h8M62 21v6m-3-3h6"/></g>
    </svg>
    <span className="search-flight-hint" aria-hidden="true">{boost ? '🚀' : 'Tippen für Schub'}</span>
  </button>;
}

export default function SearchLoadingDialog({ open, assistantName = 'DIANA-KI', onQuestions }) {
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
    <SearchLoadingArt />
    <h2 ref={heading} id={`${id}-title`} tabIndex={-1}>{assistantName} sucht passende Stellen</h2>
    <p id={`${id}-description`} className="search-loading-description">Deine Stellen werden gesucht und persönlich bewertet. Das kann bis zu zwei Minuten dauern.</p>
    {onQuestions && <button className="survey-primary diana-action-motion search-loading-questions" type="button" onClick={onQuestions}>Fragen in der Zwischenzeit beantworten<ArrowRight className="diana-action-arrow" size={18}/></button>}
    <div className="search-loading-track" role="status"><span className="sr-only">Suche und Bewertung laufen.</span><i aria-hidden="true" /></div>
  </dialog>;
}
