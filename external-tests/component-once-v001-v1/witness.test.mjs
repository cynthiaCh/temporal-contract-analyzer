// Researcher-authored checks; upstream Mocha tests are preserved but not executed.
import test, {after} from 'node:test';
import assert from 'node:assert/strict';
import {createRequire} from 'node:module';
import {writeFileSync} from 'node:fs';
const once = createRequire(import.meta.url)(process.env.TCA_MODULE);
const observations = {};
after(() => writeFileSync(process.env.TCA_OBSERVATIONS, JSON.stringify(observations, null, 2) + '\n'));

test('sequential plain calls invoke once', () => {
  let calls = 0;
  const wrapped = once(() => ++calls);
  assert.equal(wrapped(), 1);
  assert.equal(wrapped(), undefined);
  wrapped();
  observations.sequential = {callbackCalls: calls};
  assert.equal(calls, 1);
});

test('first-call arguments are preserved', () => {
  const received = [];
  const wrapped = once((...args) => received.push(args));
  wrapped('first', 42);
  wrapped('second');
  assert.deepEqual(received, [['first', 42]]);
});

test('method receiver is preserved', () => {
  const receiver = {value: 42, run: once(function () { return this.value; })};
  assert.equal(receiver.run(), 42);
  assert.equal(receiver.run(), undefined);
});

test('one shared wrapper can execute once for each receiver', () => {
  const received = [];
  const run = once(function () { received.push(this.name); });
  const a = {name: 'a', run};
  const b = {name: 'b', run};
  a.run(); a.run(); b.run(); b.run();
  observations.receivers = received;
  assert.deepEqual(received, ['a', 'b']);
});

test('synchronous plain reentry does not execute callback twice', () => {
  let calls = 0;
  const wrapped = once(() => {
    calls++;
    if (calls === 1) wrapped();
    return 'done';
  });
  assert.equal(wrapped(), 'done');
  observations.synchronousPlain = {callbackCalls: calls};
  assert.equal(calls, 1);
});

test('synchronous method reentry does not execute callback twice', () => {
  let calls = 0;
  const receiver = {run: once(function () {
    calls++;
    if (calls === 1) this.run();
  })};
  receiver.run();
  observations.synchronousMethod = {callbackCalls: calls};
  assert.equal(calls, 1);
});

test('microtask reentry does not execute callback twice', async () => {
  let calls = 0;
  const wrapped = once(() => {
    calls++;
    if (calls === 1) queueMicrotask(() => wrapped());
  });
  wrapped();
  await new Promise(resolve => queueMicrotask(resolve));
  observations.microtask = {callbackCalls: calls};
  assert.equal(calls, 1);
});
