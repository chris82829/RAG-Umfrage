import test from 'node:test';
import assert from 'node:assert/strict';
import React from 'react';
import {renderToStaticMarkup} from 'react-dom/server';
import {createServer} from 'vite';

test('admin charts expose numeric values, escape freetext, and detail dialogs retain answers',async()=>{
 const vite=await createServer({server:{middlewareMode:true,hmr:false,ws:false},appType:'custom'});
 try{
  const {QuestionChart,armLabel}=await vite.ssrLoadModule('/AdminAnalytics.jsx');
  const {default:Metrics}=await vite.ssrLoadModule('/AdminOperationMetrics.jsx');
  const unknown=renderToStaticMarkup(React.createElement(Metrics,{}));
  assert.ok(unknown.includes('keine Laufzeiten'));
  const metrics={capture_version:1,...Object.fromEntries(['search','rerank','chat'].flatMap(kind=>[[`successful_${kind}_count`,1],[`failed_${kind}_count`,0],[`${kind}_duration_ms`,1000]]))};
  const metricMarkup=renderToStaticMarkup(React.createElement(Metrics,{metrics}));
  assert.ok(metricMarkup.includes('1 erfolgreich') && metricMarkup.includes('0 fehlgeschlagen') && metricMarkup.includes('nicht bearbeitbar'));
  assert.ok(metricMarkup.includes('Die Laufzeiten überlappen'));
  const {AdminAnswerDetail,AdminModal,AdminBulkDeleteDialog,AdminResponseScope}=await vite.ssrLoadModule('/AdminPage.jsx');
  for (const value of ['completed','','in_progress']) {
   const scope=renderToStaticMarkup(React.createElement(AdminResponseScope,{value,onChange:()=>{}}));
   assert.ok(scope.includes('Abgeschlossene und unvollständige Umfragen'));
   assert.ok(scope.includes('Gilt sofort für Diagramme, Einzelantworten und Downloads'));
   assert.ok(scope.includes(`value="${value}" selected=""`));
  }
  assert.equal(armLabel('A','diana-v9'),'A · Standardberatung');
  assert.equal(armLabel('B','diana-v9'),'B · Vorlagenauswahl');
  assert.equal(armLabel('B','diana-v8'),'B · Vorlagenauswahl');
  assert.equal(armLabel('C','diana-v8'),'C · Selbst gestaltbar');
  assert.equal(armLabel('B','diana-v7'),'B · Selbst gestaltbar (historisch)');
  const stat={n:1,total:1,mean:8,median:8,statuses:{answered:1},distribution:[{value:8,label:'8',count:1,percent:100}],texts:[],remaining_texts:0};
  const chart=renderToStaticMarkup(React.createElement(QuestionChart,{question:{name:'test',title:'Hilfreich?',kind:'scale',scale:{low:'Gar nicht',high:'Sehr'},overall:stat,groups:{A:stat,B:stat,C:stat}},onSelect:()=>{}}));
  for(const expected of ['Variante A','Variante B','Variante C','Mittelwert','Median 8','n = 1','1 (100 %)','width:100%'])assert.ok(chart.includes(expected),expected);
  const text=renderToStaticMarkup(React.createElement(QuestionChart,{question:{title:'Feedback',kind:'text',overall:{...stat,texts:[{id:'x',text:'<script>bad</script>',arm:'A'}]},groups:{}},onSelect:()=>{}}));
  assert.ok(!text.includes('<script>'));assert.ok(text.includes('&lt;script&gt;'));
  const row={participation_id:'TEST-ID',survey_version:'diana-v7',study_arm:'A',openai_models:[],answers:{search_goal:'Softwareentwicklung'},definition:{demographics:{fields:[{name:'search_goal',title:'Wonach gesucht?'}]},categories:[]}};
  const detail=renderToStaticMarkup(React.createElement(AdminModal,{label:'Einzelantwort',onClose:()=>{}},React.createElement(AdminAnswerDetail,{row,onClose:()=>{},onDelete:()=>{}})));
  assert.ok(detail.includes('<dialog'));assert.ok(detail.includes('Softwareentwicklung'));assert.ok(detail.includes('Einzelantwort schließen'));
  const bulk=renderToStaticMarkup(React.createElement(AdminBulkDeleteDialog,{preview:{responses:12,drafts:3,active_consents:15},onClose:()=>{},onDelete:()=>{}}));
  assert.ok(bulk.includes('12 abgeschlossene Antworten'));assert.ok(bulk.includes('ALLE TEILNAHMEN LÖSCHEN'));assert.match(bulk,/disabled="">Alle Teilnahmen endgültig löschen/);
 }finally{await vite.close();}
});
