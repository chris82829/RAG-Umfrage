import {careerAdvisor, editableAdvisor, standardAdvisor} from './advisor.js';
import {templateSelection} from './advisor-selection.js';

export const PERSONALITY_POLICIES = ['unprompted', 'career_fixed', 'custom_career'];

function cloneAdvisor(value) {
  return {...value, traits:[...(value?.traits || [])], description:value?.description ?? ''};
}

export function policyForArm(arm) {
  return arm === 'A' ? 'unprompted' : arm === 'B' ? 'career_fixed' : 'custom_career';
}

export function canCustomizeAdvisor(policy) {
  return policy === 'custom_career';
}

export function advisorForPolicy(policy, reviewedCareer=careerAdvisor) {
  if (policy === 'unprompted') return cloneAdvisor(standardAdvisor);
  const base=editableAdvisor(reviewedCareer);
  if (policy === 'career_fixed') return cloneAdvisor(base);
  if (policy === 'custom_career') return {...cloneAdvisor(base),mode:'custom',preset:'diana',description:''};
  throw new Error('Unbekannte Beratungsvariante.');
}

export function selectionForPolicy(policy) {
  if (policy === 'career_fixed') return templateSelection('career');
  if (policy === 'custom_career') return templateSelection('');
  return null;
}

export function restoredAdvisorForPolicy(policy, session, reviewedCareer=careerAdvisor) {
  if (policy !== 'custom_career') return advisorForPolicy(policy, reviewedCareer);
  if (session?.advisor_selection?.source !== 'custom') return advisorForPolicy(policy, reviewedCareer);
  return editableAdvisor(session.advisor || advisorForPolicy(policy, reviewedCareer));
}

export function normalizeSessionForPolicy(policy, session, reviewedCareer=careerAdvisor) {
  if (!session) return session;
  const advisor=restoredAdvisorForPolicy(policy, session, reviewedCareer);
  const advisor_selection=selectionForPolicy(policy);
  return {...session,advisor,advisor_selection};
}
