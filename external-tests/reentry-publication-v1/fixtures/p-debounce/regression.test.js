import {test} from 'node:test';
import {strict as assert} from 'node:assert';
import {setTimeout as delay} from 'node:timers/promises';
import pDebounce from './index.js';


test('.promise() does not start a concurrent execution when the function synchronously calls the debounced function', async () => {
	let running = 0;
	let maxRunning = 0;
	const calls = [];
	let innerPromise;
	const debounced = pDebounce.promise(async value => {
		running++;
		maxRunning = Math.max(maxRunning, running);
		calls.push(value);
		if (value === 'outer') {
			// For example, an event handler that fires synchronously
			innerPromise = debounced('inner');
		}

		await delay(20);
		running--;
		return value;
	});

	assert.equal(await debounced('outer'), 'outer');
	assert.equal(await innerPromise, 'outer');
	assert.equal(maxRunning, 1);
	assert.deepEqual(calls, ['outer']);

	// The busy state is still correct afterwards
	const results = await Promise.all([debounced('next'), debounced('ignored')]);
	assert.deepEqual(results, ['next', 'next']);
	assert.deepEqual(calls, ['outer', 'next']);
});

test('.promise() with after option queues a call that the function makes synchronously', async () => {
	let running = 0;
	let maxRunning = 0;
	const calls = [];
	let innerPromise;
	const debounced = pDebounce.promise(async value => {
		running++;
		maxRunning = Math.max(maxRunning, running);
		calls.push(value);
		if (value === 'outer') {
			innerPromise = debounced('inner');
		}

		await delay(20);
		running--;
		return value;
	}, {after: true});

	assert.equal(await debounced('outer'), 'outer');
	assert.equal(await innerPromise, 'inner');
	assert.equal(maxRunning, 1);
	assert.deepEqual(calls, ['outer', 'inner']);
});

test('.promise() does not start a concurrent execution when a synchronously throwing function calls the debounced function', async () => {
	const error = new Error('fail');
	let innerPromise;
	const calls = [];
	const debounced = pDebounce.promise(value => {
		calls.push(value);
		if (value === 'outer') {
			innerPromise = debounced('inner');
			throw error;
		}

		return value;
	});

	await assert.rejects(debounced('outer'), error);
	await assert.rejects(innerPromise, error);
	assert.deepEqual(calls, ['outer']);
	assert.equal(await debounced('next'), 'next');
});
