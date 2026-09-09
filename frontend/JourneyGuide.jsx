import React from 'react';
import { BriefcaseBusiness, Check, Compass, MessagesSquare, UserRound } from 'lucide-react';
import './journey.css';
import './header-journey.css';
import { canVisitJourneyStep } from './journey-state.js';

const steps = [
  { number: 1, title: 'Profil erstellen', shortTitle: 'Profil', Icon: UserRound, description: 'Suchziel, Fähigkeiten und Wünsche eintragen.' },
  { number: 2, title: 'Persönlichkeit festlegen', shortTitle: 'Persönlichkeit', Icon: Compass, description: 'Wähle die Perspektive für deine Empfehlungen.' },
  { number: 3, title: 'Ergebnisse ansehen', shortTitle: 'Ergebnisse', Icon: BriefcaseBusiness, description: 'Passung und Begründungen vergleichen.' },
  { number: 4, title: 'Besprechen & verfeinern', shortTitle: 'Chat & Suche', Icon: MessagesSquare, description: 'Fragen stellen und deine Suche anpassen.' },
];

export default function JourneyGuide({ activeStep = 1, completedSteps = [], compact = false, iconOnly = false, busy = false, hasSession = false, onSelect }) {
  return <nav className={`journey-guide ${iconOnly ? 'journey-guide--icons' : compact ? 'journey-guide--compact' : 'journey-guide--expanded'}`} aria-label="Schritte deiner Jobsuche" aria-busy={busy}>
    <ol className="journey-list" role="list">
      {steps.map(({ number, title, shortTitle, Icon, description }) => {
        const active = activeStep === number;
        const complete = completedSteps.includes(number);
        const locked = !canVisitJourneyStep(number, { hasSession, activeStep });
        const accessibleLabel = `Schritt ${number}: ${title}${active ? ', aktuell' : ''}${complete ? ', bereits erledigt' : ''}${locked ? ', zuerst den aktuellen Schritt fortsetzen' : ''}`;
        return <li className="journey-item" key={number}>
          <button type="button" className={`journey-step journey-step--${number}${active ? ' is-current' : ''}${complete ? ' is-complete' : ''}`} aria-label={accessibleLabel} title={iconOnly ? accessibleLabel : undefined} aria-current={active ? 'step' : undefined} disabled={busy || locked} onClick={() => onSelect?.(number)}>
            <span className="journey-step-heading">
              <span className="journey-step-number"><span className="journey-sr-only">Schritt </span>{number}</span>
              <Icon className="journey-step-icon" size={23} strokeWidth={1.6} aria-hidden="true" />
              {iconOnly ? complete && <Check className="journey-header-check" size={11} strokeWidth={2.5} aria-hidden="true" /> : <>
                {active && <span className="journey-current">{complete && <Check className="journey-complete-check" size={11} aria-hidden="true" />}Aktuell</span>}
                {complete && !active && <span className="journey-complete"><Check size={11} aria-hidden="true" />Erledigt</span>}
              </>}
            </span>
            {!iconOnly && <><strong className="journey-step-title"><span className="journey-full-title">{title}</span>{compact && <span className="journey-short-title">{shortTitle}</span>}</strong>
              {!compact && <span className="journey-step-description">{description}</span>}
            </>}
          </button>
        </li>;
      })}
    </ol>
  </nav>;
}
