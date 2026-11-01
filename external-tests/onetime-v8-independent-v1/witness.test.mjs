// Researcher-authored behavioral checks; not upstream AVA tests or maintainer labels.
import test, {after} from 'node:test';
import assert from 'node:assert/strict';
import {writeFileSync} from 'node:fs';
import onetime from './upstream/index.js';

const observations = {};
after(() => writeFileSync(process.env.TCA_OBSERVATIONS, JSON.stringify(observations, null, 2) + '\n'));

test('control: sequential calls execute the callback once', () => {
  let calls = 0;
  const wrapped = onetime(() => ++calls);
  assert.deepEqual([wrapped(), wrapped(), wrapped()], [1, 1, 1]);
  assert.equal(calls, 1);
  observations.sequential = {callbackCalls: calls, wrapperCalls: onetime.callCount(wrapped)};
});

test('control: throw option rejects a later sequential call', () => {
  const wrapped = onetime(() => 42, {throw: true});
  assert.equal(wrapped(), 42);
  assert.throws(() => wrapped(), /can only be called once/);
});

test('control: receiver is preserved', () => {
  const receiver = {value: 42, run: onetime(function () { return this.value; })};
  assert.equal(receiver.run(), 42);
  assert.equal(receiver.run(), 42);
});

test('control: retry after a synchronous exception remains supported', () => {
  let calls = 0;
  const wrapped = onetime(() => {
    calls++;
    if (calls === 1) throw new Error('first call');
    return 'success';
  });
  assert.throws(() => wrapped(), /first call/);
  assert.equal(wrapped(), 'success');
  assert.equal(wrapped(), 'success');
  observations.retry = {callbackCalls: calls, wrapperCalls: onetime.callCount(wrapped)};
  assert.equal(calls, 2);
});

test('control: microtask reentry occurs after state publication', async () => {
  let calls = 0;
  let nested;
  const wrapped = onetime(() => {
    calls++;
    queueMicrotask(() => { nested = wrapped(); });
    return 'outer';
  });
  assert.equal(wrapped(), 'outer');
  await new Promise(resolve => queueMicrotask(resolve));
  observations.microtask = {callbackCalls: calls, nestedResult: nested};
  assert.equal(calls, 1);
  assert.equal(nested, 'outer');
});

test('probe: synchronous reentry should not execute the callback twice', () => {
  let calls = 0;
  let nested;
  const wrapped = onetime(() => {
    calls++;
    if (calls === 1) {
      nested = wrapped();
      return 'outer';
    }
    return 'inner';
  });
  const result = wrapped();
  observations.synchronous = {callbackCalls: calls, wrapperCalls: onetime.callCount(wrapped), result, nested};
  assert.equal(calls, 1);
});

test('probe: throw option should reject synchronous reentry', () => {
  let calls = 0;
  let rejected = false;
  const wrapped = onetime(() => {
    calls++;
    if (calls === 1) {
      try { wrapped(); } catch (error) { rejected = /can only be called once/.test(error.message); }
    }
    return 'done';
  }, {throw: true});
  wrapped();
  observations.synchronousThrow = {callbackCalls: calls, rejected};
  assert.equal(rejected, true);
});
