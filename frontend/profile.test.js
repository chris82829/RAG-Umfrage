import assert from 'node:assert/strict';
import { test } from 'node:test';
import { makeProfile, exampleForm, emptyForm, fromProfile, activeFilters, profileSummary } from './profile.js';
import { defaultAdvisor, validateAdvisor, sameAdvisor, advisorAiLabel, advisorPresets, advisorScoreLabel } from './advisor.js';
import { clampChatWidth, chatWidthBounds, keyboardChatWidth, messagePreview, onboardingChatWidth } from './chat-layout.js';
import { actionFeedback, candidatePool, canSendChat, pendingFeedback, profileChangeAction, recoveredSubmission, submittedChangeApplied } from './chat-actions.js';
import { MIN_MATCH_SCORE, resultVisibilityKey, scoreVisibility } from './score-visibility.js';

test('onboarding gives the right panel more space without squeezing the guide or overflowing', () => {
  assert.equal(onboardingChatWidth(1200), 720);
  assert.equal(onboardingChatWidth(1600), 800);
  for (const size of [851, 900, 1024, 1200, 1600]) {
    const width = onboardingChatWidth(size);
    assert.ok(width >= 360);
    assert.ok(size - width - 12 >= 400);
  }
});

test('profile sends clean lists and numeric hours to the strict API', () => {
  const p = makeProfile({ ...exampleForm, skills: 'Python, SQL; Python\nC++', hours: '20', location: ' München, Berlin ' });
  assert.deepEqual(p.skills, ['Python', 'SQL', 'C++']);
  assert.equal(p.filters.max_hours, 20);
  assert.deepEqual(p.filters.locations, ['München', 'Berlin']);
  assert.deepEqual(p.filters.remote, []);
});
test('empty hours set no preference and profiles still require useful applicant context', () => {
  assert.equal(makeProfile(exampleForm).filters.max_hours, null);
  assert.throws(() => makeProfile({ ...emptyForm, employment: ['werkstudent'] }));
  for (const hours of ['0', '-1', '81', 'NaN']) assert.throws(() => makeProfile({ ...exampleForm, hours }));
});
test('restored profiles preserve API fields while only employment types appear as hard filters', () => {
  const p = makeProfile({ ...exampleForm, location: 'München', remote: ['remote'], hours: '16', cv: 'Studium und Praxisprojekt' });
  assert.deepEqual(makeProfile(fromProfile(p)), p);
  assert.deepEqual(activeFilters(p), ['Werkstudent', 'Praktikum']);
  assert.deepEqual(profileSummary(p), {
    hardFilters: ['Werkstudent', 'Praktikum'],
    wishes: [...p.preferences, 'Ort gewünscht: München', 'Arbeitsmodell gewünscht: 100 % Homeoffice', 'Bis 16 h/Woche gewünscht'],
    hasExperience: true,
  });
  assert.deepEqual(profileSummary(), { hardFilters: [], wishes: [], hasExperience: false });
  assert.deepEqual(profileSummary({ filters: { locations: ['Berlin'], max_hours: 12 }, cv_text: ' ' }), {
    hardFilters: [], wishes: ['Ort gewünscht: Berlin', 'Bis 12 h/Woche gewünscht'], hasExperience: false,
  });
});

test('multiple work models chosen in chat survive editing the profile', () => {
  const p = makeProfile({ ...exampleForm, remote: ['hybrid', 'remote', 'unknown'] });
  assert.deepEqual(makeProfile(fromProfile(p)), p);
  assert.deepEqual(p.filters.remote, ['hybrid', 'remote', 'unknown']);
});

