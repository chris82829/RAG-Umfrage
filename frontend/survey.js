import {consentHeaders} from './privacy.js';
import definition from '../survey_definition.json' with { type: 'json' };

export const SURVEY_VERSION = definition.version;
export const SURVEY_STORAGE_KEY = `diana-survey:${SURVEY_VERSION}`;
export const demographics = {...definition.demographics,fields:definition.demographics.fields.filter(field=>!field.systemProvided)};
export const surveyCategories = definition.categories;
export const surveyScale = definition.scale;
export const surveyFields = [definition.demographics, ...surveyCategories].flatMap(group => group.fields);
export const surveyStages = ['system', 'demographics', ...surveyCategories.map(group => group.id)];
export const waitingQuestionFields = ['search_goal', 'personality_customized', 'personality_setup'].map(name => surveyFields.find(field => field.name === name));
export const waitingQuestionGroups = [demographics, {id: 'setup', title: 'Weitere Fragen', fields: waitingQuestionFields}];

export function suggestSearchGoal(state, suggestion) {
  if (typeof suggestion !== 'string' || !suggestion.trim() || suggestion.length > 1000 || state.submitted) return state;
  const text = suggestion.trim();
  return { ...state, searchGoalSuggestion: text,
    answers: state.searchGoalEdited || (state.searchGoalEdited === undefined && state.answers.search_goal)
      ? state.answers : { ...state.answers, search_goal: text } };
}

export function emptyAnswers() {
  return Object.fromEntries(surveyFields.map(field => [field.name, field.kind === 'scale' ? null : '']));
}

export function fieldVisible(field, answers) {
  return !field.visibleIf || answers[field.visibleIf.field] === field.visibleIf.equals;
}

export function visibleFields(fields, answers) {
  return fields.filter(field => fieldVisible(field, answers));
}

export function changeSurveyAnswer(answers, name, value) {
  const next = { ...answers, [name]: value };
  for (const field of surveyFields) if (!fieldVisible(field, next)) next[field.name] = null;
  return next;
}

export function surveyErrors(answers, fields = surveyFields) {
  const errors = {};
  for (const field of visibleFields(fields, answers)) {
    const value = answers[field.name];
    if (field.kind === 'scale') {
      if ((!Number.isInteger(value) || value < 1 || value > 10) && !field.nonresponse?.some(([code]) => code === value)) errors[field.name] = 'Bitte wähle eine Bewertung oder eine der Antworten darunter.';
    } else if (field.kind === 'choice') {
      if (!field.options.some(([option]) => option === value)) errors[field.name] = 'Bitte wähle eine Antwort.';
    } else if (typeof value !== 'string' || value.length > field.maxLength || (!field.optional && value.trim().length < (field.minLength || 1))) {
      errors[field.name] = typeof value === 'string' && value.length > field.maxLength
        ? `Bitte verwende höchstens ${field.maxLength} Zeichen.` : 'Bitte beschreibe dein Suchvorhaben kurz.';
    }
  }
  return errors;
}

export function reviseSurvey(state, changes) {
  return {...state,...changes,draftRevision:Math.max(Date.now(),(state.draftRevision || 0)+1)};
}

export function waitingFieldDone(state, field) {
  return (state.waitingAnswered || []).includes(field.name)
    && !Object.keys(surveyErrors(state.answers,[field])).length;
}

export function remainingWaitingGroups(state) {
  return waitingQuestionGroups.map(group=>({...group,fields:group.fields.filter(field=>fieldVisible(field,state.answers) && !waitingFieldDone(state,field))})).filter(group=>group.fields.length);
}

export function markWaitingFields(state, fields) {
  const valid=fields.filter(field=>fieldVisible(field,state.answers) && !Object.keys(surveyErrors(state.answers,[field])).length).map(field=>field.name);
  return reviseSurvey(state,{...(valid.includes('search_goal')?{searchGoalEdited:true}:{}),waitingAnswered:[...new Set([...(state.waitingAnswered || []),...valid])]});
}

export function finishWaitingIfReady(state) {
  const [demographicGroup,setupGroup]=waitingQuestionGroups;
  if(demographicGroup.fields.every(field=>waitingFieldDone(state,field))
      && !Object.keys(surveyErrors(state.answers,setupGroup.fields)).length) {
    return markWaitingFields(state,setupGroup.fields);
  }
  return state;
}

