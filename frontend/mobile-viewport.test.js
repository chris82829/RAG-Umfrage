import test from 'node:test';
import assert from 'node:assert/strict';
import {installMobileViewport,shouldSendOnEnter} from './mobile-viewport.js';

test('touch Enter creates a newline while desktop Enter and explicit shortcuts send',()=>{
 const event={key:'Enter',shiftKey:false,isComposing:false};
 assert.equal(shouldSendOnEnter(event),true);
 assert.equal(Boolean(shouldSendOnEnter(event,true)),false);
 assert.equal(shouldSendOnEnter({...event,ctrlKey:true},true),true);
 assert.equal(shouldSendOnEnter({...event,metaKey:true},true),true);
 for(const change of [{key:'a'},{shiftKey:true},{isComposing:true}])assert.equal(shouldSendOnEnter({...event,...change}),false);
});

test('viewport responds to keyboard resize without breaking pinch zoom and cleans up',()=>{
 const properties=new Map(),classes=new Set(),listeners=new Map();let callback;
 const viewport={height:800,scale:1,addEventListener:(name,fn)=>listeners.set(name,fn),removeEventListener:name=>listeners.delete(name)};
 const host={innerHeight:800,visualViewport:viewport,document:{documentElement:{style:{setProperty:(key,value)=>properties.set(key,value),removeProperty:key=>properties.delete(key)},classList:{toggle:(name,on)=>on?classes.add(name):classes.delete(name),remove:name=>classes.delete(name)}}},addEventListener(){},removeEventListener(){},requestAnimationFrame:fn=>{callback=fn;return 1;},cancelAnimationFrame(){}};
 const cleanup=installMobileViewport(host);
 assert.equal(properties.get('--diana-viewport-height'),'800px');
 viewport.height=430;listeners.get('resize')();callback();
 assert.equal(properties.get('--diana-viewport-height'),'430px');assert.ok(classes.has('diana-keyboard-open'));
 viewport.scale=2;viewport.height=215;listeners.get('resize')();callback();
 assert.equal(properties.get('--diana-viewport-height'),'430px');
 viewport.scale=1;viewport.height=800;listeners.get('resize')();callback();
 assert.equal(properties.get('--diana-viewport-height'),'800px');assert.equal(classes.size,0);
 cleanup();assert.equal(properties.size,0);assert.equal(listeners.size,0);
});
