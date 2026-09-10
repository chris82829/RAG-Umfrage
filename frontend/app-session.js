// Embedded survey runs must not resume the user's ordinary DIANA session.
export function surveyRun(search = '') {
  const params = new URLSearchParams(search);
  const run = params.get('run');
  return params.get('embed') === 'survey' && /^[a-f0-9]{32}$/.test(run || '') ? run : null;
}

export function appSessionStorage(host = window) {
  const run = surveyRun(host.location.search);
  const key = run ? `diana-survey-chat:${run}` : 'jobkompass-session-v1';
  const storage = () => run ? host.sessionStorage : host.localStorage;
  return {
    read() { try { return storage().getItem(key); } catch { return null; } },
    remember(id) {
      try { id ? storage().setItem(key, id) : storage().removeItem(key); } catch { /* Storage is optional. */ }
    },
  };
}

export function appPath(page, search = '') {
  const path = page === 'about' ? '/' : '/suche';
  const run = surveyRun(search);
  return run ? `${path}?embed=survey&run=${run}` : path;
}
