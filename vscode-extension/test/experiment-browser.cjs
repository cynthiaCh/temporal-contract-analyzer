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
  await fs.writeFile(path.join(caseRoot,'case.json'),JSON.stringify({id:'synthetic-panel',title:'Synthetic panel',prompt:'prompts/maintenance.md'}));
  await fs.mkdir(path.join(bench,'experiments/temporal-diagnostics-v1'),{recursive:true});
  await fs.writeFile(path.join(bench,'experiments/temporal-diagnostics-v1/corpus.json'),JSON.stringify({cases:[{id:'synthetic-panel',manifest:'cases/synthetic-panel/case.json',adapter:'python',language:'python',conditions:['latent-maintenance']}]}));
  await fs.writeFile(path.join(bench,'.bench.local.json'),JSON.stringify({model:'SYNTHETIC_UI_CHECK_ONLY'}));
  await fs.writeFile(path.join(project,'panel.py'),'async def refresh():\n    await fetch()\n    publish()\n');
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
  const server=spawn('/usr/bin/python3',['-I','-S','-B','-c',script,repository,path.join(temporary,'reports'),fake],{env:{...process.env,TCA_CONFIG:path.join(temporary,'config.json'),TCA_BENCH_ROOT:bench},stdio:['ignore','pipe','pipe']});
  const exit=new Promise(resolve=>server.once('exit',resolve));let browser,page;
  try{
    const address=await new Promise((resolve,reject)=>{let output='';const timer=setTimeout(()=>reject(new Error('Server startup timeout')),10000);server.stdout.on('data',chunk=>{output+=chunk.toString();if(output.includes('\n')){clearTimeout(timer);resolve(JSON.parse(output.split('\n')[0]));}});server.once('error',reject);server.stderr.on('data',data=>process.stderr.write(data));});
    browser=await chromium.launch({executablePath:process.env.CHROME_PATH||'/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',headless:true});
    page=await browser.newPage({viewport:{width:1440,height:1000}});const errors=[];page.on('pageerror',e=>errors.push(e.message));
    await page.goto(address.url);await page.getByRole('link',{name:'Codex 实验'}).click();
    await page.getByRole('heading',{name:'选案例，用本地 Codex 运行。'}).waitFor();
    await page.locator('[name=case][value=synthetic-panel]').check();
    assert.equal(await page.locator('[name=candidate], [name=task], #experiment-dialog, #model').count(),0);
    assert.equal(await page.locator('.experiment-advanced').getAttribute('open'),null);
    await page.screenshot({path:'/tmp/tca-case-selection.png',fullPage:true});
    await page.getByRole('button',{name:'运行实验',exact:true}).click();
    await page.waitForURL(/#experiment=e-/);
    const id=new URL(page.url()).hash.split('=')[1];
    let finished;const deadline=Date.now()+10000;
    do {finished=await(await page.request.get(address.url+'/api/experiments/'+id)).json();if(finished.status==='completed'||finished.status==='failed')break;await new Promise(resolve=>setTimeout(resolve,100));}while(Date.now()<deadline);
    assert.equal(finished.status,'completed',JSON.stringify(finished));
    await page.reload();await page.getByRole('button',{name:'查看材料'}).first().waitFor();
    await page.getByRole('button',{name:'最终回答',exact:true}).click();
    await page.getByText('SYNTHETIC_UI_CHECK_ONLY: without report',{exact:true}).waitFor();
    await page.getByRole('button',{name:'查看材料'}).nth(1).click();
    await page.getByRole('button',{name:'最终回答',exact:true}).click();
    await page.getByText('SYNTHETIC_UI_CHECK_ONLY: with report',{exact:true}).waitFor();
    await page.getByRole('button',{name:'执行轨迹',exact:true}).click();
    await page.waitForFunction(()=>document.querySelector('.experiment-log')?.textContent.includes('turn.completed'));
    const original=await fs.readFile(path.join(project,'panel.py'),'utf8');assert.match(original,/async def refresh/);
    console.log('PASS: choose case then use local Codex; no model/path/task fields; both fake CLI jobs and outputs are inspectable');
    await page.screenshot({path:'/tmp/tca-experiment-workbench.png',fullPage:true});
    await page.setViewportSize({width:390,height:844});
    assert(await page.evaluate(()=>document.documentElement.scrollWidth<=window.innerWidth));
    assert.deepEqual(errors,[]);console.log('PASS: no browser exceptions or mobile horizontal overflow');
  }catch(error){if(page){await page.screenshot({path:'/tmp/tca-experiment-browser-failure.png',fullPage:true});console.error(page.url(),await page.locator('#notice').innerText(),await page.locator('#experiment-detail').innerText());}throw error;}
  finally{if(browser)await browser.close();server.kill('SIGTERM');await exit;await fs.rm(temporary,{recursive:true,force:true});}
}
main().catch(error=>{console.error(error);process.exitCode=1;});