test('preset remains valid after clearing a custom name and switching modes', () => {
  const a = validateAdvisor({ ...defaultAdvisor, mode: 'preset', preset: 'angela', name: '', traits: [] });
  assert.equal(a.mode, 'preset');
  assert.equal(a.preset, 'angela');
  assert.ok(a.name.length > 0);
  assert.deepEqual(Object.keys(advisorPresets), ['diana', 'steve', 'angela', 'guenther']);
});
test('custom advisor requires a name and traits; comparison ignores JSON key order', () => {
  assert.throws(() => validateAdvisor({ ...defaultAdvisor, mode: 'custom', name: ' ' }));
  assert.throws(() => validateAdvisor({ ...defaultAdvisor, mode: 'custom', traits: [] }));
  const a = validateAdvisor({ ...defaultAdvisor, mode: 'custom', name: ' Lernbegleitung ', traits: ['empathisch'], focus: 'lernpotenzial' });
  assert.equal(a.name, 'Lernbegleitung');
  assert.ok(sameAdvisor(a, Object.fromEntries(Object.entries(a).reverse())));
  assert.ok(!sameAdvisor(a, { ...a, focus: 'innovation' }));
});

test('custom description survives validation, detects edits and treats legacy absence as empty', () => {
  const custom = { ...defaultAdvisor, mode: 'custom', name: 'Alex', description: '' };
  const configured = validateAdvisor({ ...custom, description: '  Erkläre ruhig.\nStelle kritische Rückfragen.  ' });
  assert.equal(configured.description, 'Erkläre ruhig.\nStelle kritische Rückfragen.');
  assert.ok(!sameAdvisor(configured, { ...configured, description: 'Sei direkt.' }));
  const { description, ...legacy } = custom;
  assert.ok(sameAdvisor(legacy, custom));
  assert.equal(validateAdvisor(legacy).description, '');
  assert.equal(validateAdvisor({ ...configured, description: 'x'.repeat(2000) }).description.length, 2000);
  assert.throws(() => validateAdvisor({ ...configured, description: 'x'.repeat(2001) }));
  assert.throws(() => validateAdvisor({ ...configured, description: 42 }));
  assert.throws(() => validateAdvisor({ ...configured, description: null }));
  assert.equal(validateAdvisor({ ...configured, mode: 'preset', preset: 'steve' }).description, '');
  assert.equal(submittedChangeApplied({ advisor: configured, chat_action: 'rerank' },
    { advisor: { ...configured, description: 'Noch nicht gespeichert.' } }, 'advisor'), false);
});

test('AI names follow saved personalities and normalize custom names without duplicate suffixes', () => {
  assert.equal(advisorAiLabel(undefined), 'Top-Berufsberater-KI');
  assert.equal(advisorAiLabel({}), 'DIANA-KI');
  for (const [preset, expected] of Object.entries({ diana: 'DIANA-KI', steve: 'Steve-Jobs-KI', angela: 'Angela-Merkel-KI', guenther: 'Günther-Jauch-KI' })) {
    assert.equal(advisorAiLabel({ ...defaultAdvisor, mode: 'preset', preset }), expected);
  }
  for (const [name, expected] of [['  Alex   Weber  ', 'Alex-Weber-KI'], ['Özlem', 'Özlem-KI'], ['Alex-ki', 'Alex-KI'], ['Alex KI', 'Alex-KI'], ['Alex-KI', 'Alex-KI'], ['Lern\nBegleitung', 'Lern-Begleitung-KI']]) {
    const advisor = Object.freeze({ ...defaultAdvisor, mode: 'custom', name });
    assert.equal(advisorAiLabel(advisor), expected);
    assert.equal(advisor.name, name);
  }
});

test('score labels follow the selected personality, including old sessions and custom names', () => {
  assert.equal(advisorScoreLabel(undefined), 'Top-Berufsberater-Score');
  for (const [preset, expected] of Object.entries({ diana: 'DIANA-Score', steve: 'Steve-Jobs-Score', angela: 'Angela-Merkel-Score', guenther: 'Günther-Jauch-Score' })) {
    assert.equal(advisorScoreLabel({ ...defaultAdvisor, mode: 'preset', preset }), expected);
  }
  assert.equal(advisorScoreLabel({ ...defaultAdvisor, mode: 'custom', name: '  Alex   Weber  ' }), 'Alex-Weber-Score');
  assert.equal(advisorScoreLabel({ ...defaultAdvisor, mode: 'custom', name: 'Özlem' }), 'Özlem-Score');
});

