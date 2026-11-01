// Isolated child process: the polyfill modifies Function.prototype here only.
import test, {after} from 'node:test';
import assert from 'node:assert/strict';
import {pathToFileURL} from 'node:url';
import {writeFileSync} from 'node:fs';
delete Function.prototype.once;
await import(pathToFileURL(process.env.TCA_MODULE).href);
const observations = {};
after(() => {
  writeFileSync(process.env.TCA_OBSERVATIONS, JSON.stringify(observations, null, 2) + '\n');
  delete Function.prototype.once;
});

test('sequential calls execute once and cache result', () => {
  let calls = 0;
  const run = (() => ++calls).once();
  assert.equal(run(), 1); assert.equal(run(), 1); assert.equal(run(), 1);
  observations.sequential = {callbackCalls: calls};
  assert.equal(calls, 1);
});

test('arguments are forwarded only on the first call', () => {
  const received = [];
  const run = ((...args) => received.push(args)).once();
  run('first', 42); run('second');
  assert.deepEqual(received, [['first', 42]]);
});

test('receiver is preserved', () => {
  const run = (function () { return this.value; }).once();
  assert.equal(run.call({value: 42}), 42);
  assert.equal(run.call({value: 99}), 42);
});

test('wrappers maintain independent state', () => {
  let calls = 0;
  const callback = () => ++calls;
  const a = callback.once(), b = callback.once();
  a(); a(); b(); b();
  assert.equal(calls, 2);
});

test('constructor returns the same created instance', () => {
  let calls = 0;
  class Item { constructor(value) { calls++; this.value = value; } }
  const Create = Item.once();
  const a = new Create(42), b = new Create(99);
  assert.equal(a, b); assert.equal(a.value, 42); assert.equal(calls, 1);
});

test('synchronous reentry does not invoke callback twice', () => {
  let calls = 0;
  const run = (() => {
    calls++;
    if (calls === 1) run();
    return 'done';
  }).once();
  run();
  observations.synchronous = {callbackCalls: calls};
  assert.equal(calls, 1);
});

test('microtask reentry does not invoke callback twice', async () => {
  let calls = 0;
  const run = (() => {
    calls++;
    if (calls === 1) queueMicrotask(() => run());
  }).once();
  run();
  await new Promise(resolve => queueMicrotask(resolve));
  observations.microtask = {callbackCalls: calls};
  assert.equal(calls, 1);
});
