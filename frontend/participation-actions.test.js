import test from 'node:test';
import assert from 'node:assert/strict';
import {copyParticipationId,deletionEmail} from './participation-actions.js';

function clipboardFallback(result=true){
 const calls=[];
 const input={style:{},focus:()=>calls.push('focus'),select:()=>calls.push('select'),setSelectionRange:(start,end)=>calls.push([start,end]),remove:()=>calls.push('remove')};
 const container={appendChild:element=>{assert.equal(element,input);calls.push('append');}};
 const document={activeElement:{focus:()=>calls.push('restore')},createElement:tag=>{assert.equal(tag,'textarea');return input;},execCommand:command=>{assert.equal(command,'copy');assert.equal(input.value,'DIANA-123');return result;}};
 return {calls,input,container,document};
}
test('modern clipboard copies the exact ID without invoking the fallback',async()=>{
 const copied=[];
 assert.equal(await copyParticipationId('DIANA-123',null,{navigator:{clipboard:{writeText:async value=>copied.push(value)}},document:null}),true);
 assert.deepEqual(copied,['DIANA-123']);
});
test('HTTP without Clipboard API copies inside the dialog and restores focus',async()=>{
 const fallback=clipboardFallback();
 assert.equal(await copyParticipationId('DIANA-123',fallback.container,{navigator:{},document:fallback.document}),true);
 assert.deepEqual(fallback.calls,['append','focus','select',[0,9],'remove','restore']);
});
test('denied Clipboard API uses the fallback',async()=>{
 const fallback=clipboardFallback();
 assert.equal(await copyParticipationId('DIANA-123',fallback.container,{navigator:{clipboard:{writeText:async()=>{throw new Error('NotAllowed');}}},document:fallback.document}),true);
 assert.ok(fallback.calls.includes('select'));
});
test('failed copy never reports success and cleans up the temporary field',async()=>{
 for(const throws of [false,true]){
  const fallback=clipboardFallback(false);
  if(throws)fallback.document.execCommand=()=>{throw new Error('Blocked');};
  assert.equal(await copyParticipationId('DIANA-123',fallback.container,{navigator:{},document:fallback.document}),false);
  assert.deepEqual(fallback.calls.slice(-2),['remove','restore']);
 }
});
test('email draft includes a short deletion request and exact ID in subject and body',()=>{
 const id='DIANA-123'; const link=new URL(deletionEmail(id));
 assert.equal(link.protocol,'mailto:');assert.equal(link.pathname,'christoph.scharnagl@th-nuernberg.de');
 assert.ok(link.searchParams.get('subject').includes(id));
 assert.equal(link.searchParams.get('body'),'Hallo Christoph,\r\n\r\nbitte lösche meine Umfragedaten.\r\nMeine Teilnahme-ID: DIANA-123\r\n\r\nVielen Dank!');
});
