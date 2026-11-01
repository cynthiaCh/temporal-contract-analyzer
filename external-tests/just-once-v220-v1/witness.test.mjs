// Researcher-authored Node checks, not the upstream Tape suite.
import test, {after} from 'node:test';
import assert from 'node:assert/strict';
import {createRequire} from 'node:module';
import {writeFileSync} from 'node:fs';
const once = createRequire(import.meta.url)(process.env.TCA_MODULE);
const observations = {};
after(() => writeFileSync(process.env.TCA_OBSERVATIONS, JSON.stringify(observations, null, 2) + '\n'));

test('invalid callback arguments are rejected', () => {
  for (const value of [undefined, null, {}, 42]) assert.throws(() => once(value), /expected a function/);
  assert.equal(typeof once(() => {}), 'function');
});

test('sequential calls execute once and cache result', () => {
  let calls = 0;
  const run = once(() => ++calls);
  assert.deepEqual([run(), run(), run()], [1, 1, 1]);
  observations.sequential = {callbackCalls: calls};
  assert.equal(calls, 1);
});

test('first-call arguments are forwarded', () => {
  const received = [];
  const run = once((...args) => { received.push(args); return args[0]; });
  assert.equal(run('first', 42), 'first');
  assert.equal(run('second'), 'first');
  assert.deepEqual(received, [['first', 42]]);
});

test('receiver is preserved', () => {
  const run = once(function () { return this.value; });
  assert.equal(run.call({value: 42}), 42);
  assert.equal(run.call({value: 99}), 42);
});

test('wrappers have independent state', () => {
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
