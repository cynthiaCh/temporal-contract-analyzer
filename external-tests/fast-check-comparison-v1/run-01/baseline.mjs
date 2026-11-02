import assert from 'node:assert/strict';
import {createRequire} from 'node:module';
import {realpathSync} from 'node:fs';
import path from 'node:path';
import {pathToFileURL} from 'node:url';

let input = '';
for await (const chunk of process.stdin) input += chunk;
const request = JSON.parse(input);
const require = createRequire(path.join(request.runtime_root, 'entry.cjs'));
const fc = require('fast-check');
const root = realpathSync(request.source_root);
let instance = 0;

async function load() {
  let module;
  if (request.module_kind === 'commonjs') {
    for (const file of Object.keys(require.cache)) if (file.startsWith(root + '/')) delete require.cache[file];
    module = {default: require(request.module)};
  } else module = await import(pathToFileURL(request.module).href + '?instance=' + instance++);
  let api = module;
  for (const part of (request.api.export || 'default').split('.')) api = api?.[part];
  if (typeof api !== 'function') throw new Error('Invalid export binding');
  return api;
}

async function execute(contract, data) {
  const factory = await load();
  const counts = {}, frames = [], outcomes = [];
  const count = (id = 'callback') => {
    counts[id] = (counts[id] || 0) + 1;
    const frame = new Error().stack.split('\n').find(line => line.includes(root + '/'));
    frames.push({id, count: counts[id], source: frame?.replaceAll(root, '<subject>').trim() || null});
    return counts[id];
  };
  const attempt = async fn => {
    try { const value = await fn(); const result = {status: 'returned', value}; outcomes.push(result); return result; }
    catch (error) { const result = {status: 'threw', name: error?.name, message: error?.message}; outcomes.push(result); return result; }
  };
  const check = (value, message) => assert.ok(value, message);
  try {
    if (contract === 'once_delivery' || contract === 'snapshot_delivery') {
      const emitter = request.api.construct ? new factory() : factory();
      const methods = request.api.methods;
      const listeners = []; let fired = false;
      for (let i = 0; i < data.listeners; i++) listeners.push(() => {
        count(String(i));
        if (i !== 0 || fired) return;
        fired = true;
        if (contract === 'once_delivery' && data.reenter) emitter[methods.emit]('probe');
        if (contract === 'snapshot_delivery') emitter[methods.off]('probe', listeners[data.target % data.listeners]);
      });
      for (const listener of listeners) emitter[methods[contract === 'once_delivery' ? 'once' : 'on']]('probe', listener);
      const times = contract === 'once_delivery' ? data.emissions : 1;
      for (let i = 0; i < times; i++) emitter[methods.emit]('probe');
      assert.deepEqual(Array.from({length: data.listeners}, (_, i) => counts[String(i)] || 0),
        Array(data.listeners).fill(1), contract);
    } else if (contract === 'cache_repeated') {
      const wrapped = factory(value => ({call: count(), value}));
      const values = [];
      for (let i = 0; i < data; i++) values.push(await wrapped(0));
      assert.equal(counts.callback, 1, contract);
      for (const value of values) assert.deepEqual(value, values[0], contract);
    } else if (contract === 'failure_rethrows') {
      const wrapped = factory(value => {
        count(); if (value === 1) throw new Error('probe callback failure'); return {value};
      });
      if (data.warmup) await wrapped(0);
      for (let i = 0; i < data.retries; i++) {
        const outcome = await attempt(() => wrapped(1));
        assert.equal(outcome.status, 'threw', contract);
      }
    } else if (contract === 'preserve_success_after_failure') {
      const wrapped = factory(value => {
        const call = count(); if (value === 1) throw new Error('probe callback failure'); return {call, value};
      });
      const first = await wrapped(0);
      for (let i = 0; i < data; i++) {
        const result = await attempt(() => wrapped(1)); check(result.status === 'threw', contract);
      }
      assert.deepEqual(await wrapped(0), first, contract);
      assert.equal(counts.callback, 1 + data, contract);
    } else if (contract === 'coalesce_pending') {
      const releases = [];
      const wrapped = factory(value => {
        const call = count(); return new Promise(resolve => releases.push(() => resolve({call, value})));
      });
      const pending = Array.from({length: data}, () => wrapped(0));
      releases.forEach(release => release());
      const values = await Promise.all(pending);
      assert.equal(counts.callback, 1, contract);
      for (const value of values) assert.deepEqual(value, values[0], contract);
    } else if (contract === 'at_most_once' || contract === 'repeat_rejected') {
      let wrapped, fired = false;
      const pending = [], releases = [];
      const callback = value => {
        const call = count();
        if (data.mode === 'reenter' && !fired) {
          fired = true; pending.push(attempt(() => wrapped(value)));
        }
        if (data.mode === 'failure') throw new Error('probe callback failure');
        return data.mode === 'overlap' ? new Promise(resolve => releases.push(() => resolve({call, value}))) : {call, value};
      };
      wrapped = factory(callback);
      if (data.mode === 'overlap') {
        for (let i = 0; i < data.times; i++) pending.push(attempt(() => wrapped(0)));
        releases.forEach(release => release()); await Promise.all(pending);
      } else {
        await attempt(() => wrapped(0));
        if (data.mode !== 'reenter') for (let i = 1; i < data.times; i++) await attempt(() => wrapped(0));
        await Promise.all(pending);
      }
      if (contract === 'at_most_once') check((counts.callback || 0) <= 1, contract);
      else {
        const second = data.mode === 'reenter' ? (await Promise.all(pending))[0] : outcomes[1];
        check(second?.status === 'threw', contract);
      }
    } else if (contract === 'restart_after_failure') {
      const finish = factory('probe', () => { count(); throw new Error('probe callback failure'); });
      await attempt(() => finish());
      await new Promise(resolve => setImmediate(resolve));
      const next = factory('probe', () => count('next'));
      assert.equal(typeof next, 'function', contract);
      next();
    } else if (contract === 'queued_delivery') {
      let fired = false;
      const callback = id => () => {
        count(id);
        if (data.reenter && !fired) { fired = true; factory('probe', callback('nested')); }
      };
      const finish = factory('probe', callback('0'));
      for (let i = 1; i < data.queued; i++) factory('probe', callback(String(i)));
      finish(); await new Promise(resolve => setImmediate(resolve));
      for (let i = 0; i < data.queued; i++) assert.equal(counts[String(i)], 1, contract);
      assert.equal(counts.nested || 0, data.reenter ? 1 : 0, contract);
    } else throw new Error('Unknown property: ' + contract);
    return {passed: true, counts, frames, outcomes};
  } catch (error) {
    error.evidence = {counts, frames, outcomes};
    throw error;
  }
}