export function displaySurveyGroup(state, stage=state.stage) {
  const group=stageGroup(stage);
  return group ? {...group,fields:group.fields.filter(field=>fieldVisible(field,state.answers) && !waitingFieldDone(state,field))} : null;
}

export function stageGroup(stage) {
  return stage === 'demographics' ? demographics : surveyCategories.find(group => group.id === stage);
}

// Every next page requires the preceding inputs. Returning to earlier pages
// preserves answers; stored or manually altered navigation cannot skip a page.
export function reachableStage(state, target = state.stage) {
  if (!surveyStages.includes(target)) return 'system';
  if (!state.systemOpened || state.systemCompleted !== true || state.chatCompleted !== true || target === 'system') return 'system';
  if (target === 'demographics') return target;
  if (Object.keys(surveyErrors(state.answers, demographics.fields)).length) return 'demographics';
  const index = surveyCategories.findIndex(group => group.id === target);
  for (const group of surveyCategories.slice(0, index)) {
    if (Object.keys(surveyErrors(state.answers, group.fields)).length) return group.id;
  }
  return target;
}

export function nextSurveyState(state) {
  const index = surveyStages.indexOf(state.stage);
  if (index < 0 || index === surveyStages.length - 1) return state;
  if (state.stage === 'system' && (state.systemCompleted !== true || state.chatCompleted !== true)) return state;
  const group = stageGroup(state.stage);
  if (group && Object.keys(surveyErrors(state.answers, group.fields)).length) return state;
  let nextIndex=index+1;
  while(nextIndex<surveyStages.length-1 && !displaySurveyGroup(state,surveyStages[nextIndex]).fields.length)nextIndex++;
  const next = { ...state, systemOpened: true, stage: surveyStages[nextIndex] };
  return { ...next, stage: reachableStage(next) };
}

export function newSurveyState(cryptoSource = globalThis.crypto) {
  const token = () => Array.from(cryptoSource.getRandomValues(new Uint8Array(16)), byte => byte.toString(16).padStart(2, '0')).join('');
  return { version: SURVEY_VERSION, submissionId: token(), runId: token(), stage: 'system', systemOpened: true, systemCompleted: false, chatCompleted: false, submitted: false, draftRevision:0, waitingAnswered:[], searchGoalSuggestion: '', searchGoalEdited: false, answers: emptyAnswers() };
}

export function loadSurveyState(storage, fresh = newSurveyState) {
  try {
    const state = JSON.parse(storage.getItem(SURVEY_STORAGE_KEY) ?? storage.getItem('diana-survey:diana-v5') ?? storage.getItem('diana-survey:diana-v4') ?? storage.getItem('diana-survey:diana-v3') ?? storage.getItem('diana-survey:diana-v2'));
    if ([SURVEY_VERSION, 'diana-v5', 'diana-v4', 'diana-v3', 'diana-v2'].includes(state?.version) && /^[a-f0-9]{32}$/.test(state.submissionId)
        && /^[a-f0-9]{32}$/.test(state.runId) && surveyStages.includes(state.stage)
        && typeof state.submitted === 'boolean' && typeof state.systemOpened === 'boolean') {
      // Completed old questionnaires must never be resubmitted under a new version.
      if (state.version !== SURVEY_VERSION && state.submitted) return state;
      const migrated = state.version !== SURVEY_VERSION;
      const unchanged = new Set([...demographics.fields.map(field => field.name), 'search_goal']);
      const answers = emptyAnswers();
      for (const field of surveyFields) {
        if (migrated && !unchanged.has(field.name)) continue;
        const value = state.answers?.[field.name];
        // Retain unfinished text drafts, but never restore invalid option values.
        if (field.kind === 'text' && typeof value === 'string' && value.length <= field.maxLength
            || !Object.keys(surveyErrors({ ...state.answers, [field.name]: value }, [field])).length) answers[field.name] = value;
      }
      for (const field of surveyFields) if (!fieldVisible(field, answers)) answers[field.name] = null;
      const submitted = state.submitted && !Object.keys(surveyErrors(answers)).length;
      const restored = { version: submitted ? state.version : SURVEY_VERSION, submissionId: state.submissionId, runId: state.runId,
        stage: state.stage, systemOpened: true, systemCompleted: state.systemCompleted === true, chatCompleted: state.chatCompleted === true,
        submitted, draftRevision:Number.isSafeInteger(state.draftRevision) && state.draftRevision>0 ? state.draftRevision : 0,
        waitingAnswered:Array.isArray(state.waitingAnswered) ? [...new Set(state.waitingAnswered)].filter(name=>waitingQuestionGroups.some(group=>group.fields.some(field=>field.name===name))) : [],
        searchGoalSuggestion: typeof state.searchGoalSuggestion === 'string' && state.searchGoalSuggestion.length <= 1000 ? state.searchGoalSuggestion : '',
        searchGoalEdited: typeof state.searchGoalEdited === 'boolean' ? state.searchGoalEdited : Boolean(answers.search_goal), answers };
      if (migrated) { restored.runId=newSurveyState().runId; restored.systemCompleted=false; restored.chatCompleted=false; restored.stage='system'; restored.waitingAnswered=restored.waitingAnswered.filter(name=>unchanged.has(name)); restored.draftRevision=Math.max(Date.now(),restored.draftRevision+1); }
      return { ...restored, stage: reachableStage(restored) };
    }
  } catch { /* Draft storage is optional. */ }
  return fresh();
}