test('resizing preserves room for job cards and handles invalid saved widths', () => {
  for (const available of [851, 1000, 1600]) {
    const width = clampChatWidth(2000, available);
    assert.ok(width >= 360 && width <= 800);
    assert.ok(available - width - 12 >= 400);
  }
  assert.equal(clampChatWidth(NaN, 1600), 460);
  assert.equal(clampChatWidth(Infinity, 1600), 460);
  assert.equal(clampChatWidth(-100, 1600), 360);
});
test('splitter keyboard moves the divider in the expected direction without eating other keys', () => {
  assert.equal(keyboardChatWidth('ArrowLeft', 460, 1200), 480);
  assert.equal(keyboardChatWidth('ArrowRight', 460, 1200), 440);
  assert.equal(keyboardChatWidth('Home', 460, 1200), 360);
  assert.equal(keyboardChatWidth('End', 460, 1200), chatWidthBounds(1200).max);
  assert.equal(keyboardChatWidth('ArrowLeft', 780, 1200, true), 788);
  assert.equal(keyboardChatWidth('a', 460, 1200), null);
});
test('long historical answers get a bounded preview while short answers stay complete', () => {
  const original = 'Eine vollständige Erklärung mit wichtigen Details. '.repeat(30);
  const preview = messagePreview(original);
  assert.ok(preview.length < 650);
  assert.ok(preview.endsWith(' …'));
  assert.ok(original.startsWith(preview.slice(0, -2)));
  assert.equal(messagePreview('Kurze Antwort.'), 'Kurze Antwort.');
});

test('chat modes permit explicit empty actions but never rerank a missing or empty saved pool', () => {
  const current = { candidate_pool: { available: true, count: 20 } };
  assert.equal(canSendChat('auto', ' ', current), false);
  assert.equal(canSendChat('auto', 'Warum passt diese Stelle?', {}), true);
  assert.equal(canSendChat('search', '', {}), true);
  assert.equal(canSendChat('rerank', '', current), true);
  for (const old of [{}, { candidate_pool: { available: false, count: 5 } }, { candidate_pool: { available: true, count: 0 } }, { candidate_pool: { available: true, count: 20, refresh_required: true } }]) {
    assert.equal(candidatePool(old).canRerank, false);
    assert.equal(canSendChat('rerank', 'Neu bewerten', old), false);
    assert.equal(canSendChat('auto', 'Warum passt diese Stelle?', old), true);
    assert.equal(canSendChat('search', '', old), true);
  }
  assert.equal(candidatePool({ candidate_pool: { available: true, count: 20, refresh_required: false } }).canRerank, true);
  assert.equal(candidatePool({ candidate_pool: { available: true, count: 20, refresh_required: true } }).refreshRequired, true);
  assert.equal(canSendChat('search', '', null), false);
});

test('only search goal, skills and employment types require a new search after editing', () => {
  const before = makeProfile(exampleForm);
  for (const after of [
    { ...before, query: 'Ich suche Designaufgaben.' },
    { ...before, skills: [...before.skills, 'Rust'] },
    { ...before, filters: { ...before.filters, employment_types: ['vollzeit'] } },
    { ...before, skills: ['Rust'], cv_text: 'Weitere Erfahrung', filters: { ...before.filters, locations: ['Berlin'] } },
  ]) assert.equal(profileChangeAction(before, after), 'search');
  for (const after of [
    { ...before, preferences: ['Teamarbeit'] },
    { ...before, cv_text: 'Praxisprojekt mit Kundengesprächen' },
    { ...before, filters: { ...before.filters, locations: ['Berlin'] } },
    { ...before, filters: { ...before.filters, remote: ['remote'] } },
    { ...before, filters: { ...before.filters, max_hours: 20 } },
  ]) assert.equal(profileChangeAction(before, after), 'rerank');
  assert.equal(profileChangeAction(undefined, before), 'search');
});

