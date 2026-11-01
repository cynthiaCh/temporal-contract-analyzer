// A negative control: repeated callbacks after activation are intended behavior.
import test, {after as afterTests} from 'node:test';
import assert from 'node:assert/strict';
import {pathToFileURL} from 'node:url';
import {writeFileSync} from 'node:fs';
const {default: after} = await import(pathToFileURL(process.env.TCA_MODULE).href);
const observations = {};
afterTests(() => writeFileSync(process.env.TCA_OBSERVATIONS, JSON.stringify(observations, null, 2) + '\n'));

test('after(3) begins at the third call and executes every later call', () => {
  let calls = 0;
  const run = after(3, () => ++calls);
  const values = [run(), run(), run(), run(), run()];
  assert.deepEqual(values, [undefined, undefined, 1, 2, 3]);
  observations.activation = {values: values.map(x => x === undefined ? 'undefined' : x), callbackCalls: calls};
});

test('zero and one activate on the first call and keep executing', () => {
  for (const n of [0, 1]) {
    let calls = 0;
    const run = after(n, () => ++calls);
    assert.deepEqual([run(), run(), run()], [1, 2, 3]);
  }
});

test('eligible calls forward new receiver and arguments each time', () => {
  const received = [];
  const run = after(1, function (a) { received.push([this.value, a]); return this.value + a; });
  assert.equal(run.call({value: 40}, 2), 42);
  assert.equal(run.call({value: 99}, 1), 100);
  assert.deepEqual(received, [[40, 2], [99, 1]]);
});

test('wrappers have independent activation counters', () => {
  let calls = 0;
  const callback = () => ++calls;
  const a = after(2, callback), b = after(2, callback);
  assert.equal(a(), undefined); assert.equal(b(), undefined);
  assert.equal(a(), 1); assert.equal(b(), 2);
});

test('synchronous reentry after activation is an eligible additional call', () => {
  let calls = 0;
  const run = after(2, () => {
    calls++;
    if (calls === 1) run();
    return 'done';
  });
  assert.equal(run(), undefined);
  assert.equal(run(), 'done');
  observations.synchronous = {callbackCalls: calls};
  assert.equal(calls, 2);
});

test('microtask reentry after activation is also an eligible call', async () => {
  let calls = 0;
  const run = after(2, () => {
    calls++;
    if (calls === 1) queueMicrotask(() => run());
  });
  run(); run();
  await new Promise(resolve => queueMicrotask(resolve));
  observations.microtask = {callbackCalls: calls};
  assert.equal(calls, 2);
});
