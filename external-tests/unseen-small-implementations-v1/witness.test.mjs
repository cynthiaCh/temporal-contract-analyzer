import test, {after} from 'node:test';
import assert from 'node:assert/strict';
import {writeFileSync} from 'node:fs';
import {pathToFileURL} from 'node:url';

const loaded = await import(pathToFileURL(process.env.TCA_MODULE));
const api = loaded.default;
const witness = process.env.TCA_WITNESS;
const observations = {};
after(() => writeFileSync(process.env.TCA_OBSERVATIONS, JSON.stringify(observations, null, 2) + '\n'));

if (witness === 'event-once') {
  test('sequential once calls only once', () => {
    const emitter = new api(); let calls = 0;
    emitter.once('x', () => calls++); emitter.emit('x'); emitter.emit('x');
    assert.equal(calls, 1);
  });
  test('once survives nested emission with one listener', () => {
    const emitter = new api(); let calls = 0;
    emitter.once('x', () => { if (++calls === 1) emitter.emit('x'); });
    emitter.emit('x'); observations.singleReentryCalls = calls;
    assert.equal(calls, 1);
  });
  test('once survives nested emission with multiple listeners', () => {
    const emitter = new api(); let onceCalls = 0, ordinaryCalls = 0;
    emitter.once('x', () => { if (++onceCalls === 1) emitter.emit('x'); });
    emitter.on('x', () => ordinaryCalls++);
    emitter.emit('x'); observations.multiReentry = {onceCalls, ordinaryCalls};
    assert.equal(onceCalls, 1); assert.equal(ordinaryCalls, 2);
  });
  test('ordinary listener preserves arguments and context', () => {
    const emitter = new api(), ctx = {}; let seen;
    emitter.on('x', function(a, b) { seen = [this === ctx, a, b]; }, ctx);
    emitter.emit('x', 1, 2); assert.deepEqual(seen, [true, 1, 2]);
  });
}

if (witness === 'mitt-removal') {
  test('on emit off preserves arguments', () => {
    const emitter = api(), seen = [], handler = x => seen.push(x);
    emitter.on('x', handler); emitter.emit('x', 7); emitter.off('x', handler); emitter.emit('x', 8);
    assert.deepEqual(seen, [7]);
  });
  test('self removal does not skip the following listener', () => {
    const emitter = api(), seen = [];
    const first = () => { seen.push('first'); emitter.off('x', first); };
    emitter.on('x', first); emitter.on('x', () => seen.push('second'));
    emitter.emit('x'); observations.selfRemoval = [...seen];
    assert.deepEqual(seen, ['first', 'second']);
  });
  test('wildcard self removal does not skip the following listener', () => {
    const emitter = api(), seen = [];
    const first = () => { seen.push('first'); emitter.off('*', first); };
    emitter.on('*', first); emitter.on('*', () => seen.push('second'));
    emitter.emit('x'); observations.wildcardRemoval = [...seen];
    assert.deepEqual(seen, ['first', 'second']);
  });
  test('ordinary subscriptions intentionally permit reentrant delivery', () => {
    const emitter = api(); let calls = 0;
    emitter.on('x', () => { if (++calls === 1) emitter.emit('x'); });
    emitter.emit('x'); assert.equal(calls, 2);
  });
}

if (witness === 'memo-exception-cache') {
  test('normal latest result caching works', () => {
    let calls = 0;
    const memo = api(x => { calls++; return x * 2; });
    assert.deepEqual([memo(1), memo(1), memo(2)], [2, 2, 4]); assert.equal(calls, 2);
  });
  test('same failing arguments rethrow the cached exception', () => {
    let calls = 0;
    const error = new Error('failure'), memo = api(() => { calls++; throw error; });
    let first, second;
    try { memo(1); } catch (e) { first = e; }
    try { memo(1); } catch (e) { second = e; }
    observations.repeatFailure = {calls, firstThrew: first === error, secondThrew: second === error};
    assert.equal(first, error); assert.equal(second, error); assert.equal(calls, 1);
  });
  test('failed arguments never return an earlier successful value', () => {
    const error = new Error('failure');
    const memo = api(x => { if (x === 2) throw error; return 10; });
    assert.equal(memo(1), 10); assert.throws(() => memo(2), e => e === error);
    let retryValue, retryThrew = false;
    try { retryValue = memo(2); } catch (e) { retryThrew = e === error; }
    observations.afterSuccessThenFailure = {retryThrew, retryValue};
    assert.equal(retryThrew, true);
  });
}