test('semantic profile comparisons preserve equivalent values but retain real preference changes', () => {
  const before = makeProfile({ ...exampleForm, location: 'München, Bad Aibling', remote: ['hybrid', 'remote'], hours: '16', cv: 'Praxisprojekt im Team' });
  const equivalent = {
    ...before, query: `  ${before.query.toUpperCase().replaceAll(' ', '  ')}  `,
    skills: [...before.skills].reverse().map(skill => skill.toLowerCase()),
    preferences: [...before.preferences].reverse(), cv_text: ' PRAXISPROJEKT  im\nTeam ',
    filters: { ...before.filters, employment_types: [...before.filters.employment_types].reverse(), locations: ['BAD  AIBLING', ' münchen '], remote: ['remote', 'hybrid', 'hybrid'] },
  };
  assert.equal(profileChangeAction(before, equivalent), 'answer');
  for (const field of ['locations', 'remote', 'max_hours']) {
    const cleared = { ...before, filters: { ...before.filters, [field]: field === 'max_hours' ? null : [] } };
    assert.equal(profileChangeAction(before, cleared), 'rerank');
  }
  assert.equal(pendingFeedback({ kind: 'profile', mode: 'rerank' }, 20), 'Profilangaben werden neu bewertet');
  assert.equal(pendingFeedback({ kind: 'profile', mode: 'search' }, 20), 'Profil wird für eine neue Suche geprüft');
});

test('successful response must actually apply the submitted profile or personality', () => {
  const profile = makeProfile(exampleForm);
  const changed = { ...profile, skills: ['Rust'] };
  assert.equal(submittedChangeApplied({ profile }, { profile: changed }, 'profile'), false);
  assert.equal(submittedChangeApplied({ profile: Object.fromEntries(Object.entries(changed).reverse()) }, { profile: changed }, 'profile'), true);
  assert.equal(submittedChangeApplied({ advisor: defaultAdvisor, chat_action: 'answer' }, { advisor: defaultAdvisor }, 'advisor'), false);
  assert.equal(submittedChangeApplied({ advisor: defaultAdvisor, chat_action: 'rerank' }, { advisor: defaultAdvisor }, 'advisor'), true);
});

test('lost replies only recover matching submissions and keep ambiguous empty actions pending', () => {
  const profile = makeProfile(exampleForm);
  const previous = { profile, advisor: defaultAdvisor, messages: [{ role: 'assistant', content: 'Deine Jobs.' }] };
  const changed = { ...profile, skills: ['Rust'] };
  const latest = { ...previous, profile: changed, chat_action: 'search', messages: [...previous.messages, { role: 'user', content: 'Ich kann Rust.' }, { role: 'assistant', content: 'Neue Empfehlungen.' }] };
  assert.equal(recoveredSubmission(previous, latest, { profile: changed }, 'profile'), true);
  assert.equal(recoveredSubmission(previous, latest, { profile: { ...profile, skills: ['Java'] } }, 'profile'), false);
  assert.equal(recoveredSubmission(previous, latest, { mode: 'search' }, 'refresh'), false);
  assert.equal(recoveredSubmission(previous, latest, { mode: 'rerank', message: 'Ich kann Rust.' }, 'chat'), false);
  assert.equal(recoveredSubmission(previous, latest, { mode: 'auto', message: 'Ich kann Rust.' }, 'chat'), true);
  assert.equal(recoveredSubmission(previous, previous, { profile }, 'profile'), false);
});

test('action feedback distinguishes answers, saved jobs and new searches', () => {
  assert.equal(actionFeedback({ chat_action: 'answer' }), 'Ergebnisse unverändert');
  assert.equal(actionFeedback({ chat_action: 'rerank', candidate_pool: { available: true, count: 20 } }), '20 Jobs neu bewertet');
  assert.equal(actionFeedback({ chat_action: 'search', jobs: [1, 2, 3] }), 'Neue Suche abgeschlossen · 3 von 3 Ergebnissen angezeigt');
  assert.equal(actionFeedback({ chat_action: 'search', jobs: [1, 2, 3] }, 0), 'Neue Suche abgeschlossen · 0 von 3 Ergebnissen angezeigt');
  assert.equal(actionFeedback({}), '');
});

