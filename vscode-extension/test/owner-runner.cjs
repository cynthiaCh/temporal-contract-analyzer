'use strict';
const assert = require('node:assert/strict');
const fs = require('node:fs/promises');
const os = require('node:os');
const path = require('node:path');
const {invoke} = require('../src/runner');
(async () => {
  const store = await fs.mkdtemp(path.join(os.tmpdir(), 'tempo-owner-'));
  const extension = path.resolve(__dirname, '..');
  const call = (operation, extra = {}) => invoke(extension, {operation, store, ...extra});
  try {
    assert.deepEqual((await call('experience_init')).entries, []);
    const record = {title: 'Keep entry', labels: ['I'], requires: ['entry_snapshot'], excludes: [], abstract: 'Capture original identity.'};
    for (const key of ['applicability', 'event_relation', 'preservation', 'exclusion', 'verification']) record[key] = 'Keep original identity.';
    const saved = await call('experience_change', {change: {action: 'save', id: 'owner-entry', revision: null, record}});
    assert.equal(saved.entries[0].record.summary.review.decision, 'accept');
    assert.equal((await call('experience_list')).entries.length, 1);
    await assert.rejects(call('experience_change', {change: {action: 'delete', id: 'owner-entry', revision: 'stale'}}), /changed outside/);
    await call('experience_change', {change: {action: 'delete', id: 'owner-entry', revision: saved.entries[0].revision}});
    assert.equal((await call('experience_history')).history.length, 1);
    assert.equal((await call('experience_list')).entries.length, 0);
    console.log('PASS: packaged Python bridge initializes, saves, lists, rejects conflicts, deletes and reads history');
  } finally { await fs.rm(store, {recursive: true, force: true}); }
})().catch(e => { console.error(e); process.exitCode = 1; });
