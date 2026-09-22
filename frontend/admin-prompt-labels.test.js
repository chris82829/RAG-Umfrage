import test from 'node:test';
import assert from 'node:assert/strict';
import {armLabel,promptPolicyLabels,promptSeriesLabel,promptVersionLabel} from './admin-prompt-labels.js';

test('current A is labelled as Basissystem even when its prompt is configurable',()=>{
  assert.equal(armLabel('A','diana-v13'),'A · Basissystem');
  assert.equal(promptPolicyLabels.unprompted,'Basissystem');
});

test('exact prompt labels expose arm, revision and abbreviated base SHA',()=>{
  const item={arm:'A',arms:['A'],policy:'unprompted',revision:3,sha256:'a'.repeat(64),count:7};
  assert.equal(promptVersionLabel(item),'A · Basissystem · Revision 3 · Basis-SHA aaaaaaaaaaaa… · n=7');
  assert.equal(promptSeriesLabel(item,'diana-v13'),'A · Basissystem · Prompt R3 · Basis-SHA aaaaaaaa…');
});
