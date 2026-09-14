import test from 'node:test';
import assert from 'node:assert/strict';
import React from 'react';
import {renderToStaticMarkup} from 'react-dom/server';
import {createServer} from 'vite';
import {templateSelection, selectionForRequest, selectedTemplate} from './advisor-selection.js';
import {defaultAdvisor} from './advisor.js';

test('explicit own creation remains custom even when the values equal a template',()=>{
  assert.deepEqual(templateSelection('career'),{source:'template',template_id:'career'});
  const custom=templateSelection('');
  assert.equal(selectedTemplate(custom,'career'),'');
  assert.deepEqual(selectionForRequest(custom),{source:'custom',template_id:null});
  assert.equal(selectionForRequest(null),undefined);
  assert.equal(selectionForRequest({source:'unknown',template_id:null}),undefined);
});

test('picker and administration distinguish actual choice from inferred legacy values',async()=>{
  const vite=await createServer({server:{middlewareMode:true,hmr:false,ws:false},appType:'custom'});
  try{
    const {default:Picker}=await vite.ssrLoadModule('/AdvisorPicker.jsx');
    const markup=renderToStaticMarkup(React.createElement(Picker,{value:defaultAdvisor,selection:templateSelection(''),onChange:()=>{}}));
    assert.match(markup,/<input(?=[^>]*type="radio")(?=[^>]*value="")(?=[^>]*checked="")/);
    assert.ok(markup.includes('Eigene Hinweise'));
    const {default:Usage}=await vite.ssrLoadModule('/AdminPersonalityUsage.jsx');
    const old=renderToStaticMarkup(React.createElement(Usage,{usage:{capture_version:0}}));
    assert.ok(old.includes('noch nicht erfasst'));
    const current=renderToStaticMarkup(React.createElement(Usage,{usage:{capture_version:1,initial_source:'template',initial_template_id:'expert',last_source:'custom',ever_custom:true,ever_template:true,selection_change_count:1}}));
    assert.ok(current.includes('Fachexperte') && current.includes('Selbst gestaltet') && current.includes('Selbstauskunft'));
  }finally{await vite.close();}
});
