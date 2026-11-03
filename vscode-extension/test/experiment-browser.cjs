'use strict';
// Synthetic UI verification only: the server runs a fake CLI, never a model.
const assert=require('node:assert/strict');
const fs=require('node:fs/promises');
const os=require('node:os');
const path=require('node:path');
const {spawn}=require('node:child_process');
const {chromium}=require('playwright');
const repository=path.resolve(__dirname,'../..');

async function main(){
  const temporary=await fs.mkdtemp(path.join(os.tmpdir(),'tca-experiment-browser-'));
  const bench=path.join(temporary,'bench');
  const project=path.join(bench,'cases/synthetic-panel/base');await fs.mkdir(project,{recursive:true});
  const caseRoot=path.dirname(project);await fs.mkdir(path.join(caseRoot,'prompts'));
  await fs.writeFile(path.join(caseRoot,'prompts/maintenance.md'),'Review whether this async refresh can publish stale results.');
  await fs.writeFile(path.join(caseRoot,'case.json'),JSON.stringify({id:'synthetic-panel',title:'Synthetic panel',prompt:'prompts/maintenance.md',reference:'reference/bounded',oracle:{probe:'oracle/probe.py'},runtime:{minimum_version:'3.9'}}));
  await fs.mkdir(path.join(bench,'experiments/temporal-diagnostics-v1'),{recursive:true});
  await fs.writeFile(path.join(bench,'experiments/temporal-diagnostics-v1/corpus.json'),JSON.stringify({cases:[{id:'synthetic-panel',manifest:'cases/synthetic-panel/case.json',adapter:'python',language:'python',conditions:['latent-maintenance']}]}));
  await fs.writeFile(path.join(bench,'.bench.local.json'),JSON.stringify({model:'SYNTHETIC_UI_CHECK_ONLY'}));
  await fs.writeFile(path.join(project,'panel.py'),'async def refresh():\n    await fetch()\n    publish()\n');
  await fs.mkdir(path.join(caseRoot,'reference/bounded'),{recursive:true});
  await fs.copyFile(path.join(project,'panel.py'),path.join(caseRoot,'reference/bounded/panel.py'));
  await fs.mkdir(path.join(caseRoot,'oracle'));
  await fs.writeFile(path.join(caseRoot,'oracle/probe.py'),`import json,sys,pathlib
passed='async def refresh' in pathlib.Path(sys.argv[1],'panel.py').read_text()
print(json.dumps({'case_id':'synthetic-panel','verdict':'PASS' if passed else 'UNDERREACH','schedules':{'synthetic-check':{'passed':passed}}}))
sys.exit(0 if passed else 1)
`);

  const emptyRoot=path.join(bench,'cases/synthetic-empty');
  await fs.mkdir(path.join(emptyRoot,'base'),{recursive:true});
  await fs.mkdir(path.join(emptyRoot,'prompts'));
  await fs.writeFile(path.join(emptyRoot,'base/panel.py'),'async def refresh():\n    return 1\n');
  await fs.writeFile(path.join(emptyRoot,'prompts/maintenance.md'),'Review this function.');
  await fs.writeFile(path.join(emptyRoot,'case.json'),JSON.stringify({id:'synthetic-empty',title:'Empty report case',prompt:'prompts/maintenance.md'}));
  const corpusPath=path.join(bench,'experiments/temporal-diagnostics-v1/corpus.json');
  const corpus=JSON.parse(await fs.readFile(corpusPath,'utf8'));
  corpus.cases.push({id:'synthetic-empty',manifest:'cases/synthetic-empty/case.json',adapter:'python',language:'python',conditions:['latent-maintenance']});
  await fs.writeFile(corpusPath,JSON.stringify(corpus));

  const codexHome=path.join(temporary,'codex-home');await fs.mkdir(codexHome);
  await fs.writeFile(path.join(codexHome,'models_cache.json'),JSON.stringify({fetched_at:'synthetic-cache',models:[{slug:'gpt-5.6-luna',visibility:'list',default_reasoning_level:'medium',supported_reasoning_levels:[{effort:'low'},{effort:'medium'}]}]}));
  const fake=path.join(temporary,'fake-codex');
  await fs.writeFile(fake,`#!/usr/bin/python3
import json, pathlib, sys
if sys.argv[1:]==['--version']:
    print('SYNTHETIC_UI_CHECK_ONLY 0.0');sys.exit(0)
args=sys.argv[1:]; prompt=sys.stdin.read()
pathlib.Path(args[args.index('-o')+1]).write_text('SYNTHETIC_UI_CHECK_ONLY: '+('with report' if '<temporal-review-material>' in prompt else 'without report'))
print(json.dumps({'type':'turn.completed','usage':{'input_tokens':11,'output_tokens':3}}))
`);await fs.chmod(fake,0o755);
  const script=`import json,sys
sys.path.insert(0,sys.argv[1])
from temporal_contract_analyzer.hub import ReportServer
server=ReportServer(sys.argv[2]);server.experiments.codex=sys.argv[3]
print(json.dumps({'url':server.url}),flush=True)
try: server.serve_forever()
finally: server.server_close()
`;
  const server=spawn('/usr/bin/python3',['-I','-S','-B','-c',script,repository,path.join(temporary,'reports'),fake],{env:{...process.env,TCA_CONFIG:path.join(temporary,'config.json'),TCA_BENCH_ROOT:bench,CODEX_HOME:codexHome},stdio:['ignore','pipe','pipe']});
  const exit=new Promise(resolve=>server.once('exit',resolve));let browser,page;
  try{
    const address=await new Promise((resolve,reject)=>{let output='';const timer=setTimeout(()=>reject(new Error('Server startup timeout')),10000);server.stdout.on('data',chunk=>{output+=chunk.toString();if(output.includes('\n')){clearTimeout(timer);resolve(JSON.parse(output.split('\n')[0]));}});server.once('error',reject);server.stderr.on('data',data=>process.stderr.write(data));});
    browser=await chromium.launch({executablePath:process.env.CHROME_PATH||'/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',headless:true});
    page=await browser.newPage({viewport:{width:1440,height:1000}});const errors=[];page.on('pageerror',e=>errors.push(e.message));
    await page.goto(address.url);await page.getByRole('link',{name:'Codex 实验'}).click();
    await page.getByRole('heading',{name:'案例目录',exact:true}).waitFor();
    await page.getByRole('button',{name:'运行案例 synthetic-empty',exact:true}).click();
    await page.getByRole('button',{name:'开始运行',exact:true}).click();
    await page.locator('#run-error').filter({hasText:'源码报告为空'}).waitFor();
    assert.equal(await page.locator('#case-dialog').evaluate(n=>n.open),true);
    assert.equal((await(await page.request.get(address.url+'/api/experiments')).json()).items.length,0);
    assert(!page.url().includes('#experiment='));
    await page.getByRole('button',{name:'关闭运行配置'}).click();
    await page.getByRole('button',{name:'运行中心',exact:true}).click();
    await page.getByRole('heading',{name:'运行中心',exact:true}).waitFor();
    await page.getByText('当前没有正在运行的网页实验。',{exact:true}).waitFor();
    await page.getByRole('button',{name:'关闭运行中心'}).click();
    await page.getByRole('button',{name:'运行案例 synthetic-panel',exact:true}).click();
    await page.getByRole('heading',{name:'Synthetic panel',exact:true}).waitFor();
    assert.equal(await page.locator('[name=candidate], [name=task], #experiment-dialog').count(),0);
    await page.getByLabel('模型',{exact:true}).selectOption('gpt-5.6-luna');
    assert.equal(await page.locator('.experiment-advanced').getAttribute('open'),null);
    await page.screenshot({path:'/tmp/tca-case-selection.png',fullPage:true});
    assert(await page.getByLabel('推理强度',{exact:true}).isVisible());
    await page.getByRole('button',{name:'开始运行',exact:true}).click();
    await page.waitForURL(/#experiment=e-/);
    const id=new URL(page.url()).hash.split('=')[1];
    let finished;const deadline=Date.now()+10000;
    do {finished=await(await page.request.get(address.url+'/api/experiments/'+id)).json();if(finished.status==='failed'||finished.jobs.every(j=>j.evaluation?.status==='passed'))break;await new Promise(resolve=>setTimeout(resolve,100));}while(Date.now()<deadline);
    assert.equal(finished.status,'completed',JSON.stringify(finished));
    assert(finished.jobs.every(j=>j.task_success==='passed'),JSON.stringify(finished));
    assert.equal(finished.model_override,'gpt-5.6-luna');
    assert.equal(finished.effort,'medium');
    assert(!finished.jobs[0].command.includes('--ignore-user-config'));
    assert.equal(finished.jobs[0].command[finished.jobs[0].command.indexOf('-m')+1],'gpt-5.6-luna');
    // Results must appear through polling, without a manual page reload.
    await page.locator('td .pill').filter({hasText:/^成功$/}).first().waitFor();
    await page.getByRole('button',{name:'查看材料'}).first().waitFor();
    assert.equal(await page.locator('td .pill').filter({hasText:/^成功$/}).count(),2);
    assert.equal(await page.locator('.summary-strip .metric').first().innerText(),'2成功');
    await page.getByRole('button',{name:'最终回答',exact:true}).click();
    await page.getByText('SYNTHETIC_UI_CHECK_ONLY: without report',{exact:true}).waitFor();
    await page.getByRole('button',{name:'查看材料'}).nth(1).click();
    await page.getByRole('button',{name:'最终回答',exact:true}).click();
    await page.getByText('SYNTHETIC_UI_CHECK_ONLY: with report',{exact:true}).waitFor();
    await page.getByText('提示词、日志与运行记录',{exact:true}).click();
    await page.getByRole('button',{name:'执行轨迹',exact:true}).click();
    await page.locator('.experiment-log').filter({hasText:'turn.completed'}).waitFor();
    await page.getByRole('link',{name:'← 运行档案',exact:true}).click();
    await page.getByRole('heading',{name:'运行档案',exact:true}).waitFor();
    await page.locator('#experiment-list .report-row').click();
    await page.locator('td .pill').filter({hasText:/^成功$/}).first().waitFor();
    await page.getByRole('button',{name:'运行中心',exact:true}).click();
    await page.locator('#recent-experiments .report-row').click();
    assert.equal(await page.locator('#experiments-dialog').evaluate(n=>n.open),false);
    const original=await fs.readFile(path.join(project,'panel.py'),'utf8');assert.match(original,/async def refresh/);
    console.log('PASS: choose cached earlier model with local Codex/config; no manual path/task fields; both fake CLI jobs and outputs are inspectable; oracle success is shown separately');
    await page.screenshot({path:'/tmp/tca-experiment-workbench.png',fullPage:true});
    await page.setViewportSize({width:390,height:844});
    assert(await page.evaluate(()=>document.documentElement.scrollWidth<=window.innerWidth));
    await page.getByRole('link',{name:/01.*案例目录/}).click();
    await page.getByLabel('搜索案例').fill('no-matching-case');
    await page.getByText('没有匹配的案例。',{exact:true}).waitFor();
    await page.getByLabel('搜索案例').fill('synthetic');
    await page.getByRole('button',{name:'运行案例 synthetic-panel',exact:true}).click();
    assert(await page.evaluate(()=>document.documentElement.scrollWidth<=window.innerWidth));
    await page.getByLabel('重复次数',{exact:true}).fill('0');
    await page.getByRole('button',{name:'开始运行',exact:true}).click();
    assert.equal(await page.locator('#repeats').evaluate(n=>n.validity.valid),false);
    assert.equal(await page.locator('#case-dialog').evaluate(n=>n.open),true);
    await page.getByRole('button',{name:'关闭运行配置'}).click();
    assert.deepEqual(errors,[]);console.log('PASS: no browser exceptions or mobile horizontal overflow');
  }catch(error){if(page){await page.screenshot({path:'/tmp/tca-experiment-browser-failure.png',fullPage:true});console.error(page.url(),await page.locator('#notice').innerText(),await page.locator('#experiment-detail').innerText());}throw error;}
  finally{if(browser)await browser.close();server.kill('SIGTERM');await exit;await fs.rm(temporary,{recursive:true,force:true});}
}
main().catch(error=>{console.error(error);process.exitCode=1;});
