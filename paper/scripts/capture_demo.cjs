'use strict';
// Capture the actual Chinese UI. No translated or invented interface elements.
const fs = require('node:fs/promises');
const os = require('node:os');
const path = require('node:path');
const {spawn} = require('node:child_process');
const repo = path.resolve(__dirname, '../..');
const {chromium} = require(path.join(repo, 'vscode-extension/node_modules/playwright'));
async function main() {
  const temp = await fs.mkdtemp(path.join(os.tmpdir(), 'tca-paper-demo-'));
  const project = path.join(temp, 'synthetic-panel');
  await fs.mkdir(project);
  await fs.copyFile(path.join(repo, 'paper/demo/unguarded/panel.cjs'), path.join(project,'panel.cjs'));
  const child = spawn(process.env.TCA_PYTHON || '/usr/bin/python3',
    ['-I','-S','-B',path.join(repo,'temporal_contract_analyzer/hub_entry.py'),
     'reports','serve','--store',path.join(temp,'reports'),'--port','0'],
    {env:{...process.env,TCA_CONFIG:path.join(temp,'config.json')},stdio:['ignore','pipe','pipe']});
  let browser;
  const exited = new Promise(resolve => child.once('exit', resolve));
  try {
    const address = await new Promise((resolve,reject) => {
      let output='';const timer=setTimeout(()=>reject(new Error('Startup timeout')),15000);
      child.stdout.on('data',data=>{output+=data.toString();if(output.includes('\n')){
        clearTimeout(timer);resolve(JSON.parse(output.split('\n')[0]));}});
      child.once('error',reject);child.stderr.on('data',data=>process.stderr.write(data));
    });
    browser = await chromium.launch({executablePath:process.env.CHROME_PATH || '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',headless:true});
    const page = await browser.newPage({viewport:{width:1440,height:1100},deviceScaleFactor:1.5});
    await page.goto(address.url);
    await page.locator('#new-scan').click();
    await page.locator('[name=candidate]').fill(project);
    await page.locator('[name=project]').fill('Synthetic panel · paper demonstration');
    await page.locator('[name=label]').fill('Synthetic example · unguarded continuation');
    await page.locator('#scan-submit').click();
    await page.locator('.boundary-card').first().waitFor();
    await page.locator('.boundary-card .source-link').first().click();
    await page.locator('.code-line.highlight').first().waitFor();
    await page.screenshot({path:path.join(repo,'paper/figures/workbench-source.png'),fullPage:false});
    await page.getByRole('tab',{name:'边界审查卡'}).click();
    await page.locator('.boundary-card').first().screenshot({path:path.join(repo,'paper/figures/workbench.png')});
    // Scripted author demonstration, not an independent participant judgment.
    await page.locator('.boundary-card .review-box summary').first().click();
    await page.getByLabel('关系是否成立').first().selectOption('confirmed');
    await page.getByLabel('现有保护是否充分').first().selectOption('insufficient');
    await page.getByLabel('仓库要求与保护依据').first().fill(
      'Author demonstration: paper/demo/README.md supplies the requirement. panel.cjs refresh and close share the lexical epoch; no check constrains publish after closure.');
    await page.getByLabel('尚缺什么证据').first().fill(
      'Only the synthetic close-before-resolution schedule was replayed; real-project and other-schedule evidence remains uncollected.');
    await page.locator('.note-form textarea').first().fill(
      'Scripted author demonstration only. Under the supplied requirement and replay schedule, the unguarded continuation publishes an obsolete result.');
    await page.locator('.note-form button').first().click();
    await page.locator('.annotation').first().waitFor();
    const reportId=new URL(page.url()).hash.split('=')[1];
    const response=await page.request.get(address.url+'/api/reports/'+reportId);
    const data=await response.json();
    await fs.writeFile(path.join(repo,'paper/evidence/demo-archive.json'),JSON.stringify(data,null,2)+'\n');
    // Same project path and scope, so the second archive can be compared.
    await fs.copyFile(path.join(repo,'paper/demo/guarded/panel.cjs'),path.join(project,'panel.cjs'));
    const scanAfter=await page.request.post(address.url+'/api/scans',{
      headers:{'X-TCA-Request':'local'},
      data:{candidate:project,label:'Synthetic example · reviewer-supplied epoch check',parent_report_id:reportId}});
    if(scanAfter.status()!==201)throw new Error(await scanAfter.text());
    const afterMeta=await scanAfter.json();
    const afterResponse=await page.request.get(address.url+'/api/reports/'+afterMeta.report_id);
    const after=await afterResponse.json();
    const comparisonResponse=await page.request.get(address.url+'/api/compare?before='+reportId+'&after='+afterMeta.report_id);
    if(!comparisonResponse.ok())throw new Error(await comparisonResponse.text());
    const comparison=await comparisonResponse.json();
    if(!comparison.comparable)throw new Error('Synthetic archives unexpectedly incomparable');
    await fs.writeFile(path.join(repo,'paper/evidence/demo-archive-guarded.json'),JSON.stringify(after,null,2)+'\n');
    await fs.writeFile(path.join(repo,'paper/evidence/demo-comparison.json'),JSON.stringify(comparison,null,2)+'\n');
    console.log(JSON.stringify({screenshot:'paper/figures/workbench.png',before_id:reportId,after_id:afterMeta.report_id,comparable:comparison.comparable,findings:data.report.findings.map(x=>x.rule),synthetic:true}));
  } finally {
    if(browser)await browser.close();
    child.kill('SIGTERM');await exited;
    await fs.rm(temp,{recursive:true,force:true});
  }
}
main().catch(error=>{console.error(error);process.exitCode=1;});
