// Four small behavioral witnesses against the unmodified, pinned upstream module.
// These are independently written probes, not analyzer output or proof of generality.
import assert from 'node:assert/strict';
import {setTimeout as delay} from 'node:timers/promises';
import pDebounce from './upstream/index.js';

const results = [];

{
  const controller = new AbortController();
  const reason = new Error('cancel before start');
  let calls = 0;
  const run = pDebounce(() => { calls++; }, 20, {signal: controller.signal});
  const promise = run();
  const rejected = assert.rejects(promise, error => error === reason);
  controller.abort(reason);
  await rejected;
  await delay(40);
  assert.equal(calls, 0);
  results.push({scenario: 'abort_before_start', passed: true, observed: {calls, rejectedWithOriginalReason: true}});
}

{
  const controller = new AbortController();
  const entered = Promise.withResolvers();
  const release = Promise.withResolvers();
  const trace = [];
  const run = pDebounce(async () => {
    trace.push('started'); entered.resolve();
    await release.promise;
    trace.push('finished'); return 'accepted-result';
  }, 0, {signal: controller.signal});
  const promise = run();
  await entered.promise;
  trace.push('abort'); controller.abort();
  release.resolve();
  const value = await promise;
  assert.equal(value, 'accepted-result');
  assert.deepEqual(trace, ['started', 'abort', 'finished']);
  results.push({scenario: 'abort_after_start', passed: true, observed: {trace, value}});
}

{
  const firstGate = Promise.withResolvers(), lastGate = Promise.withResolvers();
  const calls = [];
  let active = 0, maxActive = 0, queuedSettled = false;
  const save = pDebounce.promise(async value => {
    active++; maxActive = Math.max(maxActive, active); calls.push(value);
    await (value === 'A' ? firstGate.promise : lastGate.promise);
    active--; return value;
  }, {after: true});
  const a = save('A'), b = save('B'), c = save('C');
  b.then(() => { queuedSettled = true; });
  assert.deepEqual(calls, ['A']);
  firstGate.resolve();
  assert.equal(await a, 'A');
  assert.equal(queuedSettled, false, 'first caller settles before later queued work');
  lastGate.resolve();
  const values = await Promise.all([a, b, c]);
  assert.deepEqual(values, ['A', 'C', 'C']);
  assert.deepEqual(calls, ['A', 'C']);
  assert.equal(maxActive, 1);
  results.push({scenario: 'latest_queued_arguments_and_serial_execution', passed: true, observed: {calls, values, maxActive, firstSettledBeforeQueue: true}});
}

{
  let calls = 0, inner;
  const run = pDebounce.promise(value => {
    calls++;
    if (calls === 1) inner = run('inner');
    return value;
  });
  const outer = run('outer');
  assert.equal(inner, outer);
  assert.deepEqual(await Promise.all([outer, inner]), ['outer', 'outer']);
  assert.equal(calls, 1);
  results.push({scenario: 'synchronous_reentry_shares_in_flight_promise', passed: true, observed: {calls, samePromise: true}});
}

console.log(JSON.stringify({upstreamModified: false, scenarios: results, qualification: 'Four bounded behavioral witnesses; not a bug verdict or an agent-benefit experiment.'}, null, 2));
