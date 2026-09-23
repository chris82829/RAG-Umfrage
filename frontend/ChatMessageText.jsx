import React, {useState} from 'react';
import {jobReferenceParts, plainJobReferences, separateFollowUp, removeChatGenderSuffixes, chatContentBlocks} from './chat-presentation.js';

function ChatBody({blocks, render}) {
  return blocks.map((block, index) => block.type === 'jobs'
    ? <ul className="chat-job-points" key={index}>{block.items.map((item, i) =>
      <li key={i}><div className="chat-job-title">{render(item.title)}</div>
        {item.description && <p className="chat-job-description">{render(item.description)}</p>}</li>)}</ul>
    : <p className="chat-paragraph" key={index}>{render(block.text)}</p>);
}

function renderReferences(value, jobs, onOpenJob, busy) {
  return jobReferenceParts(value, jobs).map((part, index) => part.job
    ? <button key={index} type="button" className="chat-job-reference" disabled={busy}
        title={`Stellendetails öffnen · ${part.job.company}`}
        aria-label={`Stelle öffnen: ${removeChatGenderSuffixes(part.job.title)} bei ${part.job.company}`}
        onClick={() => onOpenJob(part.job.id)}>{part.text}</button>
    : <React.Fragment key={index}>{part.text}</React.Fragment>);
}

export function RichChatText({text, jobs, onOpenJob, busy = false, streaming = false}) {
  const {body, question} = separateFollowUp(removeChatGenderSuffixes(text, streaming));
  const render = value => renderReferences(value, jobs, onOpenJob, busy);
  return <div className={`message-text message-text--rich${streaming ? ' streaming-text' : ''}`}>
    <ChatBody blocks={chatContentBlocks(body)} render={render} />
    {question && <p className="chat-follow-up">{render(question)}</p>}
  </div>;
}

export default function ChatMessageText({text, assistant, enhanced = false, jobs = [], references = [], onOpenJob, busy = false}) {
  const [expanded, setExpanded] = useState(false);
  if (!assistant) return <div className="message-bubble"><div className="message-text">{text}</div></div>;
  const displayText = removeChatGenderSuffixes(text);
  const {body, question} = separateFollowUp(displayText);
  const blocks = chatContentBlocks(body);
  // Collapse only complete blocks. Never replace part of a sentence with dots.
  const collapsible = displayText.length > 700 && blocks.length > 2;
  const linkedJobs = [...references, ...jobs.filter(job=>!references.some(ref=>String(ref.id)===String(job.id)))];
  const render = value => enhanced ? renderReferences(value, linkedJobs, onOpenJob, busy) : plainJobReferences(value, jobs);
  return <div className="message-bubble"><div className="message-text message-text--rich">
    <ChatBody blocks={collapsible && !expanded ? blocks.slice(0, 2) : blocks} render={render} />
    {collapsible && <button type="button" className="message-expand" aria-expanded={expanded} onClick={() => setExpanded(!expanded)}>{expanded ? 'Weniger anzeigen' : 'Mehr anzeigen'}</button>}
    {question && <p className="chat-follow-up">{render(question)}</p>}
  </div></div>;
}
