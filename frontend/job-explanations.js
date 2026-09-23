import {resultVisibilityKey} from './result-visibility.js';

export function hasJobExplanation(match) {
  return Boolean((match?.reasons?.length ? match.reasons : [match?.reason])
    .some(reason => typeof reason === 'string' && reason.trim()) || match?.matched_skills?.length);
}

export function requireExplanationSession(result, sessionId) {
  if (!result || result.session_id !== sessionId || !Array.isArray(result.jobs)) {
    throw new Error('Die Begründung konnte nicht deiner aktuellen Suche zugeordnet werden.');
  }
  return result;
}

// Adding explanation text must not collapse the twenty already-visible results.
// A genuinely changed ranking still resets expansion through its different key.
export function revealedAfterExplanation(previous, next, revealed) {
  const sameRanking = Array.isArray(previous?.jobs) && Array.isArray(next?.jobs)
    && previous.jobs.length === next.jobs.length
    && previous.jobs.every((job, index) => String(job.id) === String(next.jobs[index].id)
      && job.match?.score === next.jobs[index].match?.score);
  return previous?.session_id === next?.session_id && sameRanking
    && revealed === resultVisibilityKey(previous) ? resultVisibilityKey(next) : revealed;
}
