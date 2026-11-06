const assert = require('node:assert/strict');
const Module = require('node:module');
const original = Module._load;
let slots = [], cursor = 0, cleanup;
const fakeReact = {
  useRef(value) { return slots[cursor++] ||= { current: value }; },
  useReducer() { cursor++; return [0, () => {}]; },
  useEffect(effect) { cursor++; if (!cleanup) cleanup = effect(); },
};
Module._load = function(name, parent, main) { return name === 'react' ? fakeReact : original.call(this, name, parent, main); };
const { usePreparation } = require('../src/usePreparation.js');
const checks = [], retries = new Map(), cancelled = [];
let next = 1;
globalThis.__preparationTransport = token => new Promise(resolve => checks.push({token, resolve}));
globalThis.__schedulePreparationRetry = callback => { const id = next++; retries.set(id, callback); return id; };
globalThis.__cancelPreparationRetry = id => { cancelled.push(id); retries.delete(id); };
function hook(token) { cursor = 0; return usePreparation(token); }
async function tick() { await Promise.resolve(); await Promise.resolve(); }
(async () => {
  let api = hook('A');
  api.start();
  assert.equal(checks.length, 1);
  checks[0].resolve(false); await tick();
  assert.deepEqual(api.snapshot().completed, []);
  assert.equal(api.snapshot().retryScheduled, true);
  const retry = retries.get(1); retries.delete(1); retry();
  assert.equal(checks.length, 2);
  checks[1].resolve(true); await tick();
  assert.deepEqual(api.snapshot().completed, ['A']);
  assert.equal(api.snapshot().retryScheduled, false);
  api.reopen('B');
  checks[2].resolve(false); await tick();
  api.close();
  assert.ok(cancelled.includes(2));
  api.reopen('B');
  checks[3].resolve(true); await tick();
  assert.deepEqual(api.snapshot().completed, ['A', 'B']);
  api.start();
  api.close();
  checks[4].resolve(true); await tick();
  assert.deepEqual(api.snapshot().completed, ['A', 'B']);
  cleanup();
  console.log('PASS pending retry, ready completion, close/reopen cancellation, stale result');
})().catch(error => { console.error(error); process.exitCode = 1; });