test('all twenty assessed jobs remain available and more than five good matches are shown', () => {
  const jobs = Array.from({ length: 20 }, (_, index) => Object.freeze({
    id: `job-${index + 1}`, match: Object.freeze({ score: 100 - index * 5 }),
  }));
  Object.freeze(jobs);
  const hidden = scoreVisibility(jobs);
  assert.equal(hidden.visibleJobs.length, 7);
  assert.deepEqual(hidden.visibleJobs, jobs.slice(0, 7));
  assert.equal(hidden.lowCount, 13);
  const revealed = scoreVisibility(jobs, true);
  assert.equal(revealed.visibleJobs.length, 20);
  assert.deepEqual(revealed.visibleJobs, jobs);
  assert.notEqual(revealed.visibleJobs, jobs);
  assert.equal(revealed.visibleJobs[19].match.score, 5);
  assert.deepEqual(scoreVisibility(jobs).visibleJobs, hidden.visibleJobs);
  const allGood = jobs.map(job => ({ ...job, match: { score: 90 } }));
  assert.equal(scoreVisibility(allGood).visibleJobs.length, 20);
  assert.equal(scoreVisibility(allGood).lowCount, 0);
});

test('score threshold keeps the boundary and preserves original scores and ranking order', () => {
  const jobs = Object.freeze([100, MIN_MATCH_SCORE, MIN_MATCH_SCORE - 1, 1].map((score, i) => Object.freeze({ id: String(i), match: Object.freeze({ score }) })));
  const hidden = scoreVisibility(jobs);
  assert.deepEqual(hidden.visibleJobs.map(job => job.match.score), [100, MIN_MATCH_SCORE]);
  assert.equal(hidden.lowCount, 2);
  assert.equal(hidden.matchingCount, 2);
  const revealed = scoreVisibility(jobs, true);
  assert.deepEqual(revealed.visibleJobs, jobs);
  assert.notEqual(revealed.visibleJobs, jobs);
  assert.equal(revealed.lowCount, 2);
  assert.deepEqual(jobs.map(job => job.match.score), [100, MIN_MATCH_SCORE, MIN_MATCH_SCORE - 1, 1]);
});

test('low scores and an empty search remain distinct, and invalid scores never qualify', () => {
  const low = [25, MIN_MATCH_SCORE - 1].map(score => ({ match: { score } }));
  assert.equal(scoreVisibility(low).visibleJobs.length, 0);
  assert.equal(scoreVisibility(low).lowCount, 2);
  assert.deepEqual(scoreVisibility([]), { visibleJobs: [], lowCount: 0, matchingCount: 0 });
  for (const score of [undefined, NaN, Infinity, '91', 101, 70.5]) {
    assert.equal(scoreVisibility([{ match: { score } }]).matchingCount, 0);
  }
});

test('revealing results survives answers but does not carry over to a different result set or personality', () => {
  const session = { session_id: 'first', advisor: defaultAdvisor, jobs: [{ id: 'a', match: { score: 42 } }], messages: [] };
  const key = resultVisibilityKey(session);
  assert.equal(resultVisibilityKey({ ...structuredClone(session), chat_action: 'answer', messages: [{ role: 'assistant', content: 'Antwort' }] }), key);
  assert.notEqual(resultVisibilityKey({ ...session, session_id: 'second' }), key);
  assert.notEqual(resultVisibilityKey({ ...session, advisor: { ...defaultAdvisor, preset: 'angela' } }), key);
  assert.notEqual(resultVisibilityKey({ ...session, jobs: [{ id: 'a', match: { score: 69 } }] }), key);
  assert.notEqual(resultVisibilityKey({ ...session, jobs: [{ id: 'b', match: { score: 42 } }] }), key);
  assert.equal(resultVisibilityKey(null), null);
});
