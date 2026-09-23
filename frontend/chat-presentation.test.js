import test from 'node:test';
import assert from 'node:assert/strict';
import {jobReferenceParts, separateFollowUp, previewParts, jobNavigationTarget} from './chat-presentation.js';

const jobs = [{id:'123',title:'Python Developer',company:'Daten AG'},
  {id:'456',title:'Data Analyst',company:'Daten AG'},
  {id:'789',title:'Data Analyst',company:'Andere GmbH'}];
test('references resolve only current IDs and display the canonical title', () => {
  const parts=jobReferenceParts('Hier: [Kurz](job:456). [Fremd](job:999) und <script>bad()</script>',jobs);
  assert.deepEqual(parts.filter(p=>p.job).map(p=>[p.text,p.job.id]),[['Data Analyst','456']]);
  assert.ok(parts.some(p=>p.text.includes('<script>'))); // Rendered as React text, never HTML.
  assert.equal(jobReferenceParts('[X](javascript:alert(1))',jobs).some(p=>p.job),false);
});
test('older unambiguous names work; ambiguous titles and company names do not guess a job', () => {
  assert.deepEqual(jobReferenceParts('Python Developer bei Daten AG. Data Analyst.',jobs).filter(p=>p.job).map(p=>p.job.id),['123']);
  assert.equal(jobReferenceParts('Python Developers',jobs).some(p=>p.job),false);
});
test('question is separate with or without model paragraph breaks', () => {
  assert.deepEqual(separateFollowUp('Einige Stellen sind in Erlangen. Möchtest du München bevorzugen?'),
    {body:'Einige Stellen sind in Erlangen.',question:'Möchtest du München bevorzugen?'});
  assert.deepEqual(separateFollowUp('Die Stelle passt.\n\n**Welche Technologie bevorzugst du?**'),
    {body:'Die Stelle passt.',question:'Welche Technologie bevorzugst du?'});
  assert.deepEqual(separateFollowUp('Python passt.'),{body:'Python passt.',question:''});
  assert.deepEqual(separateFollowUp('Was ist dir wichtig?'),{body:'',question:'Was ist dir wichtig?'});
});
test('long message preview never cuts an interactive reference in half', () => {
  const parts=[{text:'Wort '.repeat(120)},{text:'Python Developer',job:jobs[0]},{text:' Ende'.repeat(100)}];
  const preview=previewParts(parts);
  assert.equal(preview.find(p=>p.job)?.text,'Python Developer');
  assert.equal(preview.at(-1).text,' …');
  const short=[{text:'Kurz'}];assert.equal(previewParts(short),short);
});
test('job links reveal hidden results and never invent a navigation target', () => {
  const all=Array.from({length:20},(_,i)=>({id:String(i)}));
  assert.equal(jobNavigationTarget(all,'17').revealAll,true);
  assert.equal(jobNavigationTarget(all,'2').revealAll,false);
  assert.equal(jobNavigationTarget(all,'missing'),null);
});
test('streamed incomplete job-link syntax stays out of visible text', () => {
  assert.equal(jobReferenceParts('[Python Developer](job:1',jobs).map(p=>p.text).join(''),'Python Developer');
});
