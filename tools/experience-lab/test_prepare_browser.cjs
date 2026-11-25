'use strict';
// Real UI/server with synthetic preparation/stop responses; never starts models or Docker jobs.
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
    await page.route('**/api/runs',r=>r.fulfill({json:exists?[{id:'run-synthetic',title:'Synthetic preparation',mode:config.mode}]:[]}));
    await page.route(/\/api\/run\?/,r=>r.fulfill({json:result}));
    await page.route('**/api/prepare',async route=>{
      submitted++;assert.equal(route.request().postDataJSON().mode,'testing');
      await new Promise(resolve=>{release=resolve;});
      if(fail)await route.fulfill({status:400,json:{error:'Benchmark directory was not found: /synthetic/missing'}});
      else {exists=true;await route.fulfill({status:202,json:{id:'run-synthetic'}});}
    });
    await page.goto(address);await page.locator('#prepare:not([disabled])').waitFor();await page.click('#testing-nav');
    await page.selectOption('#profile','qoder-efficient');
    assert.match(await page.locator('#profile option:checked').textContent(),/Efficient.*free.*eligible/);
    assert(await page.locator('#profile-note').isVisible());
    assert.match(await page.locator('#profile-note').textContent(),/Service Accounts/);
    await page.selectOption('#profile','sol61-medium');
    assert(await page.locator('#profile-note').isHidden());
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
    await page.click('#training-nav');
    assert.equal(await page.locator('#runs option').count(),0);
    assert.match(await page.locator('#artifact').innerText(),/No training runs yet/);
    assert(await page.locator('#export').isDisabled());
    assert(await page.locator('#execute').isDisabled());
    assert.equal(await page.locator('#run-error').isVisible(),false);
    await page.click('#testing-nav');
    await page.locator('#run-error').getByText('Synthetic evaluator failure',{exact:true}).waitFor();
    assert.equal(await page.locator('#runs').inputValue(),'run-synthetic');
    assert.equal(submitted,2);
    let stopRequests=0, releaseStop;
    await page.route('**/api/start',()=>{throw Error('UI checks must not start execution');});
    await page.route('**/api/stop',async route=>{
      stopRequests++;assert.deepEqual(route.request().postDataJSON(),{id:'run-synthetic'});
      await new Promise(resolve=>{releaseStop=resolve;});
      result.meta.status='stopping';await route.fulfill({status:202,json:{status:'stopping'}});
    });
    for(const testMode of ['testing','learning']){
      config.mode=testMode;result.meta.status='running';delete result.meta.error;
      await page.reload();await page.locator('#prepare:not([disabled])').waitFor();
      if(testMode==='testing')await page.click('#testing-nav');
      await page.getByRole('button',{name:'Stop',exact:true}).waitFor();
      await page.locator('#stop:not([disabled])').waitFor();
      // Stop must precede the expanding feedback/workflow area, including on small screens.
      assert(await page.locator('#stop').evaluate(e=>Boolean(e.compareDocumentPosition(document.querySelector('#run-feedback')) & Node.DOCUMENT_POSITION_FOLLOWING)));
      assert.equal(await page.locator('#stop').evaluate(e=>getComputedStyle(e).backgroundColor),'rgb(255, 77, 79)');
      releaseStop=null;await page.click('#stop');
      while(!releaseStop)await new Promise(r=>setTimeout(r,10));
      assert(await page.locator('#stop').isDisabled());releaseStop();
      await page.getByRole('button',{name:'Stopping…',exact:true}).waitFor();
      assert(await page.locator('#stop').isDisabled());
      assert.match(await page.locator('#stop-note').textContent(),/No new cases will start/);
      result.meta.status='stopped';await page.click('#refresh');
      await page.locator('#run-status').filter({hasText:/^stopped$/}).waitFor();
      assert(await page.locator('#stop').isDisabled());
      assert(await page.locator('#stop-note').isHidden());
    }
    assert.equal(stopRequests,2);assert.deepEqual(errors,[]);
    console.log('PASS: preparation feedback and Stop for testing/training, pending and stopped states; no real execution requests');
  } finally {
    if(browser)await browser.close();server.kill();await exit;await fs.rm(temporary,{recursive:true,force:true});
  }
}
main().catch(error=>{console.error(error);process.exitCode=1;});
