import React, { useEffect, useId, useRef, useState } from 'react';
import { ArrowRight, GraduationCap, BriefcaseBusiness, Lightbulb, Search, Check, RotateCcw, Database, UserRound, ListFilter, PanelsTopLeft } from 'lucide-react';
import { createMemory, flipMemory } from './search-memory.js';
import { searchStatus } from './search-progress.js';
import './search-loading.css';

const memoryIcons = {study:GraduationCap, work:BriefcaseBusiness, idea:Lightbulb};
const phaseIcons = [Database, UserRound, Search, ListFilter, PanelsTopLeft];
const phaseNames = ['Stellendaten geladen', 'Suchprofil vorbereiten', 'Stellen durchsuchen', 'Vorauswahl abgleichen', 'Ergebnisse bereitstellen'];
const memoryNames = {study:'Studium', work:'Beruf', idea:'Idee'};

export function SearchLoadingArt() {
  const [game, setGame] = useState(createMemory);
  useEffect(() => {
    if (game.open.length !== 2) return;
    const timer = setTimeout(() => setGame(previous => ({...previous, open:[]})), 1000);
    return () => clearTimeout(timer);
  }, [game.open]);
  return <section className="search-memory" aria-label="Optionales Mini-Memory">
    <div className="search-memory-heading"><strong>Mini-Memory</strong><span aria-live="polite">{game.matched.length / 2}/3 Paare</span><button type="button" className="search-memory-again" aria-label="Memory neu starten" title="Neue Runde" onClick={() => setGame(createMemory())}><RotateCcw size={17} aria-hidden="true"/></button></div>
    <span className="sr-only">Finde die gleichen Symbole. Das Spiel hat keinen Einfluss auf deine Suche.</span>
    <div className="search-memory-cards">
      {game.cards.map((kind, index) => {
        const matched = game.matched.includes(index);
        const shown = matched || game.open.includes(index);
        const Icon = shown ? memoryIcons[kind] : Search;
        return <button key={index} type="button" className={`search-memory-card${shown ? ' is-open' : ''}${matched ? ' is-matched' : ''}`}
          aria-label={`Karte ${index + 1}: ${shown ? memoryNames[kind] + (matched ? ', Paar gefunden' : '') : 'aufdecken'}`}
          aria-disabled={matched || shown || game.open.length === 2}
          onClick={() => setGame(previous => flipMemory(previous, index))}>
          <Icon size={25} aria-hidden="true" />{matched && <Check className="memory-check" size={13} aria-hidden="true" />}
        </button>;
      })}
    </div>
  </section>;
}

export default function SearchLoadingDialog({ open, assistantName = 'DIANA-KI', onQuestions, progress }) {
  const dialog = useRef(null);
  const heading = useRef(null);
  const id = useId();
  const status = searchStatus(progress);

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
    <h2 ref={heading} id={`${id}-title`} tabIndex={-1}>{assistantName} sucht passende Stellen</h2>
    <span id={`${id}-description`} className="sr-only" role="status" aria-live="polite" aria-atomic="true">{status.title}. {status.description}</span>
    <div className="search-phase-progress"><ol className="search-phase-steps" aria-label="Suchfortschritt">
      {phaseNames.map((label, index) => {
        const Icon = phaseIcons[index];
        const state = index < status.index ? 'abgeschlossen' : index === status.index ? 'aktuell' : 'ausstehend';
        return <li key={label} className={index < status.index ? 'is-done' : index === status.index ? 'is-active' : ''} aria-current={index === status.index ? 'step' : undefined} title={`${label} · ${state}`}>
          <Icon size={22} aria-hidden="true"/>{index < status.index && <Check className="search-phase-check" size={12} aria-hidden="true"/>}
          <span className="sr-only">{label}: {state}</span>
        </li>;
      })}
    </ol><div className="search-loading-track" aria-hidden="true"><i /></div></div>
    {open && <SearchLoadingArt />}
    {onQuestions && <button className="survey-primary diana-action-motion search-loading-questions" type="button" onClick={onQuestions}>Fragen in der Zwischenzeit beantworten<ArrowRight className="diana-action-arrow" size={18}/></button>}
  </dialog>;
}
