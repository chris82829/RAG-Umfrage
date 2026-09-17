// All study groups start with the same number of results, regardless of score.
// Expanding the list never changes the ranking, scores or saved candidate pool.
export const INITIAL_RESULT_COUNT = 10;

export function resultVisibility(jobs, showAll = false) {
  return {
    visibleJobs: showAll ? [...jobs] : jobs.slice(0, INITIAL_RESULT_COUNT),
    additionalCount: Math.max(0, jobs.length - INITIAL_RESULT_COUNT),
  };
}

export function resultVisibilityKey(session) {
  return session ? JSON.stringify([session.session_id, session.advisor, session.jobs]) : null;
}
