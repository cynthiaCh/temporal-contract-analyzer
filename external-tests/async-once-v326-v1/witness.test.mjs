// Researcher-authored Node checks of the isolated helper, not the upstream suite.
import test, {after} from 'node:test';
import assert from 'node:assert/strict';
import {pathToFileURL} from 'node:url';
import {writeFileSync} from 'node:fs';
const {default: once} = await import(pathToFileURL(process.env.TCA_MODULE).href);
const observations = {};
after(() => writeFileSync(process.env.TCA_OBSERVATIONS, JSON.stringify(observations, null, 2) + '\n'));

test('sequential calls execute callback once', () => {
  let calls = 0;
  const wrapped = once(() => ++calls);
  wrapped(); wrapped(); wrapped();
  observations.sequential = {callbackCalls: calls};
  assert.equal(calls, 1);
});

test('first-call arguments are forwarded', () => {
  const received = [];
  const wrapped = once((...args) => received.push(args));
  wrapped('a', 42); wrapped('b');
  assert.deepEqual(received, [['a', 42]]);
});

test('receiver is preserved', () => {
  let value;
  const object = {value: 42, run: once(function () { value = this.value; })};
  object.run(); object.run();
  assert.equal(value, 42);
});

test('enumerable callback properties are copied', () => {
  function callback() {}
  callback.marker = 'kept';
  assert.equal(once(callback).marker, 'kept');
});

test('two wrappers have independent state', () => {
  let calls = 0;
  const callback = () => ++calls;
  const a = once(callback), b = once(callback);
  a(); a(); b(); b();
  assert.equal(calls, 2);
});

test('synchronous reentry does not execute callback twice', () => {
  let calls = 0;
  const wrapped = once(() => {
    calls++;
    if (calls === 1) wrapped(); // Bounded to avoid unbounded recursion in a broken variant.
  });
  wrapped();
  observations.synchronous = {callbackCalls: calls};
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