if (witness === 'promise-cache') {
  test('consecutive non awaited calls share the in flight evaluation', async () => {
    let calls = 0;
    const memo = api(async () => ++calls);
    const results = await Promise.all([memo(1), memo(1)]);
    observations.concurrent = {calls, results};
    assert.deepEqual(results, [1, 1]); assert.equal(calls, 1);
  });
  test('settled success is cached', async () => {
    let calls = 0;
    const memo = api(async () => ++calls);
    assert.equal(await memo(1), 1); assert.equal(await memo(1), 1); assert.equal(calls, 1);
  });
  test('rejected Error is not cached by default', async () => {
    let calls = 0;
    const memo = api(async () => { calls++; throw new Error('failure'); });
    await assert.rejects(memo(1), /failure/); await assert.rejects(memo(1), /failure/);
    assert.equal(calls, 2);
  });
}

if (witness === 'inflight') {
  test('same key queues callbacks behind one completion function', () => {
    const seen = [], finish = api('normal', (...args) => seen.push(args));
    assert.equal(api('normal', (...args) => seen.push(args)), null);
    finish(null, 7); assert.deepEqual(seen, [[null, 7], [null, 7]]);
  });
  test('completed key can start a fresh request', () => {
    const finish = api('repeat', () => {}); finish();
    const next = api('repeat', () => {}); assert.equal(typeof next, 'function'); next();
  });
  test('callback throw still releases the request key', () => {
    const error = new Error('failure');
    const finish = api('throwing', () => { throw error; });
    assert.throws(finish, e => e === error);
    const next = api('throwing', () => {});
    observations.afterThrowCanStart = typeof next === 'function';
    assert.equal(typeof next, 'function'); next();
  });
  test('registration inside a callback is delivered on a later tick', async () => {
    const seen = [], finish = api('reentry', () => {
      seen.push('outer'); assert.equal(api('reentry', () => seen.push('nested')), null);
    });
    finish(); assert.deepEqual(seen, ['outer']);
    await new Promise(resolve => process.nextTick(resolve));
    assert.deepEqual(seen, ['outer', 'nested']);
  });
}

if (witness === 'strict-once') {
  test('ordinary once returns the first result', () => {
    let calls = 0; const fn = api(() => ++calls);
    assert.deepEqual([fn(), fn()], [1, 1]); assert.equal(calls, 1);
  });
  test('ordinary once prevents a second callback during reentry', () => {
    let calls = 0; const fn = api(() => { if (++calls === 1) fn(); });
    fn(); assert.equal(calls, 1);
  });
  test('strict once rejects a sequential second call', () => {
    const fn = api.strict(() => 42); assert.equal(fn(), 42); assert.throws(fn);
  });
  test('strict once rejects a reentrant second call', () => {
    let calls = 0, rejected = false;
    const fn = api.strict(() => { if (++calls === 1) { try { fn(); } catch { rejected = true; } } });
    fn(); observations.strictReentry = {calls, rejected};
    assert.equal(calls, 1); assert.equal(rejected, true);
  });
}

if (witness === 'memo-retry') {
  test('repeated arguments return a cached result', () => {
    let calls = 0; const memo = api(x => { calls++; return x * 2; });
    assert.deepEqual([memo(1), memo(1), memo(2)], [2, 2, 4]); assert.equal(calls, 2);
  });
  test('throwing evaluation is retried on identical arguments', () => {
    let calls = 0; const memo = api(() => { calls++; throw new Error('failure'); });
    assert.throws(() => memo(1), /failure/); assert.throws(() => memo(1), /failure/);
    observations.retryCalls = calls; assert.equal(calls, 2);
  });
  test('failed arguments do not replace a previous successful cache entry', () => {
    let calls = 0; const memo = api(x => { calls++; if (x === 2) throw new Error('failure'); return {x}; });
    const first = memo(1); assert.throws(() => memo(2), /failure/);
    assert.equal(memo(1), first); assert.equal(calls, 2);
  });
}
