'use strict';
const $ = selector => document.querySelector(selector);
const states = {prepared:'待启动', running:'运行中', completed:'进程完成', failed:'运行失败', cancelled:'已取消', timed_out:'超时', interrupted:'服务中断'};
const layers = {none:'A · 无报告',locations:'B · 位置',facts:'C · 事实',review:'D · 审查',audit:'E · 通用提示',risk:'F · 提示＋信号',audit_review:'G · 提示＋报告'};
let selected, current, jobId, artifactName = 'prompt.md', busy = false, generation = 0;
let catalog, selectedCase, activeExperiment;
function el(tag, cls, text) { const n=document.createElement(tag);if(cls)n.className=cls;if(text!==undefined)n.textContent=text;return n; }
function error(e) { $('#notice').textContent=e.message;$('#notice').classList.remove('hidden'); }
async function api(path, body) {
  const response=await fetch(path,body===undefined?{}:{method:'POST',headers:{'Content-Type':'application/json','X-TCA-Request':'local'},body:JSON.stringify(body)});
  const data=await response.json();if(!response.ok)throw new Error(data.error);return data;
}
function action(text, callback, cls='quiet') {const n=el('button',cls,text);n.type='button';n.addEventListener('click',()=>Promise.resolve().then(callback).catch(error));return n;}
function endpoint(id=selected) { return '/api/experiments/'+encodeURIComponent(id); }
function date(value) {return new Date(value).toLocaleString('zh-CN',{hour12:false});}
async function refreshList() {
  const data=await api('/api/experiments');
  activeExperiment=data.active;updateRun();
  $('#codex-path').textContent=data.codex||'暂未发现本地 Codex';$('#experiment-store').textContent=data.root;
  $('#experiment-count').textContent=data.items.length+' 次';const list=$('#experiment-list');list.replaceChildren();
  for(const row of data.items) {
    const link=el('a','report-row'+(selected===row.id?' selected':''));link.href='#experiment='+row.id;
    link.append(el('div','row-title',row.label),el('div','row-subtitle',`${row.model==='local-default'?'本地 Codex':row.model} · ${row.jobs.length} 次运行`),el('span','pill',states[row.status]||row.status),el('div','row-subtitle',date(row.created_at)));list.append(link);
  }
  if(!data.items.length)list.append(el('p','muted','还没有实验记录。'));
}
function renderCases() {
  const list=$('#case-list');list.replaceChildren();
  const query=$('#case-search').value.trim().toLowerCase();
  const rows=catalog.cases.filter(c=>`${c.id} ${c.title} ${c.language}`.toLowerCase().includes(query));
  $('#case-count').textContent=`${catalog.cases.filter(c=>c.supported).length} 可选`;
  for(const item of rows) {
    const label=el('label','case-choice'+(item.id===selectedCase?' selected':'')+(!item.supported?' unavailable':''));
    const radio=el('input');radio.type='radio';radio.name='case';radio.value=item.id;radio.checked=item.id===selectedCase;radio.disabled=!item.supported;
    radio.addEventListener('change',()=>{selectedCase=item.id;renderCases();updateRun();});
    const text=el('span');text.append(el('strong','',item.id),el('small','',item.supported?item.title:item.unavailable_reason));label.append(radio,text);list.append(label);
  }
  if(!rows.length)list.append(el('p','muted','没有匹配的案例。'));
}
function updateRun() {
  const count=document.querySelectorAll('[name=condition]:checked').length;
  $('#run-selected').disabled=busy||!!activeExperiment||!selectedCase||!count;
  $('#run-selected').textContent=busy?'正在准备并启动…':activeExperiment?'实验运行中':'运行实验';
  $('#run-summary').textContent=selectedCase?`${selectedCase} · ${count} 个报告条件 × ${$('#repeats').value} 次`:'选择案例后运行。';
}
async function loadCatalog() {
  catalog=await api('/api/case-options');
  renderCases();updateRun();
}
async function runSelected() {
  if(busy||activeExperiment||!selectedCase)return;
  busy=true;updateRun();$('#notice').classList.add('hidden');
  try {
    const data={case_id:selectedCase,
      repeats:Number($('#repeats').value),timeout:Number($('#timeout').value),
      conditions:[...document.querySelectorAll('[name=condition]:checked')].map(n=>n.value)};
    const result=await api('/api/experiments',data);
    location.hash='experiment='+result.id;
    await api(endpoint(result.id)+'/start',{});
    await load();
  }catch(e){error(e);}finally{busy=false;await refreshList();updateRun();}
}
async function load() {
  const id=new URLSearchParams(location.hash.slice(1)).get('experiment');if(!id)return;
  const ticket=++generation;
  const data=await api(endpoint(id));if(ticket!==generation)return;
  if(selected!==id){jobId=undefined;artifactName='prompt.md';}
  selected=id;current=data;render();await refreshList();
}
function render() {
  const target=$('#experiment-detail');target.replaceChildren();const header=el('div','detail-header');
  header.append(el('span','eyebrow','FROZEN INPUT → CODEX → ARTIFACTS'),el('h2','',current.label));
  const model=current.local_codex?'本地 Codex 配置':`${current.model} / ${current.effort}`;
  header.append(el('p','detail-path',`${states[current.status]} · ${model} · ${current.jobs.length} 次运行`));
  const controls=el('div','detail-actions');
  const report=el('a','link-button','打开输入扫描报告');report.href='/#report='+current.report_id;report.target='_blank';report.rel='noopener';controls.append(report);
  if(current.status==='prepared')controls.append(action('启动 Codex 实验',async()=>{
    if(busy)return;busy=true;try{await api(endpoint()+'/start',{});await load();}finally{busy=false;}
  },'primary'));
  if(current.status==='running')controls.append(action('取消剩余运行',async()=>{await api(endpoint()+'/cancel',{});await load();}));
  header.append(controls);target.append(header);
  target.append(el('p','scope-notice','报告已固定在初始提示词中；每次使用独立代码副本。进程完成不代表任务成功，材料交付不代表 Codex 采用了报告。'));
  if(current.error)target.append(el('p','error-block',current.error));
  const task=el('details','finding');task.append(el('summary','','任务与输入范围'),el('pre','',current.task),el('p','muted',`原始目录：${current.original_candidate}\n冻结 ${Object.keys(current.input_files).length} 个文件；跳过 ${current.skipped.length} 项`),el('pre','',JSON.stringify(current.skipped,null,2)));target.append(task);
  const table=el('table'),head=el('tr');for(const text of ['条件 / 重复','状态','材料交付','改动文件','用量','查看'])head.append(el('th','',text));table.append(head);
  for(const job of current.jobs) {
    const row=el('tr');row.append(el('td','',`${layers[job.condition]} / ${job.repeat}`),el('td','',states[job.status]||job.status),el('td','',job.delivery==='stdin_file_attached'?'已关联标准输入文件':job.delivery==='not_started'?'待启动':'准备中'),el('td','',job.changed_files===undefined?'—':String(job.changed_files)),el('td','',job.usage?JSON.stringify(job.usage):'—'));
    const cell=el('td');cell.append(action('查看材料',()=>{jobId=job.id;artifactName='prompt.md';renderArtifact();}));row.append(cell);table.append(row);
  }
  const wrap=el('div','table-wrap');wrap.append(table);target.append(wrap);
  target.append(el('div','experiment-artifacts'));if(!current.jobs.some(j=>j.id===jobId))jobId=current.jobs[0].id;renderArtifact();
}
async function renderArtifact() {
  const target=$('.experiment-artifacts');target.replaceChildren();const job=current.jobs.find(j=>j.id===jobId);if(!job)return;
  target.append(el('h3','',`${layers[job.condition]} · 第 ${job.repeat} 次 · ${job.id}`));
  const tabs=el('div','detail-actions');
  for(const [name,label] of [['prompt.md','实际提示词'],['report.md','附加报告'],['answer.md','最终回答'],['events.jsonl','执行轨迹'],['stderr.log','错误日志'],['changes.json','文件改动'],['result.json','运行记录']]) {
    tabs.append(action(label,()=>{artifactName=name;renderArtifact();},artifactName===name?'primary':'quiet'));
  }
  target.append(tabs);const pre=el('pre','experiment-log','正在读取…');target.append(pre);
  const experiment=selected,jobKey=jobId,name=artifactName;
  try {
    const data=await api(endpoint(experiment)+'/artifact?'+new URLSearchParams({job:jobKey,name}));
    if(experiment!==selected||jobKey!==jobId||name!==artifactName||!pre.isConnected)return;
    pre.textContent=(data.truncated?'显示末尾 100000 字节；完整文件保存在实验目录。\n\n':'')+(data.exists?(data.text||'此条件没有附加报告。'):'尚未生成该材料。');
  }catch(e){error(e);}
}
$('#new-experiment').addEventListener('click',()=>{$('#case-search').focus();$('#case-search').scrollIntoView({block:'center'});});
$('#case-search').addEventListener('input',()=>{if(catalog)renderCases();});
$('#repeats').addEventListener('input',updateRun);
document.querySelectorAll('[name=condition]').forEach(n=>n.addEventListener('change',updateRun));
$('#run-selected').addEventListener('click',()=>runSelected().catch(error));
window.addEventListener('hashchange',()=>load().catch(error));
refreshList().then(load).catch(error);
loadCatalog().catch(e=>{$('#case-list').replaceChildren(el('p','error-block',e.message));error(e);});
setInterval(()=>{if(!document.hidden){refreshList().catch(error);if(current?.status==='running')load().catch(error);}},2000);
