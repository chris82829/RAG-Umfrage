import test from 'node:test';
import assert from 'node:assert/strict';
import {jobReferenceParts, plainJobReferences, separateFollowUp, previewParts, jobNavigationTarget, removeChatGenderSuffixes, chatContentBlocks} from './chat-presentation.js';

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
test('escaped internal links display canonical titles and keep exact navigation targets', () => {
  for (const value of [String.raw`[Kurz]\(job:456)`, String.raw`[Kurz]\(job:456\)`,
    String.raw`\[Kurz\]\(job:456\)`, '[Kurz] (job:456)', '[Kurz](job:%34%35%36)']) {
    assert.deepEqual(jobReferenceParts(value,jobs).map(part=>[part.text,part.job?.id]),[['Data Analyst','456']],value);
  }
});
test('unknown escaped references show only labels and cannot invent navigation', () => {
  const parts=jobReferenceParts(String.raw`[**Unbekannte Stelle**]\(job:999\)`,jobs);
  assert.deepEqual(parts,[{text:'Unbekannte Stelle'}]);
  assert.equal(jobReferenceParts('Hinweis (job:999)',jobs).map(part=>part.text).join(''),'Hinweis ');
});
test('every streamed prefix of escaped or normal job markup hides technical fragments', () => {
  for (const value of ['[Python Developer](job:123)', String.raw`[Python Developer]\(job:123\)`,
    String.raw`\[Python Developer\]\(job:123\)`]) {
    for (let length=1;length<=value.length;length++) {
      const visible=jobReferenceParts(value.slice(0,length),jobs).map(part=>part.text).join('');
      assert(!/[\[\]\\]|job:|123/.test(visible),`${value.slice(0,length)} => ${visible}`);
    }
  }
});
test('job references preserve concise bullet lines and the follow-up paragraph', () => {
  const {body,question}=separateFollowUp(String.raw`- [Kurz]\(job:456): SQL passt.
- Python Developer: Python passt.

Möchtest du eher SQL oder Python nutzen?`);
  const parts=jobReferenceParts(body,jobs);
  assert.equal(parts.map(part=>part.text).join(''),'- Data Analyst: SQL passt.\n- Python Developer: Python passt.');
  assert.equal(question,'Möchtest du eher SQL oder Python nutzen?');
  assert.equal(parts.find(part=>part.job)?.job.id,'456');
});
test('chat gender suffixes are removed while technical parentheses and line breaks remain', () => {
  for (const suffix of ['(m/w/d)','(w/m/d)','(m|w|d)','(f/m/d)','(m/w/x)','( W / M / D )']) {
    assert.equal(removeChatGenderSuffixes(`Data Analyst ${suffix} bei Example (Python)\nSQL (SQL)`),
      'Data Analyst bei Example (Python)\nSQL (SQL)');
  }
  assert.equal(removeChatGenderSuffixes('Data Analyst (Python) oder (Machine Learning)'),
    'Data Analyst (Python) oder (Machine Learning)');
});
test('cleaned titles remain navigable with or without gender suffix and keep original job data', () => {
  const genderJob={id:'321',title:'Python Developer (m/w/d)',company:'Beispiel'};
  for(const text of ['Python Developer (m/w/d)','Python Developer','[Kurz](job:321)',String.raw`[Kurz]\(job:321)`]) {
    const parts=jobReferenceParts(text,[genderJob]);
    assert.deepEqual(parts.map(part=>[part.text,part.job?.id]),[['Python Developer','321']]);
    assert.equal(parts[0].job,genderJob);
  }
  assert.equal(genderJob.title,'Python Developer (m/w/d)');
});
test('titles that become ambiguous after suffix removal never infer a target', () => {
  const similar=[{id:'1',title:'Data Analyst (m/w/d)',company:'Firma A'},
    {id:'2',title:'Data Analyst (f/m/d)',company:'Firma B'}];
  for(const text of ['Data Analyst','Data Analyst (m/w/d)','Data Analyst (f/m/d)']) {
    const parts=jobReferenceParts(text,similar);
    assert.equal(parts.some(part=>part.job),false);
    assert.equal(parts.map(part=>part.text).join(''),'Data Analyst');
  }
  assert.equal(jobReferenceParts('[Data Analyst](job:2)',similar)[0].job.id,'2');
});
test('streaming gender suffix tokens do not flash back after a cleaned title', () => {
  for(const suffix of ['(m/w/d)','(w/m/d)','(f/m/d)','(m|w|d)','(m/w/x)']) {
    for(let length=2;length<=suffix.length;length++) {
      assert.equal(removeChatGenderSuffixes(`Data Analyst ${suffix.slice(0,length)}`,true),'Data Analyst');
    }
  }
  assert.equal(removeChatGenderSuffixes('Data Analyst (Python)',true),'Data Analyst (Python)');
  assert.equal(removeChatGenderSuffixes('Data Analyst (Machine Learning)',true),'Data Analyst (Machine Learning)');
});

