export const promptPolicyLabels = {
  unprompted: 'Basissystem',
  career_fixed: 'Top-Berufsberater',
  custom_career: 'Selbst gestaltbare Persönlichkeit',
};

export function armLabel(arm) {
  return {A:'A · Basissystem',B:'B · Top-Berufsberater',C:'C · Selbst gestaltbar'}[arm] || arm;
}

export function promptVersionLabel(item, {count=true}={}) {
  if (!item) return 'Unbekannte Promptfassung';
  const arm = item.arms?.join('/') || item.arm || '–';
  const policy = promptPolicyLabels[item.policy] || item.policy || 'nicht dokumentiert';
  const revision = item.revision === '' || item.revision == null ? '–' : item.revision;
  const sha = item.sha256 ? `${item.sha256.slice(0,12)}…` : 'nicht dokumentiert';
  return `${arm} · ${policy} · Revision ${revision} · Basis-SHA ${sha}${count && item.count != null ? ` · n=${item.count}` : ''}`;
}

export function promptSeriesLabel(item, version) {
  if (!item) return '';
  const base = armLabel(item.arm, version);
  if (!item.policy || item.revision === '' || item.revision == null || !item.sha256) return base;
  return `${base} · Prompt R${item.revision} · Basis-SHA ${item.sha256.slice(0,8)}…`;
}
