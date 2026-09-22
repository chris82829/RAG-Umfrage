import {consentHeaders} from './privacy.js';
import {SURVEY_CHAT_LIMIT} from './chat-limit.js';
import definition from '../survey_definition_v13.json' with { type: 'json' };

export const SURVEY_VERSION = definition.version;
export const SURVEY_STORAGE_KEY = `diana-survey:${SURVEY_VERSION}`;
const demographicsDefinition = {...definition.demographics, fields:definition.demographics.fields.filter(field=>!field.systemProvided)};
const currentFields = [definition.demographics, ...definition.categories].flatMap(group=>group.fields);
const currentWaitingFields = currentFields.filter(field=>field.name==='search_goal');
const configuration = {
  beforeSystemFields: demographicsDefinition.fields.filter(field=>field.beforeSystem),
  demographics: demographicsDefinition, surveyCategories: definition.categories,
  surveyFields: currentFields, surveyScale: definition.scale,
  surveyStages: ['system', 'demographics', ...definition.categories.map(group=>group.id)],
  waitingQuestionFields: currentWaitingFields,
  waitingQuestionGroups: [demographicsDefinition, {id:'setup', title:'Weitere Fragen', fields:currentWaitingFields}],
};
export function surveyConfiguration(version = SURVEY_VERSION) {
  const requested = typeof version==='object' ? version?.version : version;
  if(requested !== SURVEY_VERSION)throw new Error('Diese Fragebogenversion ist nicht verfügbar. Bitte starte eine neue Teilnahme.');
  return configuration;
}
export const {demographics, surveyCategories, surveyFields, surveyScale, surveyStages, waitingQuestionFields, waitingQuestionGroups} = surveyConfiguration();

export function suggestSearchGoal(state, suggestion) {
  if (typeof suggestion !== 'string' || !suggestion.trim() || suggestion.length > 1000 || state.submitted) return state;
  const text = suggestion.trim();
  return { ...state, searchGoalSuggestion: text,
    answers: state.searchGoalEdited || (state.searchGoalEdited === undefined && state.answers.search_goal)
      ? state.answers : { ...state.answers, search_goal: text } };
}

export function emptyAnswers(version = SURVEY_VERSION) {
  return Object.fromEntries(surveyConfiguration(version).surveyFields.map(field => [field.name, field.kind === 'scale' ? null : '']));
}

export function fieldVisible(field, answers) {
  const condition=field.visibleIf;
  return !condition || (condition.in ? condition.in.includes(answers[condition.field]) : answers[condition.field]===condition.equals);
}

export function visibleFields(fields, answers) {
  return fields.filter(field => fieldVisible(field, answers));
}

export function changeSurveyAnswer(answers, name, value, version = SURVEY_VERSION) {
  const next = { ...answers, [name]: value };
  for (const field of surveyConfiguration(version).surveyFields) if (!fieldVisible(field, next)) next[field.name] = null;
  return next;
}

