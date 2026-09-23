import React, {useState} from 'react';
import {BriefcaseBusiness} from 'lucide-react';
import {messagePreview} from './chat-layout.js';
import {jobReferenceParts, previewParts, separateFollowUp} from './chat-presentation.js';

export function RichChatText({text, jobs, onOpenJob, busy = false, streaming = false}) {
  const {body, question} = separateFollowUp(text);
  const render = value => jobReferenceParts(value, jobs).map((part, index) => part.job
    ? <button key={index} type="button" className="chat-job-reference" disabled={busy}
        title={`Stellendetails öffnen · ${part.job.company}`}
        aria-label={`Stelle öffnen: ${part.job.title} bei ${part.job.company}`}
        onClick={() => onOpenJob(part.job.id)}><BriefcaseBusiness size={14} aria-hidden="true"/>{part.text}</button>
    : <React.Fragment key={index}>{part.text}</React.Fragment>);
  return <div className={`message-text message-text--rich${streaming ? ' streaming-text' : ''}`}>
    {body && <p>{render(body)}</p>}{question && <p className="chat-follow-up">{render(question)}</p>}
  </div>;
}

export default function ChatMessageText({text, assistant, enhanced = false, jobs = [], onOpenJob, busy = false}) {
  const [expanded, setExpanded] = useState(false);
  if (!assistant || !enhanced) {
    const preview = assistant ? messagePreview(text) : text;
    return <div className="message-bubble"><div className="message-text">{expanded ? text : preview}</div>{preview !== text && <button type="button" className="message-expand" aria-expanded={expanded} onClick={() => setExpanded(!expanded)}>{expanded ? 'Weniger anzeigen' : 'Mehr anzeigen'}</button>}</div>;
  }
  const {body, question} = separateFollowUp(text);
  const parts = jobReferenceParts(body, jobs);
  const preview = previewParts(parts);
  const render = items => items.map((part, index) => part.job
    ? <button key={index} type="button" className="chat-job-reference" disabled={busy}
        title={`Stellendetails öffnen · ${part.job.company}`}
        aria-label={`Stelle öffnen: ${part.job.title} bei ${part.job.company}`}
        onClick={() => onOpenJob(part.job.id)}><BriefcaseBusiness size={14} aria-hidden="true"/>{part.text}</button>
    : <React.Fragment key={index}>{part.text}</React.Fragment>);
  return <div className="message-bubble"><div className="message-text message-text--rich">
    {body && <p>{render(expanded ? parts : preview)}</p>}
    {preview !== parts && <button type="button" className="message-expand" aria-expanded={expanded} onClick={() => setExpanded(!expanded)}>{expanded ? 'Weniger anzeigen' : 'Mehr anzeigen'}</button>}
    {question && <p className="chat-follow-up">{render(jobReferenceParts(question, jobs))}</p>}
  </div></div>;
}
