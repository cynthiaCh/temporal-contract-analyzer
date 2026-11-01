// Researcher-authored checks of the pinned once module and its real helpers.
import test, {after} from 'node:test';
import assert from 'node:assert/strict';
import {pathToFileURL} from 'node:url';
import {writeFileSync} from 'node:fs';
const {default: once} = await import(pathToFileURL(process.env.TCA_MODULE).href);
const observations = {};
after(() => writeFileSync(process.env.TCA_OBSERVATIONS, JSON.stringify(observations, null, 2) + '\n'));

test('sequential calls invoke once and cache result', () => {
  let calls = 0;
  const run = once(() => ++calls);
  assert.deepEqual([run(), run(), run()], [1, 1, 1]);
  observations.sequential = {callbackCalls: calls};
  assert.equal(calls, 1);
});

test('first-call arguments and result remain cached', () => {
  const received = [];
  const run = once(function (a, b) { received.push([a, b]); return a + b; });
  assert.equal(run(5, 10), 15);
  assert.equal(run(20, 30), 15);
  assert.deepEqual(received, [[5, 10]]);
});

test('receiver is preserved', () => {
  const run = once(function () { return this.value; });
  assert.equal(run.call({value: 42}), 42);
  assert.equal(run.call({value: 99}), 42);
});

test('arity is preserved by the real internal helper', () => {
  const run = once(function (a, b) { return a + b; });
  assert.equal(run.length, 2);
  assert.equal(run(1, 2), 3);
});

test('zero argument and placeholder currying preserve factory', () => {
  assert.equal(once(), once);
  assert.equal(once({'@@functional/placeholder': true}), once);
  const run = once()(() => 42);
  assert.equal(run(), 42);
});

test('wrappers maintain independent state', () => {
  let calls = 0;
  const callback = () => ++calls;
  const a = once(callback), b = once(callback);
  a(); a(); b(); b();
  assert.equal(calls, 2);
});

test('synchronous reentry does not invoke callback twice', () => {
  let calls = 0;
  const run = once(() => {
    calls++;
    if (calls === 1) run();
    return 'done';
  });
  run();
  observations.synchronous = {callbackCalls: calls};
  assert.equal(calls, 1);
});

test('microtask reentry does not invoke callback twice', async () => {
  let calls = 0;
  const run = once(() => {
    calls++;
    if (calls === 1) queueMicrotask(() => run());
  });
  run();
  await new Promise(resolve => queueMicrotask(resolve));
  observations.microtask = {callbackCalls: calls};
  assert.equal(calls, 1);
});
