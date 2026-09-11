import test from 'node:test';
import assert from 'node:assert/strict';
import {readSearchProgress,searchStatus} from './search-progress.js';

test('status only describes known stages and real counts, never estimated progress',()=>{
  assert.equal(readSearchProgress({stage:'fake',candidate_count:20}),null);
  assert.deepEqual(readSearchProgress({stage:'ranking',candidate_count:-1,job_count:'8537'}),{stage:'ranking'});
  assert.match(searchStatus({stage:'ranking',job_count:8192,candidate_count:7}).title,/8.192 Stellen durchsucht/);
  assert.doesNotMatch(searchStatus(null).description,/20|8537|%/);
});
