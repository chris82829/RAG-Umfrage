// Display-only cleanup. Original job data and user-authored messages stay intact.
export function removeChatGenderSuffixes(text, streaming = false) {
  const value = text.replace(/…|\.{3,}/g, '').replace(/[ \t]*\(\s*[mwfdx]\s*[/|]\s*[mwfdx]\s*[/|]\s*[mwfdx]\s*\)/gi, '');
  // Hold back an unfinished suffix at the stream boundary. A completed technical
  // parenthesis such as (Python) is never removed.
  return streaming ? value.replace(/[ \t]*\(\s*[mwfdx](?:\s*[/|]\s*(?:[mwfdx](?:\s*[/|]\s*[mwfdx]?)?)?)?\s*$/i, '') : value;
}

// Only references to jobs in the current result set become interactive.
export function jobReferenceParts(text, jobs = []) {
  text = removeChatGenderSuffixes(text);
  const byId = new Map(jobs.map(job => [String(job.id), job]));
  // Models sometimes escape Markdown brackets/parentheses. Treat these as the
  // same internal reference; the UI renders a known title, never this markup.
  const reference = /\\*\[([^\]\n]+?)\\*\][ \t]*\\*\([ \t]*job[ \t]*:[ \t]*([^\s)\\]+)[ \t]*\\*\)/gi;
  const references = [...text.matchAll(reference)];
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
    parts.push(job ? {text: removeChatGenderSuffixes(job.title), job} : {text: match[1].replace(/\*\*([^*]+)\*\*/g, '$1').replace(/\\([\[\]()])/g, '$1')});
    start = match.index + match[0].length;
  }
  plain(text.slice(start));
  return parts;
}

export function separateFollowUp(text) {
  const value = text.replace(/\*\*([^*]+)\*\*/g, '$1').trim();
  if (!value.endsWith('?')) return {body: value, question: ''};
  const segments = [...new Intl.Segmenter('de', {granularity: 'sentence'}).segment(value)];
  const last = segments.at(-1);
  return {body: value.slice(0, last.index).trimEnd(), question: last.segment.trim()};
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
      const split = item[1].indexOf(': ');
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
  return jobReferenceParts(text, jobs).map(part => part.text).join('');
}