export function saveSurveyState(storage, state) {
  try { storage.setItem(SURVEY_STORAGE_KEY, JSON.stringify(state)); } catch { /* The form still works in memory. */ }
}

export async function submitSurvey(state, { request = globalThis.fetch, signal } = {}) {
  if (state.systemCompleted !== true) throw new Error('Bitte schließe zuerst die erste Suche mit DIANA ab.');
  if (state.chatCompleted !== true) throw new Error('Bitte sende zuerst eine eigene Nachricht im DIANA-Chat.');
  if (Object.keys(surveyErrors(state.answers)).length) throw new Error('Bitte prüfe deine Antworten.');
  const response = await request('/api/survey-responses', {
    method: 'POST', signal, headers: { ...consentHeaders(), 'Content-Type': 'application/json' },
    body: JSON.stringify({ submission_id: state.submissionId, version: SURVEY_VERSION,
      ...Object.fromEntries(surveyFields.map(field => [field.name, fieldVisible(field, state.answers) ? state.answers[field.name] : null])) }),
  });
  if (response.status === 409) throw new Error('Für diese Teilnahme wurden bereits Antworten gespeichert. Deine nachträglichen Änderungen wurden nicht übernommen.');
  if (!response.ok) throw new Error('Deine Antworten konnten nicht gespeichert werden. Bitte versuche es erneut.');
  let data;
  try { data = await response.json(); } catch { /* An invalid response is never a confirmation. */ }
  if (data?.saved !== true) throw new Error('Die Speicherbestätigung fehlt. Bitte versuche es erneut.');
}

// Only demographic facts and the search goal carry into the new experiment.
const transferableFields=[...demographics.fields.map(field=>field.name),'search_goal'];
export function restoreServerDraft(previous,draft) {
  if(draft.completed)return {...previous,submitted:true};
  if(draft.version===SURVEY_VERSION) {
    if(draft.revision<=(previous.draftRevision || 0))return previous;
    return {...previous,answers:Object.fromEntries(surveyFields.map(field=>[field.name,draft.answers[field.name]??emptyAnswers()[field.name]])),draftRevision:draft.revision,waitingAnswered:draft.waiting_answered || [],searchGoalEdited:true};
  }
  if(['diana-v4','diana-v5'].includes(draft.version)) {
    const answers={...previous.answers};
    for(const name of transferableFields)if(answers[name]==='' || answers[name]===null)answers[name]=draft.answers[name]??answers[name];
    return {...previous,answers,draftRevision:Math.max(previous.draftRevision || 0,draft.revision+1),
      waitingAnswered:[...new Set([...(previous.waitingAnswered || []),...(draft.waiting_answered || []).filter(name=>transferableFields.includes(name))])]};
  }
  return previous;
}
export function applyStudyAssignment(state,assignment) {
  if(!['B','C'].includes(assignment?.arm))throw new Error('Studienzuordnung konnte nicht geladen werden.');
  const answers=changeSurveyAnswer(state.answers,'study_arm',assignment.arm);
  return reviseSurvey(state,{answers,assignment});
}
