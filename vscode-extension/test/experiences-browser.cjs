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
    const template = await fs.readFile(path.join(__dirname, '../web/experiences.html'), 'utf8');
    await page.setContent(template.replace(/<meta http-equiv="Content-Security-Policy"[^>]*>/, '').replace(/<link[^>]*>/, '').replace(/<script[^>]*>[\s\S]*?<\/script>/, ''));
    await page.addStyleTag({content: await fs.readFile(path.join(__dirname, '../web/experiences.css'), 'utf8')});
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
    await page.locator('#search').fill('');
    await page.locator('#list button').click();
    await page.getByRole('button', {name: 'Continue', exact: true}).click();
    assert.equal(await page.locator('.metadata').getAttribute('open'), null);
    await page.getByText('Labels & mechanisms', {exact: true}).click();
    await page.locator('#field-requires').selectOption([]);
    await page.getByText('Labels & mechanisms', {exact: true}).click();
    await page.locator('#save').click();
    assert.equal(await page.locator('#field-requires').isVisible(), true, 'Invalid required fields must expand');
    await page.locator('#field-requires').selectOption('entry_snapshot');
    await page.evaluate(data => window.dispatchEvent(new MessageEvent('message', {data})), data);
    await page.evaluate(() => window.dispatchEvent(new MessageEvent('message', {data: {type: 'error', message: 'Library changed outside the editor.'}})));
    assert.equal(await page.locator('#message').getAttribute('class'), 'error');
    await page.evaluate(data => window.dispatchEvent(new MessageEvent('message', {data})), data);
    const themes = {
      dark: {'editor-background': '#1f1f1f', 'sideBar-background': '#181818', foreground: '#cccccc', descriptionForeground: '#9d9d9d', 'panel-border': '#333333', 'input-background': '#313131', 'input-foreground': '#cccccc', 'button-background': '#0078d4', 'button-foreground': '#ffffff', 'list-inactiveSelectionBackground': '#37373d', focusBorder: '#0078d4'},
      light: {'editor-background': '#ffffff', 'sideBar-background': '#f8f8f8', foreground: '#3b3b3b', descriptionForeground: '#616161', 'panel-border': '#e5e5e5', 'input-background': '#ffffff', 'input-foreground': '#3b3b3b', 'button-background': '#0078d4', 'button-foreground': '#ffffff', 'button-secondaryBackground': '#e5e5e5', 'list-inactiveSelectionBackground': '#e4e6f1', focusBorder: '#005fb8', 'badge-background': '#e5e5e5', 'badge-foreground': '#3b3b3b', 'textLink-foreground': '#005fb8'},
      'high-contrast': {'editor-background': '#000000', 'sideBar-background': '#000000', foreground: '#ffffff', descriptionForeground: '#ffffff', 'panel-border': '#6fc3df', 'input-background': '#000000', 'input-foreground': '#ffffff', 'button-background': '#000000', 'button-foreground': '#ffffff', 'list-inactiveSelectionBackground': '#000000', focusBorder: '#f38518', contrastActiveBorder: '#f38518'},
    };
    for (const [theme, tokens] of Object.entries(themes)) {
      await page.evaluate(({theme, tokens}) => {
        document.body.className = `vscode-${theme}`; document.documentElement.removeAttribute('style');
        for (const [key, value] of Object.entries(tokens)) document.documentElement.style.setProperty(`--vscode-${key}`, value);
      }, {theme, tokens});
      for (const width of [1280, 800, 390]) {
        await page.setViewportSize({width, height: 900});
        assert.equal(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth), true, `${theme} at ${width}px must not overflow`);
        assert.equal(await page.locator('#save').isVisible(), true);
      }
    }
    assert.deepEqual(errors, []);
    console.log('PASS: actual editor template, safe text, dirty guard, save, filtering, history, required-field expansion and dark/light/high-contrast responsive layouts');
  } finally { await browser.close(); }
})().catch(error => { console.error(error); process.exitCode = 1; });
