import {pathToFileURL} from 'node:url';

let input = '';
for await (const chunk of process.stdin) input += chunk;
const request = JSON.parse(input);
const trace = [], operations = [], counts = {};
const pending = [];
let budgetExceeded = false;
function encode(value) {
  if (value === undefined) return {kind: 'undefined'};
  if (typeof value === 'function') return {kind: 'function'};
  if (typeof value === 'number' && !Number.isFinite(value)) return {kind: 'number', value: String(value)};
  return {kind: 'value', value};
}
function note(event, detail = {}) {
  if (trace.length >= 256) { budgetExceeded = true; throw new Error('probe trace budget'); }
  trace.push({step: trace.length + 1, event, ...detail});
}
function enter(id, value) {
  counts[id] = (counts[id] || 0) + 1;
  const site = new Error().stack.split('\n').find(line => line.includes(request.source_root + '/'));
  note('callback', {id, count: counts[id], argument: encode(value),
    source: site?.replaceAll(request.source_root, '<subject>').trim() || null});
  return counts[id];
}
function invoke(label, fn, args = []) {
  const operation = {label, arguments: args.map(encode), status: 'pending'};
  operations.push(operation);
  note('invoke', {label});
  const success = value => { operation.status = 'returned'; operation.result = encode(value); note('return', {label}); return value; };
  const failure = error => { operation.status = 'threw'; operation.error = {name: error?.name || typeof error, message: error?.message || String(error)}; note('throw', {label}); };
  try {
    const value = fn();
    if (value && typeof value.then === 'function') {
      const task = Promise.resolve(value).then(success, failure);
      pending.push(task); return task;
    }
    return success(value);
  } catch (error) { return failure(error); }
}
try {
  const module = await import(pathToFileURL(request.module));
  let factory = module;
  for (const part of (request.api.export || 'default').split('.')) factory = factory?.[part];
  if (typeof factory !== 'function') throw new Error('The configured export must be a function');
  const scene = request.scenario;
  if (request.api.kind === 'wrapper') {
    let fired = false, wrapped;
    const release = [];
    const callback = value => {
      const call = enter('callback', value);
      if (scene.kind === 'reentry' && !fired) {
        fired = true; invoke('nested', () => wrapped(value), [value]);
      }
      if (scene.kind.startsWith('failure-') && value === 1) throw new Error('probe callback failure');
      const result = {call, value};
      return scene.kind === 'overlap' ? new Promise(resolve => release.push(() => resolve(result))) : result;
    };
    wrapped = factory(callback);
    if (typeof wrapped !== 'function') throw new Error('The configured factory must return a callable');
    if (scene.kind === 'overlap') {
      const first = invoke('call-0', () => wrapped(0), [0]);
      const second = invoke('call-1', () => wrapped(0), [0]);
      release.forEach(resolve => resolve());
      await Promise.all([first, second]);
    } else {
      const values = scene.kind === 'failure-retry' ? [0, 1, 1] : scene.kind === 'failure-first' ? [1, 1] :
        scene.kind === 'failure-restore' ? [0, 1, 0] : scene.kind === 'reentry' ? [0] : [0, 0];
      for (let i = 0; i < values.length; i++) await invoke('call-'+i, () => wrapped(values[i]), [values[i]]);
    }
  } else if (request.api.kind === 'emitter') {
    const emitter = request.api.construct ? new factory() : factory();
    const methods = request.api.methods;
    if (!['on', 'off', 'emit'].every(key => typeof emitter[methods[key]] === 'function')) throw new Error('Missing emitter method');
    const callbacks = []; let fired = false;
    const emit = label => invoke(label, () => emitter[methods.emit]('probe'), ['probe']);
    for (let i = 0; i < scene.listeners; i++) callbacks.push(value => {
      enter(String(i), value);
      if (i === 0 && !fired && ['emit-reentry', 'emit-mutation'].includes(scene.kind)) {
        fired = true;
        if (scene.kind === 'emit-reentry') emit('nested');
        else invoke('remove', () => emitter[methods.off]('probe', callbacks[scene.remove === 'self' ? 0 : 1]));
      }
    });
    for (const callback of callbacks) emitter[methods[scene.registration]]('probe', callback);
    await emit('emit-0');
    if (['emit-repeat', 'once-repeat'].includes(scene.kind)) await emit('emit-1');
  } else if (request.api.kind === 'keyed_completion') {
    let fired = false;
    const callback = id => value => {
      enter(id, value);
      if (scene.kind === 'keyed-failure') throw new Error('probe callback failure');
      if (scene.kind === 'keyed-reentry' && !fired) {
        fired = true; invoke('register-nested', () => factory('probe', callback('nested')));
      }
    };
    const complete = invoke('register-first', () => factory('probe', callback('first')));
    if (typeof complete !== 'function') throw new Error('First registration must return completion function');
    if (scene.kind === 'keyed-repeat') invoke('register-second', () => factory('probe', callback('second')));
    await invoke('complete', () => complete(null, 7));
    await new Promise(resolve => setImmediate(resolve));
    if (scene.kind !== 'keyed-reentry') {
      const next = invoke('register-after', () => factory('probe', () => enter('after', null)));
      if (typeof next === 'function') await invoke('complete-after', () => next());
    }
  } else throw new Error('Unsupported API kind');
  await Promise.all(pending);
  process.stdout.write(JSON.stringify({status: budgetExceeded ? 'inconclusive' : 'observed',
    reason: budgetExceeded ? 'trace_budget' : undefined,
    observation: {calls: Object.values(counts).reduce((a, b) => a + b, 0), counts, operations}, trace}));
} catch (error) {
  process.stdout.write(JSON.stringify({status: 'inconclusive', reason: budgetExceeded ? 'trace_budget' : 'load_or_setup_error',
    error: String(error), trace}));
}
