import assert from 'node:assert/strict';
import test from 'node:test';

import {
  PERSONALITY_POLICIES,
  advisorForPolicy,
  canCustomizeAdvisor,
  normalizeSessionForPolicy,
  policyForArm,
  restoredAdvisorForPolicy,
  selectionForPolicy,
} from './advisor-policy.js';
import { advisorTemplates, careerAdvisor, standardAdvisor } from './advisor.js';
import { selectionForRequest, templateSelection } from './advisor-selection.js';

test('study arms map to the three active personality policies', () => {
  assert.deepEqual(PERSONALITY_POLICIES, ['unprompted', 'career_fixed', 'custom_career']);
  assert.equal(policyForArm('A'), 'unprompted');
  assert.equal(policyForArm('B'), 'career_fixed');
  assert.equal(policyForArm('C'), 'custom_career');
  assert.equal(canCustomizeAdvisor('unprompted'), false);
  assert.equal(canCustomizeAdvisor('career_fixed'), false);
  assert.equal(canCustomizeAdvisor('custom_career'), true);
});

test('only the reviewed career template remains active', () => {
  assert.deepEqual(Object.keys(advisorTemplates), ['career']);
  assert.deepEqual(selectionForPolicy('career_fixed'), { source: 'template', template_id: 'career' });
  assert.deepEqual(selectionForPolicy('custom_career'), { source: 'custom', template_id: null });
  assert.deepEqual(templateSelection('expert'), { source: 'custom', template_id: null });
  assert.equal(selectionForRequest({ source: 'template', template_id: 'expert' }), undefined);
});

test('A uses the baseline policy, B is fixed, and C starts from a clean career copy', () => {
  const reviewedCareer = {
    ...careerAdvisor,
    traits: [...careerAdvisor.traits],
    description: 'Serverseitige Systemanweisung',
  };

  assert.deepEqual(advisorForPolicy('unprompted', reviewedCareer), standardAdvisor);
  assert.deepEqual(advisorForPolicy('career_fixed', reviewedCareer), reviewedCareer);

  const custom = advisorForPolicy('custom_career', reviewedCareer);
  assert.equal(custom.name, reviewedCareer.name);
  assert.deepEqual(custom.traits, reviewedCareer.traits);
  assert.notEqual(custom.traits, reviewedCareer.traits);
  assert.equal(custom.focus, reviewedCareer.focus);
  assert.equal(custom.description, '');
});

test('restoring a session cannot revive retired templates in B or C', () => {
  const oldExpertSession = {
    advisor: { mode: 'custom', name: 'Fachexperte', traits: ['analytisch'], focus: 'fachwissen' },
    advisor_selection: { source: 'template', template_id: 'expert' },
  };

  const fixed = normalizeSessionForPolicy('career_fixed', oldExpertSession, careerAdvisor);
  assert.equal(fixed.advisor.name, 'Top-Berufsberater');
  assert.deepEqual(fixed.advisor_selection, { source: 'template', template_id: 'career' });

  const custom = normalizeSessionForPolicy('custom_career', oldExpertSession, careerAdvisor);
  assert.equal(custom.advisor.name, 'Top-Berufsberater');
  assert.equal(custom.advisor.description, '');
  assert.deepEqual(custom.advisor_selection, { source: 'custom', template_id: null });
});

test('C restores a genuinely self-designed advisor', () => {
  const saved = {
    advisor: {
      mode: 'custom',
      name: 'Meine Beratung',
      traits: ['direkt', 'ruhig'],
      focus: 'entwicklung',
      description: 'Frage zuerst nach meinem bevorzugten Arbeitsumfeld.',
    },
    advisor_selection: { source: 'custom', template_id: null },
  };

  assert.deepEqual(restoredAdvisorForPolicy('custom_career', saved, careerAdvisor), {
    ...saved.advisor,
    preset: 'diana',
  });
  assert.deepEqual(normalizeSessionForPolicy('custom_career', saved, careerAdvisor), {
    ...saved,
    advisor: {...saved.advisor, preset: 'diana'},
  });
});
