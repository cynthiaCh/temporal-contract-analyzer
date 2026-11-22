'use strict';
// Real UI/server with synthetic preparation responses; never starts models or Docker jobs.
const assert = require('node:assert/strict');
const fs = require('node:fs/promises');
const os = require('node:os');
const path = require('node:path');
const {spawn} = require('node:child_process');
const {chromium} = require('../../vscode-extension/node_modules/playwright');

async function main() {
  const temporary = await fs.mkdtemp(path.join(os.tmpdir(), 'tempoevo-prepare-ui-'));
  const server = spawn(process.env.PYTHON || 'python3', ['-B', path.join(__dirname,'serve.py'), '--port','0','--runs',path.join(temporary,'runs')], {stdio:['ignore','pipe','pipe']});
  let browser;
  const exit = new Promise(resolve=>server.once('exit',resolve));
  try {
    const address = await new Promise((resolve,reject)=>{
      let output='';const timer=setTimeout(()=>reject(Error('Server startup timed out')),10000);
      server.stdout.on('data',chunk=>{output+=chunk;if(output.includes('\n')){clearTimeout(timer);resolve(JSON.parse(output.split('\n')[0]).url);}});
      server.once('error',reject);
    });
    browser=await chromium.launch({executablePath:process.env.CHROME_PATH || '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',headless:true});
    const page=await browser.newPage();const errors=[];page.on('pageerror',e=>errors.push(e.message));
    let submitted=0, release, fail=true, exists=false;
    const config={mode:'testing',count:1};
    const result={meta:{id:'run-synthetic',recorded:false,status:'preparing',config,model:{}},cases:[],events:[{at:'SYNTHETIC',kind:'PREPARE',message:'Preparing controls. No model requests.'}],preparation_log:'',passed:0,failed:0,unscored:0};
    await page.route('**/api/runs',r=>r.fulfill({json:exists?[{id:'run-synthetic',title:'Synthetic preparation'}]:[]}));
    await page.route(/\/api\/run\?/,r=>r.fulfill({json:result}));
    await page.route('**/api/prepare',async route=>{
      submitted++;assert.equal(route.request().postDataJSON().mode,'testing');
      await new Promise(resolve=>{release=resolve;});
      if(fail)await route.fulfill({status:400,json:{error:'Benchmark directory was not found: /synthetic/missing'}});
      else {exists=true;await route.fulfill({status:202,json:{id:'run-synthetic'}});}
    });
    await page.goto(address);await page.locator('#prepare:not([disabled])').waitFor();await page.click('#testing-nav');
    const benchmark=await page.locator('#benchmark').inputValue();assert(benchmark);
    await page.locator('#benchmark').evaluate(e=>{e.value='';});
    await page.click('#prepare');
    assert.equal(submitted,0);assert(await page.locator('#environment-options').evaluate(e=>e.open));
    assert.match(await page.locator('#prepare-feedback').innerText(),/Benchmark directory/);
    await page.fill('#benchmark',benchmark);await page.locator('#environment-options').evaluate(e=>{e.open=false;});
    await page.click('#prepare');await page.waitForFunction(()=>document.querySelector('#prepare').getAttribute('aria-busy')==='true');
    assert(await page.locator('#prepare').isDisabled());assert.match(await page.locator('#prepare').innerText(),/Preparing testing/);
    await page.waitForFunction(()=>document.querySelector('#prepare-feedback').textContent.includes('Checking inputs'));
    while(!release)await new Promise(r=>setTimeout(r,10));release();
    await page.getByText('Benchmark directory was not found: /synthetic/missing',{exact:true}).first().waitFor();
    assert(await page.locator('#environment-options').evaluate(e=>e.open));
    assert.equal(await page.locator('#prepare').isDisabled(),false);
    fail=false;release=null;await page.click('#prepare');
    while(!release)await new Promise(r=>setTimeout(r,10));release();
    try { await page.getByText('Preparation events · no model calls',{exact:true}).waitFor({timeout:5000}); } catch(error) { console.error(await page.locator('#notice').textContent(), await page.locator('#artifact').textContent(), errors); throw error; }
    assert.match(await page.locator('#artifact').innerText(),/Preparing controls/);
    assert(await page.locator('#execute').isDisabled());
    result.meta.status='preparation_failed';result.meta.error='Synthetic evaluator failure';result.preparation_log='SYNTHETIC control failed before any model request';
    await page.click('#refresh');await page.locator('#run-error').getByText('Synthetic evaluator failure',{exact:true}).waitFor();
    assert.equal(await page.locator('#feedback-detail').textContent(),'Synthetic evaluator failure');
    assert.match(await page.locator('#artifact').innerText(),/SYNTHETIC control failed/);
    assert.equal(submitted,2);assert.deepEqual(errors,[]);
    console.log('PASS: invalid collapsed fields, pending requests, preparation errors and live logs are visible; no execution requests');
  } finally {
    if(browser)await browser.close();server.kill();await exit;await fs.rm(temporary,{recursive:true,force:true});
  }
}
main().catch(error=>{console.error(error);process.exitCode=1;});
