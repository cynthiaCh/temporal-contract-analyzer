'use strict';
const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs/promises');
const os = require('node:os');
const path = require('node:path');
const {analyze, execute, findPython, Cancelled} = require('../src/runner');
const extension = path.resolve(__dirname, '..');
const source = '<template><div>😀</div></template><script setup>async function load() { await fetch(); store.save(); }</script>';

test('bundled Vue parser produces exact UTF-16 ranges and review hints', async () => {
  const result = await analyze(extension, {mode: 'file', path: 'Demo.vue', text: source});
  assert.equal(result.report.status, 'parsed');
  assert(result.report.findings.some(f => f.rule === 'effect-after-await'));
  const event = result.report.files[0].events.find(e => e.callee === 'store.save');
  const [line, column, endLine, endColumn] = result.ranges[event.id];
  assert.equal(line, 0);
  assert.equal(endLine, 0);
  assert.equal(source.slice(column, endColumn), 'store.save()');
  assert.match(result.markdown, /inline script/);
});

test('Python UTF-8 byte offsets become editor UTF-16 columns', async () => {
  const text = 'async def work():\n    marker = "😀"; await fetch()\n    store.save()\n';
  const result = await analyze(extension, {mode: 'file', path: 'worker.py', text});
  const event = result.report.files[0].events.find(e => e.kind === 'await');
  const [line, column, , endColumn] = result.ranges[event.id];
  assert.equal(text.split('\n')[line].slice(column, endColumn), 'await fetch()');
});

test('directory overlays include unsaved content without writing input or following excluded overlays', async t => {
  const root = await fs.mkdtemp(path.join(os.tmpdir(), 'tca folder with spaces-'));
  t.after(() => fs.rm(root, {recursive: true, force: true}));
  const original = '<script setup>const value = 1;</script>';
  await fs.writeFile(path.join(root, 'Demo.vue'), original);
  await fs.mkdir(path.join(root, 'node_modules'));
  await fs.writeFile(path.join(root, 'node_modules/dependency.js'), 'secret();');
  const result = await analyze(extension, {mode: 'folder', root, overlays: {
    'Demo.vue': source, 'node_modules/dependency.js': 'other();', '../escape.js': 'escape();',
  }});
  assert(result.report.findings.some(f => f.rule === 'effect-after-await'));
  assert.deepEqual(result.report.files.map(f => f.path), ['Demo.vue']);
  assert.equal(await fs.readFile(path.join(root, 'Demo.vue'), 'utf8'), original);
});

test('broken Vue has partial status and an actionable error', async () => {
  const result = await analyze(extension, {mode: 'file', path: 'Broken.vue', text: '<script src="./external.js"></script>'});
  assert.equal(result.report.status, 'partial');
  assert.match(result.report.files[0].error.message, /External/);
  assert.deepEqual(result.report.findings, []);
});

test('rejects excluded or escaping inputs and oversized editor buffers', async () => {
  for (const name of ['../outside.vue', 'oracle/secret.vue', '/absolute.vue']) {
    await assert.rejects(analyze(extension, {mode: 'file', path: name, text: source}), /source path/);
  }
  await assert.rejects(analyze(extension, {mode: 'file', path: 'Huge.vue', text: 'x'.repeat(1024 * 1024 + 1)}), /1 MiB/);
});

test('requires a usable Python instead of silently reporting zero hints', async () => {
  await assert.rejects(findPython(path.join(extension, 'missing-python')), /Python 3.9/);
});

test('cancellation and timeout terminate analysis processes', async () => {
  const controller = new AbortController();
  const running = execute(process.execPath, ['-e', 'setInterval(() => {}, 1000)'], {signal: controller.signal});
  setTimeout(() => controller.abort(), 100);
  await assert.rejects(running, Cancelled);
  await assert.rejects(execute(process.execPath, ['-e', 'setInterval(() => {}, 1000)'], {timeout: 100}), /超时/);
  await assert.rejects(execute(process.execPath, ['-e', 'process.exit(0)'], {signal: controller.signal}), Cancelled);
});

test('candidate code and imports are never executed', async t => {
  const root = await fs.mkdtemp(path.join(os.tmpdir(), 'tca-no-eval-'));
  t.after(() => fs.rm(root, {recursive: true, force: true}));
  const sentinel = path.join(root, 'executed');
  const text = '<script setup>import "./missing.js"; require("fs").writeFileSync(' + JSON.stringify(sentinel) + ', "bad"); throw Error("do not execute");</script>';
  const result = await analyze(extension, {mode: 'file', path: 'Demo.vue', text});
  assert.equal(result.report.status, 'parsed');
  await assert.rejects(fs.access(sentinel));
});
