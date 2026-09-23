// Display-only cleanup. Original job data and user-authored messages stay intact.
export function removeChatGenderSuffixes(text, streaming = false) {
  const value = text.replace(/…|\.{3,}/g, '').replace(/[ \t]*\(\s*[mwfdx]\s*[/|]\s*[mwfdx]\s*[/|]\s*[mwfdx]\s*\)/gi, '');
  // Hold back an unfinished suffix at the stream boundary. A completed technical
  // parenthesis such as (Python) is never removed.
  return streaming ? value.replace(/[ \t]*\(\s*[mwfdx](?:\s*[/|]\s*(?:[mwfdx](?:\s*[/|]\s*[mwfdx]?)?)?)?\s*$/i, '') : value;
}

const internalJobReference = /\\*\[([^\]\n]+?)\\*\][ \t]*\\*\([ \t]*job[ \t]*:[ \t]*([^\s)\\]+)[ \t]*\\*\)/gi;

// Explicit ID labels do not belong in participant-facing answers, including
// invented IDs. Only supplied job records can create an interactive link.
// Plain numbers (scores, hours, dates, technologies) are never treated as IDs.
export function removeVisibleJobIds(text, jobs = [], {streaming = false} = {}) {
  const byId = new Map(jobs.map(job => [String(job.id ?? ''), job]));
  const ids = [...new Set(jobs.map(job => String(job.id ?? '')).filter(Boolean))]
    .sort((a, b) => b.length - a.length)
    .map(id => id.replace(/[.*+?^${}()|[\]\\]/g, '\\$&'));
  const numericId = '(?=[\\p{L}\\p{N}._-]*\\p{N})[\\p{L}\\p{N}](?:[\\p{L}\\p{N}._-]*[\\p{L}\\p{N}])?';
  const id = `(?:${[...ids, numericId].join('|')})(?![\\p{L}\\p{N}_-])`;
  const label = '(?:(?:Job|Stellen|Anzeigen)[ \\t‐‑–-]*ID|Stellenkennung|Jobkennung|Kennung|ID)';
  const marker = `(?<![\\p{L}\\p{N}_])(?:\\*\\*)?(?:${label}(?:\\*\\*)?[ \\t]*:?[ \\t]*#?[ \\t]*|#[ \\t]*)${id}(?:\\*\\*)?`;
  const wrapped = new RegExp(`[ \\t]*\\([ \\t]*${marker}[ \\t]*\\)`, 'giu');
  const bare = new RegExp(`[ \\t]*${marker}`, 'giu');
  const longIds = [...byId.keys()].filter(value => value.length >= 5 && /^[A-Za-z0-9_-]+$/.test(value))
    .sort((a, b) => b.length - a.length).map(value => value.replace(/[.*+?^${}()|[\]\\]/g, '\\$&'));
  const bareId = longIds.length ? new RegExp(`(?<![\\p{L}\\p{N}_.-])(${longIds.join('|')})(?![\\p{L}\\p{N}_-]|[.,]\\d)`, 'gu') : null;
  const streamTail = new RegExp(`[ \\t]*(?:\\([ \\t]*)?(?<![\\p{L}\\p{N}_])(?:\\*\\*)?(?:${label}|(?:Job|Stellen|Anzeigen)[ \\t‐‑–-]*I)(?:\\*\\*)?[ \\t]*:?[ \\t]*#?[ \\t]*[\\p{L}\\p{N}._-]*$|[ \\t]*(?:\\([ \\t]*)?#[ \\t]*[\\p{N}]*$`, 'iu');
  const clean = (value, final = false) => {
    if (streaming && final) value = value.replace(streamTail, '');
    let result = value.replace(wrapped, '').replace(bare, '');
    if (bareId) result = result.replace(bareId, (match, key, offset, source) => {
      if (/^[ \t]*(?:€|EUR\b|Euro\b|%|Stunden?\b|h\b|Std\.?\b)/i.test(source.slice(offset + match.length))) return match;
      const job = byId.get(key);
      const title = removeChatGenderSuffixes(job.title || 'diese Stelle').replace(/\[/g, '［').replace(/\]/g, '］');
      return `[${title}](job:${encodeURIComponent(key)})`;
    });
    return result === value ? value : result.replace(/[ \t]{2,}/g, ' ');
  };
  // Transport targets must survive intact, including a label that is itself an
  // identifier: a known reference is rendered using its canonical job title.
  let output = '', start = 0;
  for (const match of text.matchAll(internalJobReference)) {
    output += clean(text.slice(start, match.index)) + match[0];
    start = match.index + match[0].length;
  }
  return output + clean(text.slice(start), true);
}

