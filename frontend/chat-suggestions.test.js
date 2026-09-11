import assert from 'node:assert/strict';
import { test } from 'node:test';
import { buildChatSuggestions } from './chat-suggestions.js';

function profile(filters = {}, skills = ['Python']) {
  return {
    query: 'Ich suche eine passende studentische Stelle.', skills, preferences: [], cv_text: '',
    filters: { employment_types: [], locations: [], remote: [], max_hours: null, ...filters },
  };
}

function job(overrides = {}) {
  return {
    id: '910001', title: 'Werkstudent Softwareentwicklung', company: 'Beispiel GmbH',
    employment_types: ['werkstudent'], location: 'München', remote: 'hybrid',
    hours_min: 12, hours_max: 20,
    match: { score: 87, matched_skills: ['Python'], missing_skills: ['C++'] },
    ...overrides,
  };
}

function session(jobs = [job()], savedProfile = profile(), messages = []) {
  return { session_id: 'saved-session', jobs, profile: savedProfile, messages };
}

function assertBounded(suggestions) {
  assert.ok(Array.isArray(suggestions));
  assert.ok(suggestions.length <= 3);
  assert.equal(new Set(suggestions.map(item => item.id)).size, suggestions.length);
  for (const suggestion of suggestions) {
    assert.equal(typeof suggestion.id, 'string');
    assert.equal(typeof suggestion.label, 'string');
    assert.equal(typeof suggestion.message, 'string');
    assert.ok(suggestion.id.length > 0);
    assert.ok(suggestion.label.length > 0 && suggestion.label.length <= 90);
    assert.ok(suggestion.message.length > 0 && suggestion.message.length <= 3000);
  }
}

function deepFreeze(value) {
  if (value && typeof value === 'object') {
    Object.values(value).forEach(deepFreeze);
    Object.freeze(value);
  }
  return value;
}

test('revealed low-score jobs do not introduce filters or preferences unsupported by a good match', () => {
  const good = job({ remote: 'unknown', hours_min: null, hours_max: null });
  const weak = job({ id: 'weak', remote: 'remote', hours_max: 40, match: { score: 42, missing_skills: [] } });
  const saved = session([good, weak], profile({ employment_types: ['werkstudent'] }));
  const suggestions = buildChatSuggestions(saved, [good, weak]);
  assert.ok(suggestions.length > 0);
  assert.ok(suggestions.every(item => !/^(filter|preference):/.test(item.id)));
});

test('null sessions and incomplete legacy records are safe', () => {
  assert.deepEqual(buildChatSuggestions(null, []), []);
  assert.deepEqual(buildChatSuggestions(undefined, undefined), []);
  for (const saved of [{}, { jobs: null }, { profile: {}, jobs: [] }, { jobs: [{ id: 'legacy-job' }] }]) {
    assertBounded(buildChatSuggestions(saved, saved.jobs));
  }
  assertBounded(buildChatSuggestions(session(), null));
});

test('zero actual results without active filters offer profile questions, not invented tightening', () => {
  const suggestions = buildChatSuggestions(session([], profile()), []);
  assertBounded(suggestions);
  assert.ok(suggestions.length > 0);
  for (const suggestion of suggestions) {
    assert.ok(!suggestion.id.startsWith('filter:'));
    assert.ok(!suggestion.id.startsWith('relax:'));
    assert.ok(!/^(fit|skill|compare):/.test(suggestion.id));
    assert.ok(!suggestion.message.includes('(Job-ID '));
  }
});

test('zero actual results suggest relaxing only employment type, never work preferences', () => {
  const filters = { employment_types: ['werkstudent'], locations: ['München'], remote: ['remote'], max_hours: 20 };
  const suggestions = buildChatSuggestions(session([], profile(filters)), []);
  assertBounded(suggestions);
  assert.ok(suggestions.length > 0);
  assert.ok(suggestions.some(item => item.id === 'relax:employment'));
  assert.ok(suggestions.every(item => item.id === 'relax:employment' || item.id.startsWith('profile:')));
  for (const [field, value] of [
    ['locations', ['Berlin']], ['remote', ['remote']], ['max_hours', 16],
  ]) {
    const isolated = buildChatSuggestions(session([], profile({ [field]: value })), []);
    assert.ok(isolated.length > 0);
    assert.ok(isolated.every(item => item.id.startsWith('profile:')));
  }
  const employment = buildChatSuggestions(session([], profile({ employment_types: ['praktikum'] })), []);
  assert.ok(employment.some(item => item.id === 'relax:employment'));
});

