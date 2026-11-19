'use strict';
// Exercise the real browser and server against a temporary, explicitly synthetic project.
const assert = require('node:assert/strict');
const fs = require('node:fs/promises');
const os = require('node:os');
const path = require('node:path');
const {spawn} = require('node:child_process');
const {chromium} = require('playwright');
const repository = path.resolve(__dirname, '../..');

async function main() {
  const temporary = await fs.mkdtemp(path.join(os.tmpdir(), 'tca-browser-'));
  const project = path.join(temporary, 'vue-project'); await fs.mkdir(project);
  const candidate = path.join(project, 'Editor.vue');
  const before = '<template><div>😀</div></template>\n<script setup>import {start} from "./worker.js"; start(); channel.connect(); channel.addEventListener("ready", done);</script>\n';
  await fs.writeFile(candidate, before);
  await fs.writeFile(path.join(project,'worker.js'),'export async function start(){ await fetch(); publish(); }');
  await fs.writeFile(path.join(project,'unrelated.js'),'async function unrelated(){ await fetch(); save(); }');
  const store = path.join(temporary, 'reports');
  const server = spawn('/usr/bin/python3', ['-I','-S','-B',path.join(repository,'temporal_contract_analyzer/hub_entry.py'),
    'reports','serve','--store',store,'--port','0'], {env:{...process.env,TCA_CONFIG:path.join(temporary,'config.json')}, stdio:['ignore','pipe','pipe']});
  let browser;
  const exit = new Promise(resolve=>server.once('exit',resolve));
  try {
    const address = await new Promise((resolve,reject)=>{
      let output='';const timeout=setTimeout(()=>reject(new Error('Server startup timed out')),10000);
      server.stdout.on('data',data=>{output+=data.toString();if(output.includes('\n')){clearTimeout(timeout);resolve(JSON.parse(output.split('\n')[0]));}});
      server.once('error',reject);server.stderr.on('data',data=>process.stderr.write(data));
    });
    browser=await chromium.launch({executablePath:process.env.CHROME_PATH || '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',headless:true});
    const page=await browser.newPage({viewport:{width:1440,height:1000}});
    const errors=[];page.on('pageerror',error=>errors.push(error.message));
    await page.goto(address.url);
    await page.getByText('Revisit every analysis').waitFor();
    console.log('PASS: empty archive explains its state');
    await page.locator('#new-scan').click();
    await page.locator('[name=candidate]').fill(project);
    await page.locator('[name=project]').fill('Vue workspace · Browser test');
    await page.locator('[name=label]').fill('Listener registration order · Before');
    await page.locator('#scan-submit').click();
    await page.locator('.finding').first().waitFor();
    assert.match(await page.locator('#detail').innerText(),/connect-before-listen/);
    const reportBefore = new URL(page.url()).hash.split('=')[1];
    console.log('PASS: browser scan produces an archived report and evidence');

    await page.locator('.source-link').first().click();
    await page.locator('.code-line.highlight').first().waitFor();
    assert.match(await page.locator('#source-code').innerText(),/channel.connect/);
    console.log('PASS: evidence opens and highlights the archived source');
    await page.getByRole('tab',{name:'Boundary review'}).click();
    assert.equal(await page.locator('.boundary-card').count(),3);
    assert.equal(await page.getByLabel('Relation judgment').first().inputValue(),'uncertain');
    assert.equal(await page.getByLabel('Protection sufficiency').first().inputValue(),'uncertain');
    for(const question of ['Where is the execution boundary?','What may have changed?','Which effects may be affected?','What requirements and protection apply?'])assert(await page.locator('.boundary-card').first().getByText(question,{exact:true}).isVisible());
    await page.getByLabel('Changed files').fill('Editor.vue');
    await page.getByRole('button',{name:'Filter to changes and related calls'}).click();
    assert.equal(await page.locator('.boundary-card').count(),2);
    assert.match(await page.locator('#tab-content').innerText(),/related files: Editor.vue, worker.js/);
    assert.match(await page.locator('#tab-content').innerText(),/not fully covered/);
    await page.getByLabel('Changed files').fill('not-captured.js');
    await page.getByRole('button',{name:'Filter to changes and related calls'}).click();
    assert.equal(await page.locator('.boundary-card').count(),0);
    assert.match(await page.locator('#tab-content').innerText(),/Paths absent from this snapshot: not-captured.js/);
    await page.getByRole('button',{name:'Show all cards'}).click();
    console.log('PASS: four-question cards default to uncertain and scope uses candidate call links');
    await page.locator('.boundary-card .review-box summary').first().click();
    await page.getByLabel('Relation judgment').first().selectOption('confirmed');
    await page.getByLabel('Protection sufficiency').first().selectOption('insufficient');
    await page.getByLabel('Requirement and protection basis').first().fill('Editor.vue:2; register listeners before connecting; API semantics need review.');
    await page.getByLabel('Missing evidence').first().fill('A reachable synchronous notification trace is still missing.');
    await page.locator('.note-form textarea').first().fill('Need to confirm whether connect notifies synchronously; this is a test record.');
    await page.locator('.note-form button').first().click();
    await page.getByText('Need to confirm whether connect notifies synchronously; this is a test record.',{exact:false}).first().waitFor();
    assert.match(await page.locator('.annotation').first().innerText(),/Protection: Insufficient/);
    assert.match(await page.locator('.annotation').first().innerText(),/A reachable synchronous notification trace is still missing/);
    await page.context().grantPermissions(['clipboard-read','clipboard-write']);
    await page.getByRole('button',{name:'Copy review packet for an agent'}).first().click();
    await page.waitForFunction(()=>navigator.clipboard.readText().then(text=>text.includes('A reachable synchronous notification trace is still missing')));
    const packet=await page.evaluate(()=>navigator.clipboard.readText());
    assert.match(packet,/Editor.vue:2/);assert.match(packet,/Supported; protection: Insufficient/);
    assert.match(packet,/not an oracle verdict/);
    assert.equal(await page.getByRole('tab',{name:'Advanced measurements · E/T/L/H'}).count(),0);
    assert.equal(await page.locator('a[href="/experience"], a[href="/development"], a[href="/experiments"]').count(),0);
    console.log('PASS: structured review and Agent handoff remain available; retired UI is absent');

    await fs.writeFile(candidate,'<script setup>channel.addEventListener("ready", done); channel.connect();</script>');
    await page.getByRole('button',{name:'Scan again from this baseline'}).click();
    await page.locator('[name=label]').fill('Listener registration order · After');
    await page.locator('#scan-submit').click();
    await page.locator('.detail-title').getByRole('heading',{name:'Listener registration order · After'}).waitFor();
    await page.getByRole('button',{name:'Use files changed since baseline'}).click();
    await page.getByText(/Showing 1\/3 candidate cards/).waitFor();
    assert.equal(await page.getByLabel('Changed files').inputValue(),'Editor.vue');
    assert.equal(await page.locator('.boundary-card').count(),1);
    await page.getByRole('tab',{name:'Compare scans'}).click();
    await page.getByRole('button',{name:'Compare with current report'}).click();
    await page.getByText('Added hints · 1').waitFor();
    assert.match(await page.locator('#tab-content').innerText(),/listen-before-connect/);
    assert.match(await page.locator('#tab-content').innerText(),/connect-before-listen/);
    console.log('PASS: linked before/after reports compare syntax hints');

    await page.goto(address.url+'/#report='+reportBefore);
    await page.getByRole('tab',{name:'Source snapshot'}).click();
    await page.locator('#source-code').getByText(/channel.connect/).first().waitFor();
    assert.match(await page.locator('#source-code').innerText(),/channel.connect\(\); channel.addEventListener/);
    await page.getByRole('tab',{name:'Boundary review'}).click();
    await fs.mkdir(path.join(repository,'dist'),{recursive:true});
    assert.match(await page.locator('.annotation').first().innerText(),/Protection: Insufficient/);
    await page.screenshot({path:path.join(repository,'dist/report-center-desktop.png'),fullPage:true});
    await page.setViewportSize({width:390,height:844});
    assert(await page.evaluate(()=>document.documentElement.scrollWidth<=window.innerWidth+1));
    await page.setViewportSize({width:1440,height:1000});
    console.log('PASS: historical snapshot survives working-tree changes and page reload');

    await page.locator('#origin').selectOption('codex');
    await page.getByText('No matching reports. Start a scan or clear the filters.').waitFor();
    await page.locator('#origin').selectOption('web');
    await page.locator('.report-row').nth(1).waitFor();
    assert.equal(await page.locator('.report-row').count(),2);
    console.log('PASS: report filters select the requested source');

    await page.locator('#new-scan').click();
    await page.locator('[name=candidate]').fill(path.join(temporary,'missing'));
    await page.locator('[name=label]').fill('<img src=x onerror="window.injection=true">');
    await page.locator('#scan-submit').click();
    await page.locator('.detail-title .failed').waitFor();
    assert.equal(await page.evaluate(()=>window.injection),undefined);
    assert.equal(await page.locator('#detail img').count(),0);
    console.log('PASS: failed scans remain visible and candidate-controlled labels stay inert');

    await page.setViewportSize({width:390,height:844});
    await page.screenshot({path:path.join(repository,'dist/report-center-mobile.png'),fullPage:true});
    assert(await page.evaluate(()=>document.documentElement.scrollWidth<=window.innerWidth+1));
    assert.deepEqual(errors,[]);
    console.log('PASS: responsive layout has no horizontal page overflow or browser errors');
  } finally {
    if(browser)await browser.close();
    server.kill();await exit;
    await fs.rm(temporary,{recursive:true,force:true});
  }
}
main().catch(error=>{console.error(error);process.exitCode=1;});
