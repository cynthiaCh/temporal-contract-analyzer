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
  const before = '<template><div>😀</div></template>\n<script setup>channel.connect(); channel.addEventListener("ready", done);</script>\n';
  await fs.writeFile(candidate, before);
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
    await page.getByText('让每一次分析都可以回看').waitFor();
    console.log('PASS: empty archive explains its state');
    await page.locator('#new-scan').click();
    await page.locator('[name=candidate]').fill(project);
    await page.locator('[name=project]').fill('Vue 工作区 · 浏览器测试');
    await page.locator('[name=label]').fill('监听注册顺序 · 修改前');
    await page.locator('#scan-submit').click();
    await page.locator('.finding').first().waitFor();
    assert.match(await page.locator('#detail').innerText(),/connect-before-listen/);
    const reportBefore = new URL(page.url()).hash.split('=')[1];
    console.log('PASS: browser scan produces an archived report and evidence');

    await page.locator('.source-link').first().click();
    await page.locator('.code-line.highlight').first().waitFor();
    assert.match(await page.locator('#source-code').innerText(),/channel.connect/);
    console.log('PASS: evidence opens and highlights the archived source');
    await page.getByRole('tab',{name:'证据与核查'}).click();
    await page.locator('.review-box summary').first().click();
    await page.locator('.note-form textarea').first().fill('需要确认 connect 是否同步通知；这是测试记录。');
    await page.locator('.note-form button').first().click();
    await page.getByText('需要确认 connect 是否同步通知；这是测试记录。',{exact:false}).first().waitFor();
    console.log('PASS: researcher annotations are persisted separately');

    await fs.writeFile(candidate,'<script setup>channel.addEventListener("ready", done); channel.connect();</script>');
    await page.getByRole('button',{name:'以此为基线扫描'}).click();
    await page.locator('[name=label]').fill('监听注册顺序 · 修改后');
    await page.locator('#scan-submit').click();
    await page.locator('.detail-title').getByRole('heading',{name:'监听注册顺序 · 修改后'}).waitFor();
    await page.getByRole('tab',{name:'前后对比'}).click();
    await page.getByRole('button',{name:'与当前报告对比'}).click();
    await page.getByText('新增提示 · 1').waitFor();
    assert.match(await page.locator('#tab-content').innerText(),/listen-before-connect/);
    assert.match(await page.locator('#tab-content').innerText(),/connect-before-listen/);
    console.log('PASS: linked before/after reports compare syntax hints');

    await page.goto(address.url+'/#report='+reportBefore);
    await page.getByRole('tab',{name:'源码快照'}).click();
    await page.locator('#source-code').getByText(/channel.connect/).first().waitFor();
    assert.match(await page.locator('#source-code').innerText(),/channel.connect\(\); channel.addEventListener/);
    await page.getByRole('tab',{name:'证据与核查'}).click();
    await fs.mkdir(path.join(repository,'dist'),{recursive:true});
    await page.screenshot({path:path.join(repository,'dist/report-center-desktop.png'),fullPage:true});
    console.log('PASS: historical snapshot survives working-tree changes and page reload');

    await page.locator('#origin').selectOption('codex');
    await page.getByText('没有符合条件的报告。可新建扫描，或清除筛选条件。').waitFor();
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