test('all hidden results yield score or profile questions without referencing hidden jobs or skills', () => {
  const hidden = job({ id: 'hidden-991', title: 'Geheimer Spezialtitel', company: 'VerborgeneFirma',
    match: { score: 42, matched_skills: ['VerdeckteKompetenz'], missing_skills: ['UnsichtbarerSkill'] } });
  const suggestions = buildChatSuggestions(session([hidden]), []);
  assertBounded(suggestions);
  assert.ok(suggestions.length > 0);
  const serialized = JSON.stringify(suggestions);
  for (const hiddenValue of [hidden.id, hidden.title, hidden.company, 'VerdeckteKompetenz', 'UnsichtbarerSkill']) {
    assert.ok(!serialized.includes(hiddenValue), hiddenValue);
  }
  assert.ok(suggestions.every(item => !/^(fit|skill|compare|filter|preference):/.test(item.id)));
  assert.ok(suggestions.every(item => !item.message.includes('(Job-ID ')));
});

test('saved profile and visible jobs provide a fit, supported preference and skill question without user history', () => {
  const visible = job({ remote: 'remote' });
  const saved = session([visible], profile({ employment_types: ['werkstudent'] }));
  const suggestions = buildChatSuggestions(saved, [visible]);
  assertBounded(suggestions);
  assert.equal(suggestions.length, 3);
  const fit = suggestions.find(item => item.id === `fit:${visible.id}`);
  assert.ok(fit);
  assert.ok(fit.message.includes(`(Job-ID ${visible.id})`));
  const preferences = suggestions.filter(item => item.id.startsWith('preference:'));
  assert.equal(preferences.length, 1);
  assert.ok(['preference:remote:remote', 'preference:hours:20'].includes(preferences[0].id));
  assert.ok(!suggestions.some(item => item.id === 'filter:employment:werkstudent'));
  const skill = suggestions.find(item => item.id.startsWith(`skill:${visible.id}:`));
  assert.ok(skill);
  assert.ok(skill.message.includes('C++'));
  assert.ok(skill.message.includes(`(Job-ID ${visible.id})`));
});

test('already selected employment types and wishes are never offered again and useful job questions remain', () => {
  const first = job();
  const second = job({ id: '910002', title: 'Werkstudent Datenanalyse' });
  const saved = session([first, second], profile({ employment_types: ['werkstudent'], remote: ['hybrid'], max_hours: 20 }));
  const suggestions = buildChatSuggestions(saved, [first, second]);
  assertBounded(suggestions);
  assert.ok(suggestions.length >= 2);
  assert.ok(suggestions.some(item => item.id === `fit:${first.id}`));
  assert.ok(suggestions.every(item => !/^(filter|preference):/.test(item.id)));
  assert.ok(suggestions.some(item => item.id.startsWith('skill:') || item.id.startsWith('compare:')));
});

test('hours suggestions use only valid advertised maxima as wishes and preserve existing preferences', () => {
  const active = { employment_types: ['werkstudent'], remote: ['hybrid'] };
  const visible = job({ hours_min: 12, hours_max: 24 });
  const suggestions = buildChatSuggestions(session([visible], profile(active)), [visible]);
  const hours = suggestions.find(item => item.id === 'preference:hours:24');
  assert.ok(hours);
  assert.equal(hours.label, 'Bis 24 Stunden gewünscht');
  assert.ok(hours.message.includes('als Präferenz bei der Neubewertung'));
  assert.ok(hours.message.includes('ohne Stellen allein wegen ihrer Arbeitszeit auszuschließen'));
  assert.ok(!suggestions.some(item => item.id === 'preference:hours:20'));
  for (const invalid of [undefined, null, 0, -1, '20', NaN, Infinity, 81]) {
    const unsuitable = job({ hours_max: invalid });
    const result = buildChatSuggestions(session([unsuitable], profile(active)), [unsuitable]);
    assert.ok(result.every(item => !item.id.startsWith('preference:hours:')), String(invalid));
  }
  const restricted = buildChatSuggestions(session([visible], profile({ ...active, max_hours: 16 })), [visible]);
  assert.ok(restricted.every(item => !item.id.startsWith('preference:hours:')));
});

test('work model suggestions reweight existing jobs without excluding other work models', () => {
  const visible = job({ remote: 'remote' });
  const suggestions = buildChatSuggestions(session([visible], profile({ employment_types: ['werkstudent'] })), [visible]);
  const workModel = suggestions.find(item => item.id === 'preference:remote:remote');
  assert.ok(workModel);
  assert.equal(workModel.label, '100 % Homeoffice bevorzugen');
  assert.ok(workModel.message.includes('Neubewertung der vorhandenen Jobs'));
  assert.ok(workModel.message.includes('ohne andere Arbeitsmodelle auszuschließen'));
  assert.ok(!/nur stellen|suche erneut|zeige mir nur/i.test(workModel.message));
  const afterQuestion = buildChatSuggestions(session([visible], profile({ employment_types: ['werkstudent'] }), [{ role: 'user', content: workModel.message }]), [visible]);
  assert.ok(!afterQuestion.some(item => item.id === workModel.id));
});