export function surveyErrors(answers, fields = surveyFields) {
  const errors = {};
  for (const field of visibleFields(fields, answers)) {
    const value = answers[field.name];
    if (field.kind === 'scale') {
      if ((!Number.isInteger(value) || value < (field.scale?.min ?? surveyScale.min) || value > (field.scale?.max ?? surveyScale.max)) && !field.nonresponse?.some(([code]) => code === value)) errors[field.name] = 'Bitte wähle eine Bewertung oder eine der Antworten darunter.';
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
  return surveyConfiguration(state).waitingQuestionGroups.map(group=>({...group,fields:group.fields.filter(field=>fieldVisible(field,state.answers) && !waitingFieldDone(state,field))})).filter(group=>group.fields.length);
}

export function markWaitingFields(state, fields) {
  const valid=fields.filter(field=>fieldVisible(field,state.answers) && !Object.keys(surveyErrors(state.answers,[field])).length).map(field=>field.name);
  return reviseSurvey(state,{...(valid.includes('search_goal')?{searchGoalEdited:true}:{}),waitingAnswered:[...new Set([...(state.waitingAnswered || []),...valid])]});
}

export function finishWaitingIfReady(state) {
  const [demographicGroup,setupGroup]=surveyConfiguration(state).waitingQuestionGroups;
  if(demographicGroup.fields.every(field=>waitingFieldDone(state,field))
      && !Object.keys(surveyErrors(state.answers,setupGroup.fields)).length) {
    return markWaitingFields(state,setupGroup.fields);
  }
  return state;
}

export function displaySurveyGroup(state, stage=state.stage) {
  const group=stageGroup(stage,state.version);
  return group ? {...group,fields:group.fields.filter(field=>fieldVisible(field,state.answers) && !waitingFieldDone(state,field))} : null;
}

export function stageGroup(stage, version = SURVEY_VERSION) {
  const {demographics,surveyCategories}=surveyConfiguration(version);
  return stage === 'demographics' ? demographics : surveyCategories.find(group => group.id === stage);
}

export function hasRequiredStudyChat(state) {
  return state.chatCompleted === true && Number.isInteger(state.chatCount) && state.chatCount >= SURVEY_CHAT_LIMIT;
}

// Every next page requires preceding inputs from the assigned questionnaire.
export function reachableStage(state, target = state.stage) {
  const {surveyStages,demographics,surveyCategories}=surveyConfiguration(state);
  if (!surveyStages.includes(target)) return 'system';
  if (!state.systemOpened || state.systemCompleted !== true || !hasRequiredStudyChat(state) || target === 'system') return 'system';
  if (target === 'demographics') return target;
  if (Object.keys(surveyErrors(state.answers, demographics.fields)).length) return 'demographics';
  const index = surveyCategories.findIndex(group => group.id === target);
  for (const group of surveyCategories.slice(0, index)) {
    if (Object.keys(surveyErrors(state.answers, group.fields)).length) return group.id;
  }
  return target;
}

export function nextSurveyState(state) {
  const {surveyStages}=surveyConfiguration(state);
  const index = surveyStages.indexOf(state.stage);
  if (index < 0 || index === surveyStages.length - 1) return state;
  if (state.stage === 'system' && (state.systemCompleted !== true || !hasRequiredStudyChat(state))) return state;
  const group = stageGroup(state.stage,state.version);
  if (group && Object.keys(surveyErrors(state.answers, group.fields)).length) return state;
  let nextIndex=index+1;
  while(nextIndex<surveyStages.length-1 && !displaySurveyGroup(state,surveyStages[nextIndex]).fields.length)nextIndex++;
  const next = { ...state, systemOpened: true, stage: surveyStages[nextIndex] };
  return { ...next, stage: reachableStage(next) };
}

export function newSurveyState(cryptoSource = globalThis.crypto) {
  const token = () => Array.from(cryptoSource.getRandomValues(new Uint8Array(16)), byte => byte.toString(16).padStart(2, '0')).join('');
  return { version: SURVEY_VERSION, submissionId: token(), runId: token(), stage: 'system', systemTaskStarted: false, systemOpened: true, systemCompleted: false, chatCompleted: false, chatCount: 0, submitted: false, draftRevision:0, waitingAnswered:[], searchGoalSuggestion: '', searchGoalEdited: false, answers: emptyAnswers() };
}

function sanitizeAnswers(source,version) {
  const answers=emptyAnswers(version), fields=surveyConfiguration(version).surveyFields;
  for(const field of fields) {
    const value=source?.[field.name];
    if(field.kind==='text' && typeof value==='string' && value.length<=field.maxLength
        || !Object.keys(surveyErrors({...source,[field.name]:value},[field])).length)answers[field.name]=value;
  }
  for(const field of fields)if(!fieldVisible(field,answers))answers[field.name]=null;
  return answers;
}

export function loadSurveyState(storage, fresh = newSurveyState) {
  try {
    // Retired questionnaires must not reappear after the study has been reset.
    if(typeof storage.key==='function' && typeof storage.removeItem==='function') {
      const retired=[];
      for(let index=0;index<storage.length;index++) {
        const key=storage.key(index);
        if(key?.startsWith('diana-survey:') && key!==SURVEY_STORAGE_KEY)retired.push(key);
      }
      retired.forEach(key=>storage.removeItem(key));
    }
    const state=JSON.parse(storage.getItem(SURVEY_STORAGE_KEY) || 'null');
    if (state?.version===SURVEY_VERSION && /^[a-f0-9]{32}$/.test(state.submissionId)
        && /^[a-f0-9]{32}$/.test(state.runId) && typeof state.submitted==='boolean' && typeof state.systemOpened==='boolean') {
      const version=SURVEY_VERSION;
      const {surveyStages,waitingQuestionGroups,surveyFields}=surveyConfiguration(version);
      if(!surveyStages.includes(state.stage))return fresh();
      const answers=sanitizeAnswers(state.answers,version);
      const restored={...state,version,answers,systemOpened:true,systemCompleted:state.systemCompleted===true,chatCompleted:state.chatCompleted===true,
        submitted:state.submitted && !Object.keys(surveyErrors(answers,surveyFields)).length,
        draftRevision:Number.isSafeInteger(state.draftRevision) && state.draftRevision>0?state.draftRevision:0,
        waitingAnswered:Array.isArray(state.waitingAnswered)?[...new Set(state.waitingAnswered)].filter(name=>waitingQuestionGroups.some(group=>group.fields.some(field=>field.name===name))):[],
        searchGoalSuggestion:typeof state.searchGoalSuggestion==='string' && state.searchGoalSuggestion.length<=1000?state.searchGoalSuggestion:'',
        searchGoalEdited:typeof state.searchGoalEdited==='boolean'?state.searchGoalEdited:Boolean(answers.search_goal)};
      return {...restored,stage:reachableStage(restored)};
    }
  } catch { /* Draft storage is optional. */ }
  return fresh();
}

export function saveSurveyState(storage, state) {
  try { if(state.version===SURVEY_VERSION)storage.setItem(SURVEY_STORAGE_KEY, JSON.stringify(state)); } catch { /* The form still works in memory. */ }
}

export async function submitSurvey(state, { request = globalThis.fetch, signal } = {}) {
  const {surveyFields}=surveyConfiguration(state);
  if (state.systemCompleted !== true) throw new Error('Bitte schließe zuerst die erste Suche mit DIANA ab.');
  if (!hasRequiredStudyChat(state)) throw new Error('Bitte schließe zuerst drei eigene Nachrichten im DIANA-Chat ab.');
  if (Object.keys(surveyErrors(state.answers,surveyFields)).length) throw new Error('Bitte prüfe deine Antworten.');
  const response = await request('/api/survey-responses', {
    method: 'POST', signal, headers: { ...consentHeaders(), 'Content-Type': 'application/json' },
    body: JSON.stringify({ submission_id: state.submissionId, version: state.version,
      ...Object.fromEntries(surveyFields.map(field => [field.name, fieldVisible(field, state.answers) ? state.answers[field.name] : null])) }),
  });
  if (response.status === 409) throw new Error('Für diese Teilnahme wurden bereits Antworten gespeichert. Deine nachträglichen Änderungen wurden nicht übernommen.');
  if (!response.ok) throw new Error('Deine Antworten konnten nicht gespeichert werden. Bitte versuche es erneut.');
  let data;
  try { data = await response.json(); } catch { /* An invalid response is never a confirmation. */ }
  if (data?.saved !== true) throw new Error('Die Speicherbestätigung fehlt. Bitte versuche es erneut.');
}

export function restoreServerDraft(previous,draft) {
  if(draft.version!==SURVEY_VERSION)return previous;
  if(draft.completed)return {...previous,submitted:true};
  if(draft.version===previous.version && draft.revision<=(previous.draftRevision || 0))return previous;
  const restored={...previous,version:draft.version,answers:sanitizeAnswers(draft.answers,draft.version),draftRevision:draft.revision,waitingAnswered:draft.waiting_answered || [],searchGoalEdited:true};
  return {...restored,stage:reachableStage(restored)};
}

export function applyStudyAssignment(state,assignment) {
  if(!['A','B','C'].includes(assignment?.arm))throw new Error('Studienzuordnung konnte nicht geladen werden.');
  const version=assignment.questionnaire_version;
  if(version!==SURVEY_VERSION)throw new Error('Diese Fragebogenversion ist nicht verfügbar. Bitte starte eine neue Teilnahme.');
  const next=state.version===SURVEY_VERSION ? state : newSurveyState();
  const answers=changeSurveyAnswer(next.answers,'study_arm',assignment.arm,version);
  const progress=assignment.chat_progress;
  const chatCount=Number.isInteger(progress?.used) && progress.used >= 0 ? progress.used : 0;
  return reviseSurvey(next,{answers,assignment,chatCount,chatCompleted:progress?.can_proceed===true && chatCount>=SURVEY_CHAT_LIMIT});
}

// The same preparation precedes the current conference-study system in every arm.
export function needsSystemPreparation(state) {
  const fields=surveyConfiguration(state).beforeSystemFields;
  const startedOnServer=fields.length>0 && fields.every(field=>waitingFieldDone(state,field));
  return state.version===SURVEY_VERSION && !state.systemTaskStarted && !startedOnServer && !state.systemCompleted && !state.submitted;
}
export function startPreparedSystem(state) {
  const fields=surveyConfiguration(state).beforeSystemFields;
  if(Object.keys(surveyErrors(state.answers,fields)).length)return state;
  return reviseSurvey(markWaitingFields(state,fields),{systemTaskStarted:true});
}
