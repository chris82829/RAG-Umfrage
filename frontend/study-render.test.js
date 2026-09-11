import test from 'node:test';
import assert from 'node:assert/strict';
import React from 'react';
import {renderToStaticMarkup} from 'react-dom/server';
import {createServer} from 'vite';

// SSR checks the actual card and setup markup without a browser or model call.
test('basic cards suppress all rating insights while retaining job details and chat; full cards keep insights',async()=>{
 const originalWindow=globalThis.window;
 globalThis.window={location:{pathname:'/suche',search:''}};
 const vite=await createServer({server:{middlewareMode:true},appType:'custom'});
 try{
  const {JobCard,ProfileForm,AssignedSearch}=await vite.ssrLoadModule('/main.jsx');
  // Direct /suche visits also wait for the server's assignment instead of showing
  // the personalized variant before the participant's actual arm is known.
  const directSearch=renderToStaticMarkup(React.createElement(AssignedSearch));
  assert.ok(directSearch.includes('Dein Systemtest wird vorbereitet'));
  assert.ok(!directSearch.includes('Jetzt Profil erstellen'));
  const job={id:'test-job',company:'Test GmbH',title:'Werkstudent Software',employment_types:['werkstudent'],location:'Nürnberg',remote:'hybrid',professional_fields:['Informatik'],summary:'Produktdaten pflegen.',tasks:'Python-Anwendungen entwickeln.',requirements:'Kenntnisse in Python.',benefits:'Flexible Zeiten.',application_url:'https://example.com/job',match:{score:88,reasons:['Python passt zum Profil.','Die Aufgaben unterstützen dein Lernziel.'],matched_skills:['Python'],missing_skills:['SQL']}};
  const props={job,index:0,ranked:true,scoreLabel:'Test-Score',assistantName:'DIANA-KI',onAsk:()=>{},busy:false};
  const basic=renderToStaticMarkup(React.createElement(JobCard,{...props,showInsights:false}));
  for(const forbidden of ['Test-Score','Warum das passen könnte','Python passt zum Profil.','Die Aufgaben unterstützen dein Lernziel.','Im Profil noch nicht belegt','match-score','skills-list'])assert.ok(!basic.includes(forbidden),forbidden);
  for(const retained of ['Werkstudent Software','Produktdaten pflegen.','Python-Anwendungen entwickeln.','Kenntnisse in Python.','Zur Stellenanzeige','Mit DIANA-KI besprechen'])assert.ok(basic.includes(retained),retained);
  const full=renderToStaticMarkup(React.createElement(JobCard,{...props,showInsights:true}));
  for(const expected of ['Test-Score','Warum das passen könnte','Python passt zum Profil.','Im Profil noch nicht belegt','skills-list'])assert.ok(full.includes(expected),expected);
  const withoutMatch=renderToStaticMarkup(React.createElement(JobCard,{...props,job:{...job,match:undefined},showInsights:false}));
  assert.ok(withoutMatch.includes('Produktdaten pflegen.'));
  const form={query:'Python',skills:'Python',preferences:'Lernen',employment:[],remote:[],hours:'',location:'',cv:''};
  const setupProps={form,step:1,ready:true,advisor:{preset:'neutral',name:'DIANA'},setForm:()=>{},onSubmit:()=>{}};
  const a=renderToStaticMarkup(React.createElement(ProfileForm,{...setupProps,neutral:true}));
  const b=renderToStaticMarkup(React.createElement(ProfileForm,{...setupProps,neutral:false}));
  assert.ok(a.includes('Passende Jobs finden'));assert.ok(!a.includes('Weiter zur Persönlichkeit'));
  assert.ok(b.includes('Weiter zur Persönlichkeit'));
 }finally{await vite.close();if(originalWindow===undefined)delete globalThis.window;else globalThis.window=originalWindow;}
});
