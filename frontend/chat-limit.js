export const SURVEY_CHAT_LIMIT = 3;

export function chatAllowance(session, { testPage = false } = {}) {
  const historyCount = (session?.messages || []).filter(message => message.role === 'user'
    && typeof message.content === 'string' && message.content.trim()).length;
  const usage = session?.chat_usage;
  const used = Math.max(historyCount, Number.isInteger(usage?.used) && usage.used >= 0 ? usage.used : 0);
  if (testPage) return { limit: null, used, pending: 0, remaining: null, blocked: false, exhausted: false };
  const pending = Number.isInteger(usage?.pending) && usage.pending >= 0 ? usage.pending : 0;
  const available = Math.max(0, SURVEY_CHAT_LIMIT - used - pending);
  const remaining = Number.isInteger(usage?.remaining) && usage.remaining >= 0
    ? Math.min(available, usage.remaining) : available;
  return { limit: SURVEY_CHAT_LIMIT, used, pending, remaining,
    blocked: remaining === 0, exhausted: used >= SURVEY_CHAT_LIMIT };
}
