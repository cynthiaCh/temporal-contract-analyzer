'use strict';
// Read-only archive UI checks. No Codex CLI or model is launched.
const assert=require('node:assert/strict');
const fs=require('node:fs/promises');
const os=require('node:os');
const path=require('node:path');
const {spawn}=require('node:child_process');
const {chromium}=require('playwright');
const repository=path.resolve(__dirname,'../..');

async function main(){
  const temporary=await fs.mkdtemp(path.join(os.tmpdir(),'tca-development-browser-'));
  const research=path.join(temporary,'research');
  async function write(batch,name,value){const file=path.join(research,batch,name);await fs.mkdir(path.dirname(file),{recursive:true});await fs.writeFile(file,typeof value==='string'?value:JSON.stringify(value));}
  const summary={case:'Synthetic temporal case',experience:'E2',groups:{A:{condition:'AUTO',started:1,valid_denominator:1,complete_passed:0},B:{condition:'AUTO_EXP',started:1,valid_denominator:1,complete_passed:1}},per_slot:[{slot:'A1',condition:'AUTO',valid:true,verdict:'UNDERREACH',passed_items:1,total_items:2,original_correct_losses:['preserve-history']},{slot:'B1',condition:'AUTO_EXP',valid:true,verdict:'PASS',passed_items:2,total_items:2}]};
  const literal='<img src=x onerror="window.pwned=true">';
  await write('revision','summary.json',summary);
  await write('revision','NEW_EXPERIENCE.md','Preserve shared work.\n'+literal);
  await write('revision','E1.md','Cancel all work.\n');
  await write('revision','reflection-receipt.json',{infrastructure_valid:true,output_format_valid:true});
  await write('revision','experience-freeze.json',{candidate:'E2',before_any_maintenance:true});
  await write('replication','summary.json',{...summary,experience_frozen_no_revision:true,source_batch:'/server/research/revision'});
  await write('replication','NEW_EXPERIENCE.md','Reused experience.');
  await write('stopped','summary.json',{status:'STOPPED',development:[],tests:{T1:{runs:[{slot:'test-A',valid_score:false,execution_status:'NOT_STARTED'}]}},preparation_failure:{material_valid:false},frozen_library:null,stop:{reason:'invalid material'}});
  await write('legacy','summary.json',{development:{D1:{preanalysis:{contract:'Synthetic legacy Contract',primary_class:'T4'}}},tests:{}});
  const code=`import sys,json
sys.path.insert(0,sys.argv[1])
from temporal_contract_analyzer.hub import ReportServer
server=ReportServer(sys.argv[2])
print(json.dumps({'url':server.url}),flush=True)
try: server.serve_forever()
finally: server.server_close()
`;
  const server=spawn('/usr/bin/python3',['-I','-S','-B','-c',code,repository,path.join(temporary,'reports')],{env:{...process.env,TCA_CONFIG:path.join(temporary,'config.json'),TCA_DEVELOPMENT_ROOT:research},stdio:['ignore','pipe','pipe']});
  let browser;
  try{
    const address=await new Promise((resolve,reject)=>{let output='';const timer=setTimeout(()=>reject(new Error('Server startup timeout')),10000);server.stdout.on('data',chunk=>{output+=chunk.toString();if(output.includes('\n')){clearTimeout(timer);resolve(JSON.parse(output.split('\n')[0]));}});server.once('error',reject);server.stderr.on('data',chunk=>process.stderr.write(chunk));});
    browser=await chromium.launch({executablePath:process.env.CHROME_PATH||'/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',headless:true});
    const page=await browser.newPage({viewport:{width:1440,height:1000}}),errors=[],mutations=[];
    page.on('pageerror',error=>errors.push(error.message));page.on('request',request=>{if(request.method()!=='GET')mutations.push(request.url());});
    await page.goto(address.url);await page.getByRole('link',{name:'经验开发',exact:true}).click();
    await page.getByRole('heading',{name:'经验怎样形成'}).waitFor();
    assert.equal(await page.locator('#taxonomy-labels > details').count(),7);
    await page.locator('#obligation-taxonomy > summary').click();
    await page.getByText('R · 就绪条件协调',{exact:true}).waitFor();
    await page.locator('#development-search').fill('revision');
    await page.locator('#development-list a').click();
    await page.getByRole('button',{name:/反思经验/}).click();
    await page.getByText(literal,{exact:false}).first().waitFor();
    assert.equal(await page.evaluate(()=>window.pwned),undefined);
    assert.equal(await page.locator('#development-detail img').count(),0);
    await page.getByRole('button',{name:'NEW_EXPERIENCE.md',exact:true}).click();
    await page.waitForFunction(()=>document.querySelector('.artifact-viewer').textContent.includes('Preserve shared work'));
    await page.getByRole('button',{name:/回验与对照/}).click();
    await page.getByText('0 / 1 整题通过',{exact:true}).waitFor();
    await page.getByText('1 / 1 整题通过',{exact:true}).waitFor();
    await page.getByText('preserve-history',{exact:true}).waitFor();
    await page.goto(address.url+'/development#batch=replication&stage=reflection');
    await page.getByText('本批复用冻结经验，没有新增反思或训练；经验生成见来源批次。',{exact:true}).waitFor();
    await page.getByRole('link',{name:/来源批次/}).click();
    await page.locator('#development-detail .detail-path').getByText('revision',{exact:true}).waitFor();
    await page.goto(address.url+'/development#batch=stopped&stage=case');
    await page.getByText('批次停止：invalid material',{exact:true}).waitFor();
    await page.getByRole('button',{name:/冻结决定/}).click();
    await page.getByText('未启动：依据本批实际记录展示，后续材料不会自动推定为已完成。',{exact:true}).waitFor();
    await page.goto(address.url+'/development#batch=legacy&stage=case');
    await page.getByText('D1 · 候选 Contract · 历史四类路由：T4（未自动换算）',{exact:true}).waitFor();
    await page.locator('#obligation-taxonomy > summary').click();
    await page.setViewportSize({width:390,height:844});
    assert.equal(await page.evaluate(()=>document.documentElement.scrollWidth<=window.innerWidth),true);
    assert.deepEqual(errors,[]);assert.deepEqual(mutations,[]);
    console.log('Development browser checks passed: stages, truthful reuse/stop, raw text, mobile and GET-only navigation.');
  }finally{
    if(browser)await browser.close();
    const exited=new Promise(resolve=>server.once('exit',resolve));server.kill('SIGTERM');await exited;
    await fs.rm(temporary,{recursive:true,force:true});
  }
}
main().catch(error=>{console.error(error);process.exitCode=1;});
