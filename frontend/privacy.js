export const CONSENT_KEY = 'diana-privacy-consent';
let memoryToken = '';
export function consentToken(host = globalThis.window) {
  try { return host?.sessionStorage.getItem(CONSENT_KEY) || memoryToken; } catch { return memoryToken; }
}
export function rememberConsent(token, host = globalThis.window) {
  memoryToken = token;
  try { token ? host?.sessionStorage.setItem(CONSENT_KEY, token) : host?.sessionStorage.removeItem(CONSENT_KEY); } catch { /* Current page still works. */ }
}
export function consentHeaders() {
  const token = consentToken();
  return token ? {'X-Diana-Consent': token} : {};
}
export function clearParticipation(host = globalThis.window) {
  memoryToken = '';
  try {
    const storage = host.sessionStorage;
    for (const key of Object.keys(storage)) {
      if (key === CONSENT_KEY || key.startsWith('diana-survey:') || key.startsWith('diana-survey-chat:')) storage.removeItem(key);
    }
    host.localStorage.removeItem('jobkompass-session-v1');
  } catch { /* In-memory state is discarded by the gate too. */ }
}
export async function privacyRequest(path = '', options = {}) {
  const response = await fetch(`/api/privacy${path}`, {...options, headers:{...consentHeaders(), ...(options.body ? {'Content-Type':'application/json'} : {})}});
  const data = await response.json();
  if (!response.ok) throw new Error(data.error?.message || 'Datenschutz-Einstellungen konnten nicht geladen werden.');
  return data;
}
