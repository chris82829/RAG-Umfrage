export const SEARCH_STAGES = ['loaded', 'profiling', 'retrieval', 'ranking', 'finalizing'];

// Only public phase metadata crosses the survey iframe boundary.
export function readSearchProgress(value) {
  if (!value || !SEARCH_STAGES.includes(value.stage)) return null;
  const result = {stage:value.stage};
  for (const key of ['job_count', 'candidate_count']) {
    if (Number.isSafeInteger(value[key]) && value[key] >= 0) result[key] = value[key];
  }
  return result;
}

export function searchStatus(value) {
  const progress = readSearchProgress(value);
  const jobs = progress?.job_count?.toLocaleString('de-DE');
  const candidates = progress?.candidate_count?.toLocaleString('de-DE');
  const messages = {
    loaded: ['Stellendaten sind geladen', `${jobs ? `${jobs} Anzeigen stehen bereit.` : 'Die Anzeigen stehen bereit.'} Der digitale Papierstapel sitzt.`],
    profiling: ['Dein Suchprofil wird vorbereitet', `${jobs ? `${jobs} Anzeigen sind geladen. ` : ''}Deine Fähigkeiten und Wünsche werden aufbereitet. Kaffee ist dafür keiner nötig.`],
    retrieval: ['Stellen werden durchsucht', `${jobs ? `${jobs} Anzeigen werden` : 'Die Anzeigen werden'} mit Stichwörtern und inhaltlich verglichen. Auch zwischen den Zeilen.`],
    ranking: ['Vorauswahl gefunden · KI prüft', `${candidates ? `${candidates} Stellen sind` : 'Die Stellen sind'} in der Vorauswahl. Jetzt läuft der genaue Abgleich mit deinem Profil – inklusive Kleingedrucktem.`],
    finalizing: ['Ergebnisse werden vorbereitet', 'Der Abgleich ist fertig. Die Stellenkarten sind zusammengestellt und werden für die Anzeige bereitgestellt. Gleich darfst du stöbern.'],
  };
  const [title, description] = messages[progress?.stage] || ['Suche ist gestartet', 'Das System bereitet deine Anfrage vor. Gleich geht’s an die Stellen.'];
  return {title, description, index:SEARCH_STAGES.indexOf(progress?.stage)};
}