export function jobDiscussionPrompt(job, {enhanced = false} = {}) {
  const title = enhanced ? removeChatGenderSuffixes(job.title) : job.title;
  const identifier = enhanced ? '' : ` (Job-ID ${job.id})`;
  return `Warum passt die Stelle „${title}“ bei ${job.company}${identifier} zu mir, und welche Kenntnisse fehlen noch?`.slice(0, 3000);
}

// Only references to supplied, server-grounded job records become interactive.
export function jobReferenceParts(text, jobs = [], {hideJobIds = true} = {}) {
  text = removeChatGenderSuffixes(text);
  if (hideJobIds) text = removeVisibleJobIds(text, jobs);
  const byId = new Map(jobs.map(job => [String(job.id), job]));
  // Models sometimes escape Markdown brackets/parentheses. Treat these as the
  // same internal reference; the UI renders a known title, never this markup.
  const references = [...text.matchAll(internalJobReference)];
  const names = new Map();
  for (const job of jobs) {
    const title = removeChatGenderSuffixes(job.title || '').replace(/\s+/g, ' ').trim();
    // Harmless shortening used in chat: retain the actual role and specialism.
    // Do not guess from a company name or use fuzzy matching for different jobs.
    const variants = new Set([title, title.replace(/\bim Bereich\s+/gi, '')]);
    for (const name of variants) {
      if (name.length < 5) continue;
      const key = name.toLocaleLowerCase('de');
      const existing = names.get(key);
      names.set(key, existing && existing.id !== job.id ? {ambiguous: true} : existing || job);
    }
  }
  const unique = [...names].filter(([, job]) => !job.ambiguous)
    .sort((a, b) => b[0].length - a[0].length)
    .map(([name, job]) => ({job, pattern: new RegExp(name.split(/\s+/)
      .map(word => word.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')).join('\\s+'), 'giu')}));
  const parts = [];
  function plain(value) {
    if (hideJobIds) value = value.replace(/\\*\[[ \t]*#?\d+[ \t]*(?:\\*\][ \t]*(?:\\*\((?:j(?:o(?:b(?::[^\n)]*)?)?)?)?\\*)?)?$/gi, 'diese Stelle');
    // Also recognize unambiguous titles in earlier messages without link markup.
    let rest = value.replace(/\*\*([^*]+)\*\*/g, '$1')
      // Suppress an unfinished internal target while its tokens are streaming.
      .replace(/\\*\[([^\]\n]+?)\\*\][ \t]*\\*\((?:j(?:o(?:b(?::[^\n)]*)?)?)?)?\\*$/gi, '$1')
      .replace(/\\*\[([^\]\n]+?)\\*\][ \t]*\\*$/g, '$1')
      .replace(/\\*\[([^\]\n]*)$/g, '$1')
      .replace(/\\*\([ \t]*job[ \t]*:[^\n)]*(?:\)|$)/gi, '')
      .replace(/\\([\[\]()])/g, '$1').replace(/\\+$/g, '');
    while (rest) {
      let next = null;
      for (const {pattern, job} of unique) {
        pattern.lastIndex = 0;
        for (const match of rest.matchAll(pattern)) {
          const index = match.index, length = match[0].length;
          if ((index > 0 && /[\p{L}\p{N}]/u.test(rest[index - 1]))
              || /[\p{L}\p{N}]/u.test(rest[index + length] || '')) continue;
          if (!next || index < next.index || (index === next.index && length > next.length))
            next = {index, length, job};
          break;
        }
      }
      if (!next) { parts.push({text: rest}); break; }
      if (next.index) parts.push({text: rest.slice(0, next.index)});
      parts.push({text: rest.slice(next.index, next.index + next.length), job: next.job});
      rest = rest.slice(next.index + next.length);
    }
  }
  let start = 0;
  for (const match of references) {
    plain(text.slice(start, match.index));
    let id;
    try { id = decodeURIComponent(match[2]); } catch { id = ''; }
    const job = byId.get(id);
    // Never navigate to a model-provided URL or invent a target for unknown IDs.
    const label = match[1].replace(/\*\*([^*]+)\*\*/g, '$1').replace(/\\([\[\]()])/g, '$1');
    let safeLabel = hideJobIds ? removeVisibleJobIds(label, jobs) : label;
    if (hideJobIds && (!safeLabel.trim() || /^#?\s*\d+$/.test(label.trim()) || label.trim().replace(/^#/, '') === id)) safeLabel = 'diese Stelle';
    parts.push(job ? {text: removeChatGenderSuffixes(job.title), job} : {text: safeLabel});
    start = match.index + match[0].length;
  }
  plain(text.slice(start));
  return parts;
}

export function separateFollowUp(text) {
  const value = text.replace(/\*\*([^*]+)\*\*/g, '$1').trim();
  if (!value.endsWith('?')) return {body: value, question: ''};
  // Job-title punctuation belongs to a title, not to a sentence boundary.
  const masked = value.replace(/\[[^\]\n]+\]\(job:[^)]+\)/g, match=>match.replace(/[.!?]/g, '·'));
  const segments = [...new Intl.Segmenter('de', {granularity: 'sentence'}).segment(masked)];
  const last = segments.at(-1);
  return {body: value.slice(0, last.index).trimEnd(), question: value.slice(last.index).trim()};
}

export function previewParts(parts, limit = 620) {
  if (parts.reduce((sum, part) => sum + part.text.length, 0) <= 700) return parts;
  const preview = [];
  let length = 0;
  for (const part of parts) {
    if (length >= limit) break;
    if (part.job || length + part.text.length <= limit) {
      preview.push(part); length += part.text.length;
    } else {
      const fragment = part.text.slice(0, limit - length);
      const space = fragment.lastIndexOf(' ');
      preview.push({text: fragment.slice(0, space > 0 ? space : undefined).trimEnd()});
      break;
    }
  }
  return [...preview, {text: ' …'}];
}

export function jobNavigationTarget(jobs, jobId, initialCount = 10) {
  const index = jobs.findIndex(job => String(job.id) === String(jobId));
  return index < 0 ? null : {job: jobs[index], revealAll: index >= initialCount};
}

// Keep job names and explanations in separate readable lines, using real lists.
export function chatContentBlocks(text) {
  const blocks = [];
  let paragraph = [];
  const flush = () => {
    if (paragraph.length) blocks.push({type: 'paragraph', text: paragraph.join('\n')});
    paragraph = [];
  };
  for (const line of text.split('\n')) {
    const item = line.trim().match(/^(?:[-•*]|\d+[.)])\s+(.+)$/);
    if (item) {
      flush();
      if (blocks.at(-1)?.type !== 'jobs') blocks.push({type: 'jobs', items: []});
      const ranges = [...item[1].matchAll(/\[[^\]\n]+\]\(job:[^)]+\)/g)].map(match=>[match.index,match.index+match[0].length]);
      const split = [...item[1].matchAll(/: /g)].find(match=>!ranges.some(([start,end])=>match.index>=start&&match.index<end))?.index ?? -1;
      blocks.at(-1).items.push({title: split < 0 ? item[1] : item[1].slice(0, split),
        description: split < 0 ? '' : item[1].slice(split + 2)});
    } else if (!line.trim()) flush();
    else paragraph.push(line.trim());
  }
  flush();
  return blocks;
}

// Baseline A may mention the same jobs, but never exposes interactive targets.
export function plainJobReferences(text, jobs = []) {
  return jobReferenceParts(text, jobs, {hideJobIds: false}).map(part => part.text).join('');
}
