import test from 'node:test';
import assert from 'node:assert/strict';
import React from 'react';
import {renderToStaticMarkup} from 'react-dom/server';
import {createServer} from 'vite';
import {updateAnswer, changedAnswers, answerVisible} from './admin-answer-editor.js';

const definition={demographics:{fields:[{name:'study_arm',title:'Gruppe',kind:'choice',options:[['A','Neutral'],['B','Personalisiert']]}]},categories:[{fields:[{name:'chat_used',title:'Chat genutzt?',kind:'choice',options:[['yes','Ja'],['no','Nein']]},{name:'chat_helpfulness',title:'Chat hilfreich?',kind:'scale',visibleIf:{field:'chat_used',equals:'yes'}},{name:'feedback',title:'Feedback',kind:'text',optional:true,maxLength:4000}]}]};

test('editing stages values without mutating originals and clears skipped dependent questions',()=>{
 const original={study_arm:'A',chat_used:'yes',chat_helpfulness:8,feedback:''};
 const edited=updateAnswer(original,'chat_used','no',definition);
 assert.deepEqual(original,{study_arm:'A',chat_used:'yes',chat_helpfulness:8,feedback:''});
 assert.equal(edited.chat_helpfulness,null);
 assert.deepEqual(changedAnswers(original,edited),['chat_used','chat_helpfulness']);
 assert.equal(updateAnswer(original,'study_arm','B',definition),original);
});

test('editor exposes explicit save, version-specific fields, immutable assignment and accessible audit',async()=>{
 const vite=await createServer({server:{middlewareMode:true,hmr:false,ws:false},appType:'custom'});
 try{
  const {default:Editor,AdminCorrectionHistory}=await vite.ssrLoadModule('/AdminAnswerEditor.jsx');
  const row={definition,answers:{study_arm:'A',chat_used:'no',chat_helpfulness:null,feedback:'<script>test</script>'},response_status:'completed',edit_revision:'a'.repeat(64)};
  const markup=renderToStaticMarkup(React.createElement(Editor,{row,onCancel:()=>{},onSave:()=>{}}));
  assert.ok(markup.includes('Korrektur speichern') && markup.includes('Änderungen verwerfen'));
  assert.ok(markup.includes('Grund für die Korrektur') && markup.includes('noch nicht gespeichert'));
  assert.ok(markup.includes('Neutral · fest zugeordnet'));
  assert.ok(!markup.includes('Chat hilfreich?'));
  assert.match(markup,/disabled="">Korrektur speichern/);
  assert.ok(!markup.includes('<script>'));
  const legacy={...row,definition:{demographics:{fields:[{name:'chat_helpfulness',title:'Hilfe',kind:'scale',minimum:1,maximum:5}]},categories:[]},answers:{chat_helpfulness:4}};
  const old=renderToStaticMarkup(React.createElement(Editor,{row:legacy,onCancel:()=>{},onSave:()=>{}}));
  assert.ok(old.includes('value="5"') && !old.includes('value="6"'));
  const history=renderToStaticMarkup(React.createElement(AdminCorrectionHistory,{row:{...row,correction_count:1,corrections:[{corrected_at:'2026-09-14T12:00:00Z',reason:'<script>reason</script>',changes:[{field:'feedback',before:'original',after:'corrected'}]}]}}));
  assert.ok(history.includes('Vorher: original') && history.includes('Gespeichert: corrected'));
  assert.ok(!history.includes('<script>'));
 }finally{await vite.close();}
});


test('v8 shared B/C questions remain visible and C-only settings stay separate',()=>{
 const shared={name:'score_usefulness',visibleIf:{field:'study_arm',in:['B','C']}};
 const custom={name:'personality_setup',visibleIf:{field:'study_arm',equals:'C'}};
 assert.equal(answerVisible(shared,{study_arm:'A'}),false);
 assert.equal(answerVisible(shared,{study_arm:'B'}),true);
 assert.equal(answerVisible(shared,{study_arm:'C'}),true);
 assert.equal(answerVisible(custom,{study_arm:'B'}),false);
 assert.equal(answerVisible(custom,{study_arm:'C'}),true);
 const def={demographics:{fields:[]},categories:[{fields:[shared,custom]}]};
 const edited=updateAnswer({study_arm:'B',score_usefulness:8,personality_setup:null},'score_usefulness',9,def);
 assert.equal(edited.score_usefulness,9);
 assert.equal(edited.personality_setup,null);
});
