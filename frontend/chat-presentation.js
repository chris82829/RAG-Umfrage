// Only references to jobs in the current result set become interactive.
export function jobReferenceParts(text, jobs = []) {
  const byId = new Map(jobs.map(job => [String(job.id), job]));
  // Models sometimes escape Markdown brackets/parentheses. Treat these as the
  // same internal reference; the UI renders a known title, never this markup.
  const reference = /\\*\[([^\]\n]+?)\\*\][ \t]*\\*\([ \t]*job[ \t]*:[ \t]*([^\s)\\]+)[ \t]*\\*\)/gi;
  const references = [...text.matchAll(reference)];
  const explicitReferences = references.length > 0;
  const names = new Map();
  for (const job of jobs) for (const name of explicitReferences ? [] : [job.title, job.company]) {
    if (!name || name.length < 5) continue;
    const key = name.toLocaleLowerCase('de');
    const existing = names.get(key);
    names.set(key, existing && existing.id !== job.id ? {ambiguous: true} : existing || job);
  }
  const unique = [...names].filter(([, job]) => !job.ambiguous).sort((a, b) => b[0].length - a[0].length);
  const parts = [];
  function plain(value) {
    // Also recognize unambiguous names in earlier messages without link markup.
    let rest = value.replace(/\*\*([^*]+)\*\*/g, '$1')
      // Suppress an unfinished internal target while its tokens are streaming.
      .replace(/\\*\[([^\]\n]+?)\\*\][ \t]*\\*\((?:j(?:o(?:b(?::[^\n)]*)?)?)?)?\\*$/gi, '$1')
      .replace(/\\*\[([^\]\n]+?)\\*\][ \t]*\\*$/g, '$1')
      .replace(/\\*\[([^\]\n]*)$/g, '$1')
      .replace(/\\*\([ \t]*job[ \t]*:[^\n)]*(?:\)|$)/gi, '')
      .replace(/\\([\[\]()])/g, '$1').replace(/\\+$/g, '');
    while (rest) {
      const lower = rest.toLocaleLowerCase('de');
      let next = null;
      for (const [name, job] of unique) {
        const index = lower.indexOf(name);
        if (index < 0 || (index > 0 && /[\p{L}\p{N}]/u.test(rest[index - 1]))
            || /[\p{L}\p{N}]/u.test(rest[index + name.length] || '')) continue;
        if (!next || index < next.index) next = {index, length: name.length, job};
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
    parts.push(job ? {text: job.title, job} : {text: match[1].replace(/\*\*([^*]+)\*\*/g, '$1').replace(/\\([\[\]()])/g, '$1')});
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