function arbitrary(contract) {
  switch (contract) {
    case 'once_delivery': return fc.record({listeners: fc.integer({min: 1, max: 4}), reenter: fc.boolean(), emissions: fc.integer({min: 1, max: 3})});
    case 'snapshot_delivery': return fc.record({listeners: fc.integer({min: 2, max: 4}), target: fc.integer({min: 0, max: 3})});
    case 'failure_rethrows': return fc.record({warmup: fc.boolean(), retries: fc.integer({min: 2, max: 4})});
    case 'at_most_once': return fc.record({mode: fc.constantFrom('repeat', 'reenter', 'failure', 'overlap'), times: fc.integer({min: 2, max: 4})});
    case 'repeat_rejected': return fc.record({mode: fc.constantFrom('repeat', 'reenter'), times: fc.constant(2)});
    case 'queued_delivery': return fc.record({queued: fc.integer({min: 1, max: 4}), reenter: fc.boolean()});
    case 'restart_after_failure': return fc.constant(null);
    case 'preserve_success_after_failure': return fc.integer({min: 1, max: 3});
    default: return fc.integer({min: 2, max: 4});
  }
}

try {
  const rows = [];
  for (const contract of Object.keys(request.contracts).filter(key => request.contracts[key])) {
    const property = fc.asyncProperty(arbitrary(contract), async data => { await execute(contract, data); });
    const details = await fc.check(property, {seed: request.seed, numRuns: 100});
    const error = details.errorInstance;
    const row = {contract, failed: details.failed, interrupted: details.interrupted,
      numRuns: details.numRuns, numShrinks: details.numShrinks, seed: details.seed,
      path: details.counterexamplePath, counterexample: details.counterexample,
      classification: !details.failed ? 'no_counterexample' : error?.name === 'AssertionError' ? 'contract_counterexample' : 'inconclusive_error',
      error: error ? {name: error.name, message: error.message, stack: error.stack} : null,
      evidence: error?.evidence || null};
    if (details.failed) {
      const replay = await fc.check(property, {seed: details.seed, path: details.counterexamplePath, numRuns: 100, endOnFailure: true});
      row.replay_matches = replay.failed && JSON.stringify(replay.counterexample) === JSON.stringify(details.counterexample);
      try { await fc.assert(property, {seed: details.seed, path: details.counterexamplePath, numRuns: 100, endOnFailure: true}); }
      catch (native) { row.native_failure_output = native.stack; }
    }
    if (request.paired_replay?.[contract]) {
      row.paired_replay = [];
      for (const data of request.paired_replay[contract]) {
        try { row.paired_replay.push({data, result: await execute(contract, data)}); }
        catch (error) { row.paired_replay.push({data, result: {passed: false, error: error.message, ...error.evidence}}); }
      }
    }
    rows.push(row);
  }
  process.stdout.write(JSON.stringify({fast_check_version: fc.__version, seed: request.seed, rows}));
} catch (error) {
  process.stdout.write(JSON.stringify({status: 'infrastructure_error', name: error.name, error: error.stack}));
  process.exitCode = 2;
}
