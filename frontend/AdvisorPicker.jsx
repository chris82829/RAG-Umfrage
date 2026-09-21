import React, { useId } from 'react';
import { Check, Info } from 'lucide-react';
import { ADVISOR_DESCRIPTION_MAX_LENGTH, editableAdvisor, traitLabels } from './advisor.js';
import './advisor-picker.css';
import {templateSelection} from './advisor-selection.js';

export default function AdvisorPicker({ value, onChange, disabled, headingRef, onExplain }) {
  const draft = {...editableAdvisor(value), focus: 'ausgewogen'};
  const id = useId();
  const update = (key, item) => onChange({ ...draft, [key]: item }, templateSelection(''));
  return <section className="advisor-picker advisor-builder" aria-label="Deine Suchpersönlichkeit">
    <div className="advisor-intro profile-intro profile-intro--compact"><span className="step-label">DEINE SUCHPERSÖNLICHKEIT</span><div className="advisor-intro-heading"><div className="advisor-title"><h3 ref={headingRef} tabIndex={-1}>KI-Suchpersönlichkeit</h3><button type="button" className="advisor-help" onClick={onExplain} disabled={disabled} aria-label="Wie beeinflusst das meine Suche?" title="Wie beeinflusst das meine Suche?" aria-haspopup="dialog"><Info size={16} aria-hidden="true" /></button></div>
    </div></div>
    <p className="advisor-role-hint">Gestalte, wie deine KI mit dir spricht und Empfehlungen erklärt. Die Suche bleibt ausgewogen.</p>
    <div className="advisor-custom">
      <label className="advisor-name-field" htmlFor={`${id}-name`}><span>Name deiner KI</span><input id={`${id}-name`} required maxLength={60} value={draft.name} onChange={e => update('name', e.target.value)} disabled={disabled} placeholder="Name eingeben" aria-describedby={`${id}-name-hint`} /><span className="sr-only" id={`${id}-name-hint`}>Dieser Name steht im Chat und an deinem persönlichen Score.</span></label>
      <fieldset disabled={disabled} aria-describedby={`${id}-traits-hint`}><legend>Wie soll deine KI mit dir sprechen?</legend><div className="choice-group">{Object.entries(traitLabels).map(([key, label]) => <label className={`choice ${draft.traits.includes(key) ? 'selected' : ''}`} key={key}><input type="checkbox" checked={draft.traits.includes(key)} disabled={!draft.traits.includes(key) && draft.traits.length >= 4} onChange={() => update('traits', draft.traits.includes(key) ? draft.traits.filter(x => x !== key) : [...draft.traits, key])} />{draft.traits.includes(key) && <Check size={13} aria-hidden="true" />}{label}</label>)}</div><p className="field-hint" id={`${id}-traits-hint`}>Wähle 1 bis 4 Eigenschaften für Ton und Erklärungen.</p></fieldset>
      <label htmlFor={`${id}-description`}><span>Eigene Hinweise <span className="optional">optional</span></span><textarea id={`${id}-description`} rows={3} maxLength={ADVISOR_DESCRIPTION_MAX_LENGTH} value={draft.description} onChange={e => update('description', e.target.value)} disabled={disabled} placeholder="Weitere Wünsche zum Gesprächsstil und zu den Begründungen" aria-describedby={`${id}-description-hint`} /><span className="field-hint" id={`${id}-description-hint`}>Für Gesprächsstil und Begründungen. Deine Jobwünsche gehören ins Suchprofil. {draft.description.length}/{ADVISOR_DESCRIPTION_MAX_LENGTH}</span></label>
    </div>
  </section>;
}
