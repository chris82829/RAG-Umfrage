export const defaultAdvisor = { mode: 'preset', preset: 'diana', name: 'Meine DIANA', traits: ['analytisch', 'ermutigend'], focus: 'ausgewogen', description: '' };
export const ADVISOR_DESCRIPTION_MAX_LENGTH = 2000;
export const advisorPresets = {
  diana: { name: 'DIANA', subtitle: 'Ausgewogen & ermutigend', description: 'Prüft fachliche Passung und Wünsche ausgewogen. Erklärt analytisch und ermutigt mit konkreten nächsten Schritten.', focus: 'ausgewogen', traits: ['analytisch', 'ermutigend'] },
  steve: { name: 'Steve Jobs', subtitle: 'Gestaltung & neue Ideen', description: 'Spricht direkt, pointiert und mit einem klaren Anspruch an die Wirkung deiner Arbeit. Stellt Gestaltungsspielraum und die entscheidende Frage in den Vordergrund.', focus: 'innovation', traits: ['kreativ', 'direkt', 'neugierig'] },
  angela: { name: 'Angela Merkel', subtitle: 'Abwägung & fachliche Tiefe', description: 'Wägt ruhig Chancen und offene Voraussetzungen ab. Argumentiert präzise, prüft fachliche Tiefe und kommt zu einem begründeten, vorsichtigen Fazit.', focus: 'ausgewogen', traits: ['analytisch', 'strukturiert', 'kritisch'] },
  guenther: { name: 'Günther Jauch', subtitle: 'Lernen & gute Fragen', description: 'Erklärt anschaulich und im Gespräch mit dir. Macht Lernchancen verständlich und fragt gezielt nach, wenn dir das bei der Entscheidung hilft.', focus: 'lernpotenzial', traits: ['neugierig', 'strukturiert', 'empathisch'] },
};
export const traitLabels = { analytisch: 'Analytisch', direkt: 'Direkt', ermutigend: 'Ermutigend', empathisch: 'Empathisch', neugierig: 'Neugierig', kreativ: 'Kreativ', strukturiert: 'Strukturiert', kritisch: 'Kritisch' };
export const focusLabels = { ausgewogen: 'Ausgewogen', fachliche_tiefe: 'Fachliche Vertiefung', lernpotenzial: 'Lernen & Entwicklung', innovation: 'Innovation & Gestaltung' };
export function advisorLabel(advisor) {
  const a = advisor || defaultAdvisor;
  return a.mode === 'custom' ? (a.name?.trim() || advisorPresets.diana.name) : (advisorPresets[a.preset]?.name || advisorPresets.diana.name);
}
export function advisorAiLabel(advisor) {
  const name = advisorLabel(advisor).trim().replace(/\s+/g, '-');
  return /-ki$/i.test(name) ? name.replace(/-ki$/i, '-KI') : `${name}-KI`;
}
export function advisorScoreLabel(advisor) {
  const name = advisorLabel(advisor).trim().replace(/\s+/g, '-');
  return `${name}-Score`;
}
export function validateAdvisor(a) {
  if (a.mode === 'preset') return { ...defaultAdvisor, preset: a.preset, traits: [...defaultAdvisor.traits] };
  if (a.mode === 'custom' && (!a.name.trim() || !a.traits.length || a.traits.length > 4)) throw new Error('Gib deiner Persönlichkeit einen Namen und wähle eine bis vier Eigenschaften.');
  const description = a.description === undefined ? '' : a.description;
  if (typeof description !== 'string' || description.trim().length > ADVISOR_DESCRIPTION_MAX_LENGTH) throw new Error(`Beschreibe deine Persönlichkeit mit höchstens ${ADVISOR_DESCRIPTION_MAX_LENGTH} Zeichen.`);
  return { ...a, name: a.name.trim(), traits: [...a.traits], description: description.trim() };
}

export function sameAdvisor(left, right) {
  if (!left || !right) return false;
  return ['mode', 'preset', 'name', 'focus'].every(key => left[key] === right[key]) && JSON.stringify(left.traits) === JSON.stringify(right.traits) && (left.description ?? '') === (right.description ?? '');
}
