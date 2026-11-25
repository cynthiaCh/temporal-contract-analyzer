'use strict';
const assert = require('node:assert/strict');
const fs = require('node:fs/promises');
const path = require('node:path');
const {chromium} = require('playwright');
(async () => {
  const browser = await chromium.launch({executablePath: process.env.CHROME_PATH || '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome', headless: true});
  try {
    const page = await browser.newPage();
    const errors = []; page.on('pageerror', e => errors.push(e.message));
    await page.setContent('<header><button id="choose"></button><button id="reload"></button><button id="history"></button><span id="store"></span></header><p id="message"></p><input id="search"><select id="category"></select><button id="new">New</button><nav id="list"></nav><form id="editor"><p id="identity"></p><p id="notice"></p><div id="fields"></div><button id="save" type="submit">Save</button><button id="delete" type="button">Delete</button><span id="dirty"></span></form><div id="history-list" hidden></div>');
    await page.evaluate(() => { window.sent = []; window.acquireVsCodeApi = () => ({postMessage: m => window.sent.push(m), setState: () => {}, getState: () => null}); });
    await page.addScriptTag({content: await fs.readFile(path.join(__dirname, '../web/experiences.js'), 'utf8')});
    const record = {title: '<b>Entry identity</b>', labels: ['I'], requires: ['entry_snapshot'], excludes: [], summary: {text: 'Capture identity.'}, review: {decision: 'accept'}};
    for (const key of ['applicability', 'event_relation', 'preservation', 'exclusion', 'verification']) record[key] = 'Keep original identity.';
    const data = {type: 'loaded', store: '/synthetic/library', entries: [{id: 'entry', category: 'Personal', file: 'personal.json', revision: 'base', record}], taxonomy: {codebook: [{code: 'I', family: 'Identity'}], mechanism_predicates: {entry_snapshot: 'Entry snapshot'}}};
    await page.evaluate(data => window.dispatchEvent(new MessageEvent('message', {data})), data);
    assert.equal(await page.locator('#field-title').inputValue(), record.title);
    assert.equal(await page.locator('#list b').count(), 0, 'Titles must be rendered as text');
    await page.locator('#field-event_relation').fill('Capture before dispatch.');
    await page.locator('#new').click();
    await page.getByRole('button', {name: 'Cancel', exact: true}).click();
    assert.equal(await page.locator('#field-event_relation').inputValue(), 'Capture before dispatch.');
    await page.locator('#save').click();
    const change = await page.evaluate(() => window.sent.find(m => m.type === 'change').change);
    assert.equal(change.record.event_relation, 'Capture before dispatch.');
    assert.deepEqual(change.record.requires, ['entry_snapshot']);
    assert.equal(change.revision, 'base');
    await page.evaluate(data => window.dispatchEvent(new MessageEvent('message', {data: {...data, type: 'saved', id: 'entry'}})), data);
    await page.locator('#search').fill('absent-query');
    assert.equal(await page.locator('#list button').count(), 0);
    await page.evaluate(record => window.dispatchEvent(new MessageEvent('message', {data: {type: 'history', history: [{id: 'entry', at: '2026-11-25', action: 'save', category: 'Personal', record}]}})), record);
    await page.locator('#history-list button').click();
    assert.equal(await page.locator('#dirty').textContent(), 'Unsaved changes');
    assert.deepEqual(errors, []);
    console.log('PASS: owner editor fields, safe text, dirty guard, direct save, filtering, history restore');
  } finally { await browser.close(); }
})().catch(error => { console.error(error); process.exitCode = 1; });
