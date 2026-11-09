'use strict';
// Synthetic CLI and oracle only. This verifies controls, not model effectiveness.
const assert=require('node:assert/strict');
const fs=require('node:fs/promises');
const os=require('node:os');
const path=require('node:path');
const {spawn}=require('node:child_process');
const {chromium}=require('playwright');
const repository=path.resolve(__dirname,'../..');
async function main(){
 const temporary=await fs.mkdtemp(path.join(os.tmpdir(),'tca-experience-browser-'));
 const script=`import json, sys
from pathlib import Path
sys.path.insert(0,sys.argv[1]);sys.path.insert(0,str(Path(sys.argv[1])/'tests'))
from test_experience_workbench import synthetic_bench, synthetic_codex
from temporal_contract_analyzer.hub import ReportServer
root=Path(sys.argv[2]);synthetic_bench(root/'bench');synthetic_codex(root/'fake-codex')
server=ReportServer(root/'reports');server.experiments.codex=str(root/'fake-codex')
print(json.dumps({'url':server.url}),flush=True)
try:server.serve_forever()
finally:server.server_close()
`;
 const server=spawn(process.env.TCA_TEST_PYTHON||'/usr/bin/python3',['-B','-c',script,repository,temporary],{env:{...process.env,TCA_CONFIG:path.join(temporary,'config.json'),TCA_BENCH_ROOT:path.join(temporary,'bench')},stdio:['ignore','pipe','pipe']});
 let browser;
 try{
  const address=await new Promise((resolve,reject)=>{let output='';const timer=setTimeout(()=>reject(Error('Startup timeout')),10000);server.stdout.on('data',chunk=>{output+=chunk;if(output.includes('\n')){clearTimeout(timer);resolve(JSON.parse(output.split('\n')[0]));}});server.once('error',reject);server.stderr.on('data',chunk=>process.stderr.write(chunk));});
  browser=await chromium.launch({executablePath:process.env.CHROME_PATH||'/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',headless:true});
  const page=await browser.newPage({viewport:{width:1440,height:1000}});const errors=[];page.on('pageerror',e=>errors.push(e.message));
  await page.goto(address.url);await page.getByRole('link',{name:'七类训练与测试',exact:true}).click();
  await page.locator('#case option[value=development]').waitFor({state:'attached'});
  await page.locator('#case').selectOption('development');await page.locator('#model').fill('SYNTHETIC');await page.locator('#relationship').fill('Synthetic exposed fixtures; no independent generalization.');
  await page.getByRole('button',{name:'新建批次（不调用模型）',exact:true}).click();
  const detail=page.locator('#detail');
  await detail.getByRole('button',{name:'开始预分析（调用模型）',exact:true}).waitFor();
  const devId=new URL(page.url()).hash.slice(1);
  let data=await(await page.request.get(address.url+'/api/experience/'+devId)).json();assert.equal(data.jobs.length,0);
  await detail.getByRole('button',{name:'开始预分析（调用模型）',exact:true}).click();
  async function approve(){await page.locator('#review-reason').waitFor();await page.locator('#review-reason').fill('Synthetic source, rule evidence, preservation and verification checked.');await page.locator('#review-confirm').check();await detail.getByRole('button',{name:'审核通过',exact:true}).click();}
  await approve();await detail.getByRole('button',{name:'开始训练（两次 AUTO＋一次反思）',exact:true}).click();
  await approve();await detail.getByRole('button',{name:'开始两次开发回验',exact:true}).click();
  await detail.getByRole('button',{name:'冻结研究经验',exact:true}).click();
  await detail.getByRole('button',{name:'使用此经验新建测试',exact:true}).click();
  await page.locator('#case').selectOption('test');assert.equal(await page.locator('#parent').inputValue(),devId);
  await page.getByRole('button',{name:'新建批次（不调用模型）',exact:true}).click();
  await detail.getByRole('button',{name:'开始预分析（调用模型）',exact:true}).click();await approve();
  await detail.getByRole('button',{name:'开始 A/B 测试（4 次修复）',exact:true}).click();
  await detail.getByRole('heading',{name:'冻结经验 A/B 测试 · 测试完成',exact:true}).waitFor();
  const testId=new URL(page.url()).hash.slice(1);data=await(await page.request.get(address.url+'/api/experience/'+testId)).json();
  assert.deepEqual(data.jobs.map(j=>j.role),['analysis','B1','A1','A2','B2']);assert.equal(data.test_summary.B.whole_passes,2);assert.equal(data.test_summary.A.whole_passes,0);
  await detail.getByText('证据、提示词、补丁和原始日志',{exact:true}).click();await detail.getByRole('button',{name:'test-inputs.json',exact:true}).click();await detail.locator('.artifact-buttons + pre').filter({hasText:'"source_bound_obligations_and_premises"'}).waitFor();
  await page.screenshot({path:'/tmp/tca-experience-v2-desktop.png',fullPage:true});
  await page.setViewportSize({width:390,height:844});await page.screenshot({path:'/tmp/tca-experience-v2-mobile.png',fullPage:true});
  assert(await page.evaluate(()=>document.documentElement.scrollWidth<=window.innerWidth), 'Mobile overflow');
  await fs.writeFile(path.join(temporary,'sleep-next'),'synthetic slow CLI');
  await page.locator('#kind').selectOption('development');await page.locator('#case').selectOption('development');
  await page.getByRole('button',{name:'新建批次（不调用模型）',exact:true}).click();
  await detail.getByRole('button',{name:'开始预分析（调用模型）',exact:true}).click();
  const cancelId=new URL(page.url()).hash.slice(1);
  await detail.getByRole('button',{name:'取消当前运行',exact:true}).click();
  await detail.getByRole('heading',{name:'经验开发训练 · 已取消',exact:true}).waitFor();
  assert.equal(new URL(page.url()).hash.slice(1),cancelId);
  await fs.unlink(path.join(temporary,'sleep-next'));
  await fs.writeFile(path.join(temporary,'bad-citation-next'),'synthetic bad source anchors');
  await page.getByRole('button',{name:'新建批次（不调用模型）',exact:true}).click();
  await detail.getByRole('button',{name:'开始预分析（调用模型）',exact:true}).click();
  await detail.getByRole('heading',{name:'经验开发训练 · 引用待修正',exact:true}).waitFor();
  const citationId=new URL(page.url()).hash.slice(1);
  const citation=await(await page.request.get(address.url+'/api/experience/'+citationId)).json();
  assert.equal(citation.jobs.length,1);assert.equal(citation.citation_issues.length,2);
  await detail.getByText('obligation_labels[0].evidence[0] · main.py:2',{exact:true}).click();
  await detail.getByText('逐字引用可在第 1 行找到。',{exact:false}).waitFor();
  const corrected=JSON.parse(JSON.stringify(citation.analysis));
  corrected.obligation_labels[0].evidence[0].line=1;
  corrected.facts[0].evidence[0].quote='accepted = True';
  await page.locator('#review-analysis').fill(JSON.stringify({...corrected,contract:'Unapproved new policy'}));
  await page.locator('#review-reason').fill('Correct the frozen source references.');await page.locator('#review-confirm').check();
  await detail.getByRole('button',{name:'校验引用修正（不调用模型）',exact:true}).click();
  await page.locator('#notice').filter({hasText:'仅允许修改 evidence'}).waitFor();
  await page.locator('#review-analysis').fill(JSON.stringify(corrected));
  await detail.getByRole('button',{name:'校验引用修正（不调用模型）',exact:true}).click();
  await detail.getByRole('heading',{name:'经验开发训练 · 待审核 Contract 与分类',exact:true}).waitFor();
  assert.equal(await detail.getByRole('button',{name:'开始训练（两次 AUTO＋一次反思）',exact:true}).count(),0);
  const after=await(await page.request.get(address.url+'/api/experience/'+citationId)).json();assert.equal(after.jobs.length,1);
  assert.equal(after.jobs[0].usage.input_tokens,citation.jobs[0].usage.input_tokens);
  await approve();await detail.getByRole('button',{name:'开始训练（两次 AUTO＋一次反思）',exact:true}).waitFor();
  assert.deepEqual(errors,[]);console.log('SYNTHETIC ONLY: Web development, reviews, freeze, A/B, mobile, cancellation and citation-correction checks passed.');
 }finally{server.kill('SIGTERM');if(browser)await browser.close();await fs.rm(temporary,{recursive:true,force:true});}
}
main().catch(e=>{console.error(e);process.exitCode=1;});
