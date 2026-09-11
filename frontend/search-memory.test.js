import test from 'node:test';
import assert from 'node:assert/strict';
import {createMemory,flipMemory} from './search-memory.js';
import {readSearchProgress,searchStatus} from './search-progress.js';

test('memory has three pairs, a card cannot match itself and mismatch blocks further flips',()=>{
  let game=createMemory(()=>.999);
  assert.deepEqual(Object.values(Object.groupBy(game.cards,x=>x)).map(x=>x.length),[2,2,2]);
  game=flipMemory(game,0);
  assert.equal(flipMemory(game,0),game);
  game=flipMemory(game,1);
  assert.equal(game.turns,1);
  assert.equal(flipMemory(game,3),game);
  game={...game,open:[]};
  for (const pair of [[0,3],[1,4],[2,5]]) {
    game=flipMemory(flipMemory(game,pair[0]),pair[1]);
    assert.equal(flipMemory(game,pair[0]),game);
  }
  assert.equal(game.matched.length,6);
  assert.equal(game.turns,4);
  assert.deepEqual(game.open,[]);
  assert.equal(createMemory().matched.length,0);
});

test('status only describes known stages and real counts, never estimated progress',()=>{
  assert.equal(readSearchProgress({stage:'fake',candidate_count:20}),null);
  assert.deepEqual(readSearchProgress({stage:'ranking',candidate_count:-1,job_count:'8537'}),{stage:'ranking'});
  assert.match(searchStatus({stage:'ranking',candidate_count:7}).description,/7 Stellen/);
  assert.doesNotMatch(searchStatus(null).description,/20|8537|%/);
});
