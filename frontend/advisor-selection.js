// Selection records a UI choice, never guesses it from a name or text contents.
export function templateSelection(key) {
  return key === 'career' ? {source:'template',template_id:'career'} : {source:'custom',template_id:null};
}

export function selectionForRequest(selection) {
  if (selection?.source === 'custom') return {source:'custom',template_id:null};
  if (selection?.source === 'template' && selection.template_id === 'career') return {...selection};
  return undefined;
}

export function selectedTemplate(selection, fallback) {
  if (selection?.source === 'custom') return '';
  if (selection?.source === 'template') return selection.template_id;
  return fallback;
}