test('readable job blocks separate titles and explanations without truncation',()=>{
  const text='Hallo! 20 Stellen gefunden.\n\n- Python Developer: Deine Python-Kenntnisse passen zu den Aufgaben.\n\n- Data Analyst: Hier kannst du mit SQL arbeiten.';
  const blocks=chatContentBlocks(text);
  assert.equal(blocks.length,2);
  assert.equal(blocks[0].type,'paragraph');
  assert.deepEqual(blocks[1],{type:'jobs',items:[
    {title:'Python Developer',description:'Deine Python-Kenntnisse passen zu den Aufgaben.'},
    {title:'Data Analyst',description:'Hier kannst du mit SQL arbeiten.'},
  ]});
  assert.equal(removeChatGenderSuffixes('Python… SQL... Version 3.12'), 'Python SQL Version 3.12');
});

test('baseline references become plain labels without IDs or interactive metadata', () => {
  assert.equal(plainJobReferences('Hier: [Kurz](job:123). [Andere](job:999)', jobs),
    'Hier: Python Developer. Andere');
  assert.equal(typeof plainJobReferences('Python Developer', jobs), 'string');
});


test('only job titles become links; even unique company names and locations stay plain', () => {
  const job={id:'813447',title:'Werkstudent/Praktikant Data Engineering mit Python (m/w/d)',company:'Wieland-Werke AG',location:'Ulm'};
  const text='Empfehlung: Werkstudent/Praktikant Data Engineering mit Python bei Wieland-Werke AG, Ulm.';
  const parts=jobReferenceParts(text,[job]);
  assert.deepEqual(parts.filter(part=>part.job).map(part=>part.text),['Werkstudent/Praktikant Data Engineering mit Python']);
  assert.equal(parts.map(part=>part.text).join(''),text);
  assert.equal(jobReferenceParts('Wieland-Werke AG, Ulm.',[job]).some(part=>part.job),false);
});


test('MEAG title with omitted im Bereich links only the title, not company or place', () => {
  const job={id:'853303',title:'Werkstudent im Bereich Data Management (m|w|d)',company:'MEAG MUNICH ERGO AssetManagement GmbH'};
  const text='Werkstudent Data Management bei MEAG Munich Re AssetManagement (München, hybrid)';
  const parts=jobReferenceParts(text,[job]);
  assert.deepEqual(parts.filter(p=>p.job).map(p=>[p.text,p.job.id]),[['Werkstudent Data Management','853303']]);
  assert.equal(parts.map(p=>p.text).join(''),text);
});

test('gender marker inside title and variable whitespace still resolve correctly', () => {
  const job={id:'819942',title:'Werkstudent (m|w|d) Data Management',company:'MEAG'};
  for (const text of ['Werkstudent Data Management','Werkstudent  Data Management','Werkstudent (m|w|d) Data Management'])
    assert.equal(jobReferenceParts(text,[job]).find(p=>p.job)?.job.id,'819942');
});

test('shortened ambiguous titles never select an arbitrary job', () => {
  const jobs=[{id:'1',title:'Werkstudent im Bereich Data Management',company:'MEAG'},
    {id:'2',title:'Werkstudent Data Management',company:'Andere Firma'}];
  assert.equal(jobReferenceParts('Werkstudent Data Management',jobs).some(p=>p.job),false);
  assert.equal(jobReferenceParts('Werkstudent im Bereich Data Management',jobs).find(p=>p.job)?.job.id,'1');
  assert.equal(jobReferenceParts('Werkstudent Data Science',jobs).some(p=>p.job),false);
});

test('plain titles remain linked alongside explicit references in the same message', () => {
  const parts=jobReferenceParts('[Kurz](job:123) und Data Analyst',[jobs[0],jobs[1]]);
  assert.deepEqual(parts.filter(p=>p.job).map(p=>p.job.id),['123','456']);
});

test('title punctuation inside a reference does not split a job bullet or follow-up',()=>{
 const title='Werkstudent: Data Engineering bei Dr. Beispiel';
 const text=`- [${title}](job:17): Python passt.\n\nMöchtest du [${title}](job:17)?`;
 const {body,question}=separateFollowUp(text);
 assert.equal(question,`Möchtest du [${title}](job:17)?`);
 const [block]=chatContentBlocks(body);
 assert.equal(block.items[0].title,`[${title}](job:17)`);
 assert.equal(block.items[0].description,'Python passt.');
 assert.equal(jobReferenceParts(block.items[0].title,[{id:'17',title}]).filter(p=>p.job).length,1);
});
