import test, {after} from 'node:test';
import assert from 'node:assert/strict';
import {writeFileSync} from 'node:fs';
import {createRequire} from 'node:module';
import {pathToFileURL} from 'node:url';

const id = process.env.TCA_CASE;
const path = process.env.TCA_MODULE;
const mod = path.endsWith('.cjs') ? createRequire(import.meta.url)(path) : await import(pathToFileURL(path));
const api = mod.default || mod.createNanoEvents || mod;
const observations = {};
after(() => writeFileSync(process.env.TCA_OBSERVATIONS, JSON.stringify(observations, null, 2) + '\n'));

if (id === 'async-only-once') {
  test('first invocation preserves receiver and arguments; second throws', () => {
    let calls = 0;
    const ctx = {n: 3};
    const fn = api(function(x) { calls++; assert.equal(this, ctx); assert.equal(x, 7); });
    fn.call(ctx, 7);
    assert.throws(() => fn(), /already called/);
    assert.equal(calls, 1);
  });
  test('synchronous reentry is rejected before a second callback', () => {
    let calls = 0, rejected = false;
    const fn = api(() => { if (++calls === 1) { try { fn(); } catch { rejected = true; } } });
    fn();
    observations.reentry = {calls, rejected};
    assert.equal(calls, 1);
    assert.equal(rejected, true);
  });
  test('callback throw consumes the invocation', () => {
    const fn = api(() => { throw new Error('user error'); });
    assert.throws(fn, /user error/);
    assert.throws(fn, /already called/);
  });
}

if (id === 'underscore-negate') {
  test('negates truthiness and preserves receiver/arguments', () => {
    const ctx = {};
    const fn = api(function(a, b) { assert.equal(this, ctx); return a + b; });
    assert.equal(fn.call(ctx, 1, 2), false);
    assert.equal(fn.call(ctx, 1, -1), true);
  });
  test('repetition is intended', () => {
    let calls = 0;
    const fn = api(() => { calls++; return false; });
    assert.equal(fn(), true); assert.equal(fn(), true);
    observations.repeatedCalls = calls;
    assert.equal(calls, 2);
  });
  test('predicate errors propagate', () => {
    const fn = api(() => { throw new Error('predicate'); });
    assert.throws(fn, /predicate/);
  });
}

if (id === 'just-throttle') {
  test('leading call blocks synchronous reentry', () => {
    let calls = 0;
    const fn = api(() => { if (++calls === 1) fn(); return 42; }, 60000);
    try { assert.equal(fn(), 42); observations.reentryCalls = calls; assert.equal(calls, 1); }
    finally { fn.cancel(); }
  });
  test('cancel permits another leading call', () => {
    let calls = 0;
    const fn = api(() => ++calls, 60000);
    try { fn(); fn(); assert.equal(calls, 1); fn.cancel(); fn(); assert.equal(calls, 2); }
    finally { fn.cancel(); }
  });
  test('trailing flush uses latest arguments and receiver', () => {
    const seen = [], ctx = {};
    const fn = api(function(x) { seen.push([this === ctx, x]); }, 60000, {leading: false});
    try { fn.call(ctx, 1); fn.call(ctx, 2); assert.deepEqual(seen, []); fn.flush(); assert.deepEqual(seen, [[true, 2]]); }
    finally { fn.cancel(); }
  });
}

if (id === 'just-memoize-last') {
  test('caches latest evaluation only', () => {
    let calls = 0;
    const fn = api(x => { calls++; return x * 2; });
    assert.deepEqual([fn(1), fn(1), fn(2), fn(1)], [2, 2, 4, 2]);
    assert.equal(calls, 3);
  });
  test('receiver participates in cache identity', () => {
    let calls = 0;
    const fn = api(function(x) { calls++; return this.n + x; });
    assert.equal(fn.call({n: 1}, 2), 3); assert.equal(fn.call({n: 4}, 2), 6);
    assert.equal(calls, 2);
  });
  test('observe same-argument synchronous reentry without imposing a new contract', () => {
    let calls = 0, inner;
    const fn = api(x => { calls++; inner = fn(x); return 42; });
    const outer = fn(1);
    observations.reentry = {calls, inner, outer};
    assert.deepEqual(observations.reentry, {calls: 1, inner: null, outer: 42});
  });
  test('observe cache state after a callback throws', () => {
    let calls = 0;
    const fn = api(x => { calls++; if (x === 2) throw new Error('failure'); return 10; });
    fn(1); assert.throws(() => fn(2), /failure/);
    const retry = fn(2);
    observations.afterThrow = {calls, retry};
    assert.deepEqual(observations.afterThrow, {calls: 2, retry: 10});
  });
}

if (id === 'nanoevents') {
  test('on/emit/unbind passes arguments and stops subsequent delivery', () => {
    const emitter = api(), seen = [];
    const unbind = emitter.on('x', (...args) => seen.push(args));
    emitter.emit('x', 1, 2); unbind(); emitter.emit('x', 3);
    assert.deepEqual(seen, [[1, 2]]);
  });
  test('ordinary subscriptions permit reentrant emission', () => {
    const emitter = api(); let calls = 0;
    emitter.on('x', () => { if (++calls === 1) emitter.emit('x'); });
    emitter.emit('x'); observations.reentryCalls = calls; assert.equal(calls, 2);
  });
  test('documented once recipe unbinds before callback', () => {
    const emitter = api(); let calls = 0;
    const callback = () => { if (++calls === 1) emitter.emit('x'); };
    const unbind = emitter.on('x', (...args) => { unbind(); callback(...args); });
    emitter.emit('x'); emitter.emit('x'); assert.equal(calls, 1);
  });
  test('instances keep independent event tables', () => {
    const a = api(), b = api(); let calls = 0;
    a.on('x', () => calls++); b.emit('x'); assert.equal(calls, 0);
  });
}

if (id === 'tiny-emitter') {
  test('once delivers only once across sequential emissions', () => {
    const emitter = new api(); let calls = 0;
    emitter.once('x', () => calls++); emitter.emit('x'); emitter.emit('x'); assert.equal(calls, 1);
  });
  test('once unsubscribes before synchronous reentry', () => {
    const emitter = new api(); let calls = 0;
    emitter.once('x', () => { if (++calls === 1) emitter.emit('x'); });
    emitter.emit('x'); observations.onceReentryCalls = calls; assert.equal(calls, 1);
  });
  test('ordinary listeners permit repeated emission and off removes them', () => {
    const emitter = new api(); let calls = 0;
    const cb = () => calls++;
    emitter.on('x', cb); emitter.emit('x'); emitter.emit('x'); emitter.off('x', cb); emitter.emit('x');
    assert.equal(calls, 2);
  });
  test('once preserves context and arguments', () => {
    const emitter = new api(), ctx = {};
    let seen;
    emitter.once('x', function(a, b) { seen = [this === ctx, a, b]; }, ctx);
    emitter.emit('x', 1, 2); assert.deepEqual(seen, [true, 1, 2]);
  });
}
