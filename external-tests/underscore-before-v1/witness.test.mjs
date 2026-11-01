// Researcher-authored tests of the actual standalone before module.
import test, {after} from 'node:test';
import assert from 'node:assert/strict';
import {pathToFileURL} from 'node:url';
import {writeFileSync} from 'node:fs';
const {default: before} = await import(pathToFileURL(process.env.TCA_MODULE).href);
const observations = {};
after(() => writeFileSync(process.env.TCA_OBSERVATIONS, JSON.stringify(observations, null, 2) + '\n'));

test('before(2) executes once and caches result', () => {
  let calls = 0;
  const run = before(2, () => ++calls);
  assert.deepEqual([run(), run(), run()], [1, 1, 1]);
  observations.sequential = {callbackCalls: calls};
  assert.equal(calls, 1);
});

test('before(3) executes twice and caches the last result', () => {
  let calls = 0;
  const run = before(3, () => ++calls);
  assert.deepEqual([run(), run(), run(), run()], [1, 2, 2, 2]);
  observations.limitThree = {callbackCalls: calls};
  assert.equal(calls, 2);
});

test('zero and one limits never execute callback', () => {
  let calls = 0;
  for (const n of [0, 1]) {
    const run = before(n, () => ++calls);
    assert.equal(run(), undefined);
    assert.equal(run(), undefined);
  }
  assert.equal(calls, 0);
});

test('arguments and receiver are forwarded before the cache freezes', () => {
  const received = [];
  const run = before(2, function (a, b) { received.push([this.value, a, b]); return this.value + a + b; });
  assert.equal(run.call({value: 40}, 2, 3), 45);
  assert.equal(run.call({value: 99}, 5, 6), 45);
  assert.deepEqual(received, [[40, 2, 3]]);
});

test('wrappers maintain independent counters', () => {
  let calls = 0;
  const callback = () => ++calls;
  const a = before(2, callback), b = before(2, callback);
  a(); a(); b(); b();
  assert.equal(calls, 2);
});

test('synchronous reentry cannot reuse the before(2) budget', () => {
  let calls = 0;
  const run = before(2, () => {
    calls++;
    if (calls === 1) run();
    return 'done';
  });
  run();
  observations.synchronous = {callbackCalls: calls};
  assert.equal(calls, 1);
});

test('microtask reentry cannot reuse the before(2) budget', async () => {
  let calls = 0;
  const run = before(2, () => {
    calls++;
    if (calls === 1) queueMicrotask(() => run());
  });
  run();
  await new Promise(resolve => queueMicrotask(resolve));
  observations.microtask = {callbackCalls: calls};
  assert.equal(calls, 1);
});
