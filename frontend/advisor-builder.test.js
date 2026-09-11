import assert from 'node:assert/strict';
import { test } from 'node:test';
import { defaultAdvisor, advisorTemplates, advisorFromTemplate, editableAdvisor, sameAdvisor, validateAdvisor, advisorAiLabel } from './advisor.js';

test('new users start with the career advisor and two professional templates', () => {
  assert.equal(defaultAdvisor.mode, 'custom');
  assert.equal(validateAdvisor(editableAdvisor()).mode, 'custom');
  assert.ok(sameAdvisor(defaultAdvisor, advisorFromTemplate('career')));
  assert.equal(defaultAdvisor.name, 'Top-Berufsberater');
  assert.deepEqual(Object.keys(advisorTemplates), ['career', 'expert']);
  assert.throws(() => advisorFromTemplate('diana'));
  assert.throws(() => advisorFromTemplate('missing'));
  assert.throws(() => advisorFromTemplate('__proto__'));
});

test('no template restores an independent neutral draft without celebrity instructions', () => {
  const value = advisorFromTemplate('');
  assert.equal(value.name, '');
  assert.throws(() => validateAdvisor(value));
  assert.equal(validateAdvisor({...value,name:'Meine KI'}).mode, 'custom');
  assert.equal(value.description, '');
  value.traits.push('direkt');
  assert.deepEqual(advisorFromTemplate('').traits, ['analytisch', 'ermutigend']);
});

test('templates fill all editable fields and never submit the hidden fixed preset mode', () => {
  for (const [key, template] of Object.entries(advisorTemplates)) {
    const draft = advisorFromTemplate(key);
    const submitted = validateAdvisor(editableAdvisor(draft));
    assert.equal(submitted.mode, 'custom');
    assert.equal(submitted.name, template.name);
    assert.equal(submitted.focus, template.focus);
    assert.deepEqual(submitted.traits, template.traits);
    assert.equal(submitted.description, template.instructions);
    assert.ok(submitted.description.length > 40);
    assert.ok(sameAdvisor(draft, submitted));
  }
});

test('editing a template preserves every user change through submission and reopening', () => {
  const template = advisorFromTemplate('career');
  const edited = { ...template, name: ' Meine Begleitung ', focus: 'lernpotenzial', traits: ['empathisch', 'strukturiert'], description: '  Bitte erkläre ruhig und nenne konkrete nächste Schritte.  ' };
  const submitted = validateAdvisor(editableAdvisor(edited));
  const reopened = editableAdvisor(submitted);
  assert.equal(submitted.mode, 'custom');
  assert.equal(submitted.name, 'Meine Begleitung');
  assert.equal(submitted.focus, 'lernpotenzial');
  assert.deepEqual(submitted.traits, ['empathisch', 'strukturiert']);
  assert.equal(submitted.description, edited.description.trim());
  assert.ok(sameAdvisor(submitted, reopened));
  assert.ok(!sameAdvisor(template, submitted));
  assert.equal(advisorAiLabel(submitted), 'Meine-Begleitung-KI');
});

test('switching templates fills a fresh draft without mutating templates or previous selections', () => {
  const first = advisorFromTemplate('career');
  const saved = structuredClone(first);
  const second = advisorFromTemplate('expert');
  second.traits.pop();
  assert.deepEqual(first, saved);
  assert.deepEqual(advisorFromTemplate('expert').traits, ['analytisch', 'kritisch', 'strukturiert']);
  const initial = editableAdvisor();
  initial.traits.push('direkt');
  assert.deepEqual(defaultAdvisor.traits, ['empathisch', 'strukturiert', 'ermutigend']);
});

test('legacy preset sessions become editable drafts without modifying saved settings or labels', () => {
  for (const preset of ['steve', 'angela', 'guenther']) {
    const saved = Object.freeze({ mode: 'preset', preset, name: 'Meine DIANA', traits: Object.freeze(['analytisch']), focus: 'ausgewogen' });
    const draft = editableAdvisor(saved);
    assert.equal(saved.mode, 'preset');
    assert.equal(draft.mode, 'custom');
    assert.equal(advisorAiLabel(draft), advisorAiLabel(saved));
    assert.ok(draft.description.includes(saved.preset === 'steve' ? 'Steve Jobs' : saved.preset === 'angela' ? 'Angela Merkel' : 'Günther Jauch'));
    assert.throws(() => advisorFromTemplate(preset));
  }
  const legacyCustom = { mode: 'custom', name: 'Alex', traits: ['direkt'], focus: 'innovation' };
  const draft = editableAdvisor(legacyCustom);
  draft.traits.push('neugierig');
  assert.deepEqual(legacyCustom.traits, ['direkt']);
  assert.equal(draft.description, '');
});
