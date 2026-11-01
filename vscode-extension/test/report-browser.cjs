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
    await page.getByRole('tab',{name:'边界审查卡'}).click();
    assert.equal(await page.locator('.boundary-card').count(),3);
    assert.equal(await page.getByLabel('关系是否成立').first().inputValue(),'uncertain');
    assert.equal(await page.getByLabel('现有保护是否充分').first().inputValue(),'uncertain');
    for(const question of ['执行边界在哪里？','什么可能已经变化？','影响什么效果？','仓库要求与保护是什么？'])assert(await page.locator('.boundary-card').first().getByText(question,{exact:true}).isVisible());
    await page.getByLabel('本次改动文件').fill('Editor.vue');
    await page.getByRole('button',{name:'查看改动及相关调用候选'}).click();
    assert.equal(await page.locator('.boundary-card').count(),2);
    assert.match(await page.locator('#tab-content').innerText(),/关联文件：Editor.vue、worker.js/);
    assert.match(await page.locator('#tab-content').innerText(),/未完整覆盖/);
    await page.getByLabel('本次改动文件').fill('not-captured.js');
    await page.getByRole('button',{name:'查看改动及相关调用候选'}).click();
    assert.equal(await page.locator('.boundary-card').count(),0);
    assert.match(await page.locator('#tab-content').innerText(),/未被当前源码快照捕获：not-captured.js/);
    await page.getByRole('button',{name:'查看全部卡片'}).click();
    console.log('PASS: four-question cards default to uncertain and scope uses candidate call links');
    await page.locator('.boundary-card .review-box summary').first().click();
    await page.getByLabel('关系是否成立').first().selectOption('confirmed');
    await page.getByLabel('现有保护是否充分').first().selectOption('insufficient');
    await page.getByLabel('仓库要求与保护依据').first().fill('Editor.vue:2；连接前须完成监听注册，API 语义待核查。');
    await page.getByLabel('尚缺什么证据').first().fill('还缺同步通知的可达轨迹。');
    await page.locator('.note-form textarea').first().fill('需要确认 connect 是否同步通知；这是测试记录。');
    await page.locator('.note-form button').first().click();
    await page.getByText('需要确认 connect 是否同步通知；这是测试记录。',{exact:false}).first().waitFor();
    assert.match(await page.locator('.annotation').first().innerText(),/保护：保护不足/);
    assert.match(await page.locator('.annotation').first().innerText(),/还缺同步通知的可达轨迹/);
    await page.context().grantPermissions(['clipboard-read','clipboard-write']);
    await page.getByRole('button',{name:'复制给 Agent 的核查材料'}).first().click();
    await page.waitForFunction(()=>navigator.clipboard.readText().then(text=>text.includes('还缺同步通知的可达轨迹')));
    const packet=await page.evaluate(()=>navigator.clipboard.readText());
    assert.match(packet,/Editor.vue:2/);assert.match(packet,/核查成立；保护：保护不足/);
    assert.match(packet,/不等于 oracle 判定/);
    await page.getByRole('tab',{name:'高级测量 · E/T/L/H'}).click();
    assert.match(await page.locator('#tab-content').innerText(),/可选的研究分析层/);
    assert.match(await page.locator('#tab-content').innerText(),/还没有义务测量/);
    await page.getByRole('tab',{name:'边界审查卡'}).click();
    console.log('PASS: structured reviews and concise Agent handoff need no full measurement');

    await fs.writeFile(candidate,'<script setup>channel.addEventListener("ready", done); channel.connect();</script>');
    await page.getByRole('button',{name:'以此为基线扫描'}).click();
    await page.locator('[name=label]').fill('监听注册顺序 · 修改后');
    await page.locator('#scan-submit').click();
    await page.locator('.detail-title').getByRole('heading',{name:'监听注册顺序 · 修改后'}).waitFor();
    await page.getByRole('button',{name:'使用基线间变化文件'}).click();
    await page.getByText(/显示 1\/3 张候选卡/).waitFor();
    assert.equal(await page.getByLabel('本次改动文件').inputValue(),'Editor.vue');
    assert.equal(await page.locator('.boundary-card').count(),1);
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
    await page.getByRole('tab',{name:'边界审查卡'}).click();
    await fs.mkdir(path.join(repository,'dist'),{recursive:true});
    assert.match(await page.locator('.annotation').first().innerText(),/保护：保护不足/);
    await page.screenshot({path:path.join(repository,'dist/report-center-desktop.png'),fullPage:true});
    await page.setViewportSize({width:390,height:844});
    assert(await page.evaluate(()=>document.documentElement.scrollWidth<=window.innerWidth+1));
    await page.setViewportSize({width:1440,height:1000});
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