test('C, C++ and NoSQL remain distinct from similar saved or previously discussed skills', () => {
  const identifiers = [];
  for (const [known, missing] of [['C', 'C++'], ['C++', 'C'], ['SQL', 'NoSQL'], ['NoSQL', 'SQL']]) {
    const visible = job({ match: { score: 91, matched_skills: [known], missing_skills: [missing] } });
    const saved = session([visible], profile({ employment_types: ['werkstudent'], remote: ['hybrid'], max_hours: 20 }, [known]));
    const suggestion = buildChatSuggestions(saved, [visible]).find(item => item.id.startsWith(`skill:${visible.id}:`));
    assert.ok(suggestion, `${known} must not hide ${missing}`);
    assert.ok(suggestion.message.includes(missing));
    assert.ok(suggestion.message.includes(`(Job-ID ${visible.id})`));
    identifiers.push(suggestion.id);
    const previousQuestion = { role: 'user', content: `Welche Rolle spielt ${known} bei der Stelle (Job-ID ${visible.id})?` };
    const discussed = buildChatSuggestions({ ...saved, messages: [previousQuestion] }, [visible]);
    assert.ok(discussed.some(item => item.id === suggestion.id), `Discussion of ${known} must not suppress ${missing}`);
  }
  assert.equal(new Set(identifiers).size, 4);
});

test('questions follow the next visible result instead of preserving a stale job reference', () => {
  const oldJob = job({ id: 'old-991', title: 'Bisherige Empfehlung' });
  const nextJob = job({ id: 'next-882', title: 'Aktuelle Empfehlung' });
  const previous = buildChatSuggestions(session([oldJob]), [oldJob]);
  const current = buildChatSuggestions(session([nextJob]), [nextJob]);
  assert.ok(previous.some(item => item.id === `fit:${oldJob.id}`));
  assert.ok(current.some(item => item.id === `fit:${nextJob.id}`));
  assert.ok(!JSON.stringify(current).includes(oldJob.id));
  const concrete = current.filter(item => /^(fit|skill):/.test(item.id));
  assert.ok(concrete.every(item => item.message.includes(`(Job-ID ${nextJob.id})`)));
});

test('recent user messages suppress the same generated suggestion, while assistant text does not', () => {
  const saved = session();
  const initial = buildChatSuggestions(saved, saved.jobs);
  const fit = initial.find(item => item.id.startsWith('fit:'));
  assert.ok(fit);
  const asked = { ...saved, messages: [{ role: 'user', content: fit.message }] };
  const next = buildChatSuggestions(asked, saved.jobs);
  assertBounded(next);
  assert.ok(!next.some(item => item.message === fit.message));
  const assistant = { ...saved, messages: [{ role: 'assistant', content: fit.message }] };
  assert.ok(buildChatSuggestions(assistant, saved.jobs).some(item => item.id === fit.id));
});

test('suggestions are deterministic, bounded and do not mutate frozen profile, jobs or history', () => {
  const longJob = job({ title: 'Ausführlicher Stellenname '.repeat(100), company: 'Großer Firmenname '.repeat(100),
    match: { score: 89, matched_skills: ['Python'], missing_skills: ['Komplexer Fachbegriff '.repeat(300)] } });
  const saved = deepFreeze(session([longJob], profile(), [{ role: 'assistant', content: 'Empfehlungen.' }]));
  const visible = deepFreeze([longJob]);
  const before = JSON.stringify({ saved, visible });
  const first = buildChatSuggestions(saved, visible);
  const second = buildChatSuggestions(saved, visible);
  assertBounded(first);
  assert.deepEqual(second, first);
  assert.equal(JSON.stringify({ saved, visible }), before);
  const fit = first.find(item => item.id === `fit:${longJob.id}`);
  assert.ok(fit?.message.includes(`(Job-ID ${longJob.id})`));
});

test('multiple active alternatives may be narrowed to a supported visible-job filter', () => {
  const visible = job({ remote: 'onsite', hours_min: null, hours_max: null });
  const saved = session([visible], profile({ employment_types: ['werkstudent', 'praktikum'], remote: ['onsite', 'remote'] }));
  const filters = buildChatSuggestions(saved, [visible]).filter(item => item.id.startsWith('filter:'));
  assert.equal(filters.length, 1);
  assert.equal(filters[0].id, 'filter:employment:werkstudent');
});


test('basic variant retains contextual search refinements without scores or invented skill gaps',()=>{
 const basic=job({match:undefined});
 const suggestions=buildChatSuggestions(session([basic]),[basic],{showScores:false});
 assertBounded(suggestions);
 assert.ok(suggestions.some(item=>item.id==='filter:employment:werkstudent'));
 assert.ok(suggestions.some(item=>item.id.startsWith('fit:')));
 assert.ok(suggestions.every(item=>!item.id.startsWith('scores:')&&!item.id.startsWith('skill:')));
 assert.ok(suggestions.every(item=>!/(score|punktzahl)/i.test(item.message)));
 const emptyVisible=buildChatSuggestions(session([basic]),[],{showScores:false});
 assert.ok(emptyVisible.every(item=>!item.id.startsWith('scores:')));
});
