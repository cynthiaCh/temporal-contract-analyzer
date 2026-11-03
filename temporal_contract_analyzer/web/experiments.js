'use strict';
const $ = selector => document.querySelector(selector);
const states = {prepared:'待启动', running:'运行中', completed:'进程完成', failed:'运行失败', cancelled:'已取消', timed_out:'超时', interrupted:'服务中断'};
const layers = {none:'A · 无报告',locations:'B · 位置',facts:'C · 事实',review:'D · 审查',audit:'E · 通用提示',risk:'F · 提示＋信号',audit_review:'G · 提示＋报告',learned_review:'失败经验辅助（开发）'};
let selected, current, jobId, artifactName = 'oracle.json', busy = false, generation = 0;
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
function progress(jobs) {
  const done=jobs.filter(j=>!['prepared','running'].includes(j.status)).length;
  return `${done} / ${jobs.length} 次结束`;
}
function experimentRow(row) {
  const link=el('a','report-row'+(selected===row.id?' selected':''));link.href='#experiment='+row.id;
  link.addEventListener('click',()=>$('#experiments-dialog').close());
  const title=el('div','section-heading');title.append(el('strong','row-title',row.label),el('span','pill',states[row.status]||row.status));
  link.append(title,el('div','row-subtitle',`${row.model==='local-default'?'本地 Codex':row.model} · ${progress(row.jobs)} · ${date(row.created_at)}`));
  const results=row.jobs.filter(j=>j.evaluation?.status==='passed'||j.evaluation?.status==='failed');
  if(results.length)link.append(el('div','row-subtitle',`行为验证：${results.filter(j=>j.evaluation.status==='passed').length} 成功 · ${results.filter(j=>j.evaluation.status==='failed').length} 失败 · ${row.jobs.length-results.length} 尚未验证`));
  return link;
}
function outcome(job) {
  const status=job.evaluation?.status;
  if(status==='passed')return ['成功','parsed'];
  if(status==='failed')return ['失败','failed'];
  if(status==='error')return ['未验证 · 验证异常','partial'];
  if(activeExperiment===selected&&job.status==='completed')return ['验证中',''];
  return ['尚未验证',''];
}
function scenarioLabel(job) {
  const progress=job.evaluation?.scenario_progress;
  if(!progress)return '未提供逐场景结论';
  if(progress.unknown===progress.total)return `未提供逐场景结论（${progress.total} 个场景）`;
  return `${progress.passed}/${progress.total} 个场景通过`;
}
async function refreshList() {
  let data;
  try{data=await api('/api/experiments');}catch(e){
    $('#activity-title').textContent='无法连接本机运行服务';
    $('#activity-detail').textContent='已有进度可能过期；连接恢复后自动更新。';
    $('#activity-progress').replaceChildren();throw e;
  }
  activeExperiment=data.active;updateRun();
  $('#codex-path').textContent=data.codex||'暂未发现本地 Codex';$('#experiment-store').textContent=data.root;
  $('#experiment-count').textContent=data.items.length;const list=$('#experiment-list');list.replaceChildren();
  for(const row of data.items)list.append(experimentRow(row));
  if(!data.items.length)list.append(el('p','muted','还没有实验记录。'));
  const active=data.items.filter(r=>r.status==='running'||r.id===data.active);
  for(const [id,rows,empty] of [['#active-experiments',active,'当前没有正在运行的网页实验。'],['#recent-experiments',data.items.filter(r=>!active.includes(r)).slice(0,10),'暂无已结束的实验记录。']]) {
    const target=$(id);target.replaceChildren();for(const row of rows)target.append(experimentRow(row));
    if(!rows.length)target.append(el('p','muted',empty));
  }
  const running=active[0];
  $('#activity-title').textContent=running?`${states[running.status]} · ${running.label}`:data.active?'服务忙碌 · 正在核对实验状态':'当前没有正在运行的网页实验';
  $('#activity-detail').textContent=running?`${progress(running.jobs)} · ${running.jobs.filter(j=>j.status==='running').length} 运行中 · ${running.jobs.filter(j=>j.status==='prepared').length} 待开始`:'本机服务已连接 · 关闭页面不会停止后台实验';
  const bar=$('#activity-progress');bar.replaceChildren();
  if(running){const meter=el('progress');meter.max=running.jobs.length;meter.value=running.jobs.filter(j=>!['prepared','running'].includes(j.status)).length;meter.setAttribute('aria-label','已结束的实验尝试');bar.append(meter);}
}
function renderCases() {
  const list=$('#case-list');list.replaceChildren();
  const query=$('#case-search').value.trim().toLowerCase();
  const rows=catalog.cases.filter(c=>`${c.id} ${c.title} ${c.language}`.toLowerCase().includes(query));
  $('#case-count').textContent=catalog.cases.length;
  $('#catalog-summary').textContent=`${rows.length} 个案例 · ${catalog.cases.filter(c=>c.supported).length} 个可运行`;
  const table=el('table'),head=el('tr');for(const title of ['案例 / 维护任务','语言','运行状态','操作'])head.append(el('th','',title));
  const thead=el('thead');thead.append(head);table.append(thead);const body=el('tbody');table.append(body);
  for(const item of rows) {
    const row=el('tr'),name=el('td');name.append(el('strong','row-title',item.title),el('div','row-subtitle',item.id));
    const status=el('td');status.append(el('span','pill'+(item.supported?' parsed':''),item.supported?'可运行':'未接入'));
    if(!item.supported)status.append(el('div','row-subtitle',item.unavailable_reason));
    const cell=el('td');const button=action('运行这个案例',()=>{
      selectedCase=item.id;$('#case-title').textContent=item.title;$('#case-description').textContent=item.id;
      $('#run-error').classList.add('hidden');updateRun();$('#case-dialog').showModal();
    });button.disabled=!item.supported;button.setAttribute('aria-label',`运行案例 ${item.id}`);cell.append(button);
    row.append(name,el('td','',item.language||'—'),status,cell);body.append(row);
  }
  if(rows.length){const wrap=el('div','table-wrap');wrap.append(table);list.append(wrap);}else list.append(el('p','muted','没有匹配的案例。'));
}
function updateRun() {
  const count=document.querySelectorAll('[name=condition]:checked').length;
  $('#run-selected').disabled=busy||!!activeExperiment||!selectedCase||!count;
  $('#run-selected').textContent=busy?'正在准备并启动…':activeExperiment?'等待当前实验结束':'开始运行';
  const model=$('#model').value||'本地默认';
  $('#run-summary').textContent=selectedCase?`${model} · ${count} 个报告条件 × ${$('#repeats').value} 次 = ${count*Number($('#repeats').value)} 次运行${activeExperiment?'；当前实验结束后可手动开始。':''}`:'选择案例后运行。';
}
async function loadCatalog() {
  catalog=await api('/api/case-options');
  const select=$('#model');select.replaceChildren();
  const local=el('option','','本地 Codex 默认配置');local.value='';select.append(local);
  for(const [earlier,label] of [[true,'较早版本'],[false,'其他本地可选模型']]) {
    const group=el('optgroup');group.label=label;
    for(const model of catalog.model_choices||[]) {
      if(model.earlier!==earlier)continue;
      const option=el('option','',model.id);option.value=model.id;option.disabled=!model.efforts.length;group.append(option);
    }
    if(group.childElementCount)select.append(group);
  }
  updateEffort();
  renderCases();updateRun();
}
function updateEffort() {
  const choice=catalog?.model_choices?.find(r=>r.id===$('#model').value);
  $('#effort-field').hidden=!choice;
  const select=$('#effort');select.replaceChildren();
  if(choice){for(const value of choice.efforts){const option=el('option','',value);option.value=value;select.append(option);}select.value=choice.efforts.includes('medium')?'medium':choice.default_effort;}
  $('#model-note').textContent=choice?'通过本机 Codex 调用，沿用本地登录与服务配置。':'沿用本地 Codex 的模型配置和登录。';
}
async function runSelected() {
  if(busy||activeExperiment||!selectedCase)return;
  busy=true;updateRun();$('#notice').classList.add('hidden');
  try {
    const data={case_id:selectedCase,
      repeats:Number($('#repeats').value),timeout:Number($('#timeout').value),
      conditions:[...document.querySelectorAll('[name=condition]:checked')].map(n=>n.value)};
    if($('#model').value){data.model=$('#model').value;data.use_local_config=true;data.effort=$('#effort').value;}
    const result=await api('/api/experiments',data);
    location.hash='experiment='+result.id;
    await api(endpoint(result.id)+'/start',{});
    $('#case-dialog').close();
    await load();
  }catch(e){$('#run-error').textContent=e.message;$('#run-error').classList.remove('hidden');error(e);}finally{busy=false;await refreshList();updateRun();}
}
async function load() {
  const ticket=++generation;
  const id=new URLSearchParams(location.hash.slice(1)).get('experiment');
  const history=location.hash==='#runs';
  $('#case-browser').hidden=!!id||history;$('#history-view').hidden=!history;$('#experiment-detail').hidden=!id;
  document.querySelectorAll('[data-view]').forEach(n=>{const active=n.dataset.view===(id||history?'runs':'cases');n.classList.toggle('active',active);if(active)n.setAttribute('aria-current','page');else n.removeAttribute('aria-current');});
  if(!id)return;
  const data=await api(endpoint(id));if(ticket!==generation)return;
  if(selected!==id){jobId=undefined;artifactName='oracle.json';}
  selected=id;current=data;render();await refreshList();
}
function render() {
  const openDetails=[...$('#experiment-detail').querySelectorAll('details[open][data-section]')].map(n=>n.dataset.section);
  const oldLog=$('.experiment-log'),logScroll=oldLog?.scrollTop||0;
  const scenariosOpen=$('[data-section=scenarios]')?.open??true;
  const target=$('#experiment-detail');target.replaceChildren();const header=el('div','detail-header');
  const back=el('a','back-link','← 运行档案');back.href='#runs';header.append(back,el('span','eyebrow','RUN / 实验结果'),el('h2','',current.label));
  const model=current.local_codex&&!current.model_override?'本地 Codex 配置':`${current.model} / ${current.effort}`;
  header.append(el('p','detail-path',`${states[current.status]} · ${model} · ${current.jobs.length} 次运行`));
  const controls=el('div','detail-actions');
  const report=el('a','link-button','打开输入扫描报告');report.href='/#report='+current.report_id;report.target='_blank';report.rel='noopener';controls.append(report);
  if(current.status==='prepared')controls.append(action('启动 Codex 实验',async()=>{
    if(busy)return;busy=true;try{await api(endpoint()+'/start',{});await load();}finally{busy=false;}
  },'primary'));
  if(current.status==='running'||activeExperiment===selected)controls.append(action('取消运行或验证',async()=>{await api(endpoint()+'/cancel',{});await load();}));
  if(current.case&&current.status!=='running'&&current.jobs.some(j=>j.status==='completed'))controls.append(action(current.evaluation_id?'重新验证修改结果':'验证修改结果',async()=>{
    if(busy)return;busy=true;updateRun();
    try{await api(endpoint()+'/evaluate',{});await load();}finally{busy=false;await refreshList();}
  }));
  if(current.evaluation_id&&current.status!=='running'&&current.jobs.some(j=>j.evaluation?.status==='failed'))controls.append(action('从失败提炼经验',async()=>{
    if(busy)return;busy=true;
    try{await api(endpoint()+'/learn',{});await load();}finally{busy=false;}
  }));
  header.append(controls);target.append(header);
  const summary=el('div','summary-strip');
  for(const [label,count] of [['成功',current.jobs.filter(j=>j.evaluation?.status==='passed').length],['失败',current.jobs.filter(j=>j.evaluation?.status==='failed').length],['尚未验证',current.jobs.filter(j=>!['passed','failed'].includes(j.evaluation?.status)).length]]){const metric=el('div','metric');metric.append(el('strong','',String(count)),el('span','',label));summary.append(metric);}target.append(summary);
  target.append(el('p','scope-notice','修改结果按案例行为测试判定。场景通过数展示已验证的执行情形，不等于独立任务数；整体失败仍可能通过部分场景，全部场景通过也不能替代整体判定。'));
  if(current.learning)target.append(el('p','scope-notice','本次含失败经验辅助条件：'+current.learning.qualification+'。冻结经验：'+current.learning.lesson_ids.join('、')));
  if(current.learning_warning)target.append(el('p','error-block','失败经验暂不可用；原实验结果保留。'+current.learning_warning));
  if(current.failure_lessons?.length){
    const lessons=el('section','finding');lessons.append(el('h3','','失败经验 · 候选记忆'),
      el('p','muted','失败已沉淀为候选核查策略；不会自动改写扫描规则。下次在“其他报告条件”勾选“失败经验辅助（开发）”可显式使用。'));
    const names={'effect-separation':'分别核查历史记录与当前显示的有效性条件','boundary-coverage':'补查暂停、重入、清理与后续访问的组合'};
    for(const lesson of current.failure_lessons.slice(0,3)){
      lessons.append(el('p','',lesson.recipes.map(r=>names[r]||r).join('；')),
        el('p','muted',`${lesson.id} · 来源 ${lesson.source.experiment_id} / ${lesson.source.evaluation_id}`),el('p','muted',lesson.qualification));
    }
    target.append(lessons);
  }
  if(current.error)target.append(el('p','error-block',current.error));
  const task=el('details','finding');task.dataset.section='task';task.open=openDetails.includes('task');task.append(el('summary','','任务与输入范围'),el('pre','',current.task),el('p','muted',`原始目录：${current.original_candidate}\n冻结 ${Object.keys(current.input_files).length} 个文件；跳过 ${current.skipped.length} 项`),el('pre','',JSON.stringify(current.skipped,null,2)));target.append(task);
  const table=el('table'),head=el('tr');for(const text of ['条件 / 重复','修改结果','场景通过','运行状态','改动文件','用量','查看'])head.append(el('th','',text));table.append(head);
  for(const job of current.jobs) {
    const row=el('tr'),result=el('td');const [label,style]=outcome(job);result.append(el('span','pill '+style,label));
    if(job.evaluation?.verdict)result.append(el('div','row-subtitle',job.evaluation.verdict));
    if(job.evaluation?.reason)result.append(el('div','row-subtitle',job.evaluation.reason));
    const progress=el('td','scenario-progress',job.evaluation?scenarioLabel(job):'尚未验证');
    const detail=job.evaluation?.scenario_progress;
    if(detail){
      if(detail.failed)progress.append(el('div','row-subtitle',`${detail.failed} 个未通过`));
      if(detail.unknown||detail.error)progress.append(el('div','row-subtitle',`${detail.unknown} 个结论未知 · ${detail.error} 个运行异常`));
    }
    row.append(el('td','',`${layers[job.condition]} / ${job.repeat}`),result,progress,el('td','',states[job.status]||job.status),el('td','',job.changed_files===undefined?'—':String(job.changed_files)),el('td','',job.usage?`输入 ${job.usage.input_tokens??'—'} / 输出 ${job.usage.output_tokens??'—'} tokens`:'—'));
    const cell=el('td');cell.append(action('查看材料',()=>{jobId=job.id;artifactName='oracle.json';renderArtifact();}));row.append(cell);table.append(row);
  }
  const wrap=el('div','table-wrap');wrap.append(table);target.append(wrap);
  target.append(el('div','experiment-artifacts'));if(!current.jobs.some(j=>j.id===jobId))jobId=current.jobs[0]?.id;renderArtifact(logScroll,openDetails.includes('technical'),scenariosOpen);
}
async function renderArtifact(logScroll=0,technicalOpen=$('[data-section=technical]')?.open||false,scenariosOpen=$('[data-section=scenarios]')?.open??true) {
  const target=$('.experiment-artifacts');target.replaceChildren();const job=current.jobs.find(j=>j.id===jobId);if(!job)return;
  target.append(el('h3','',`${layers[job.condition]} · 第 ${job.repeat} 次 · ${job.id}`));
  const progress=job.evaluation?.scenario_progress;
  if(progress){
    const box=el('details','finding');box.dataset.section='scenarios';box.open=scenariosOpen;
    box.append(el('summary','',scenarioLabel(job)));
    const states={passed:'通过',failed:'未通过',error:'运行异常',unknown:'结论未知'};
    for(const item of progress.items){
      const line=el('p','scenario-outcome');line.append(el('span','pill '+(item.status==='passed'?'parsed':item.status==='failed'?'failed':'partial'),states[item.status]),el('code','',item.name));
      const a=item.assertions;
      if(a.total)line.append(el('span','muted',`断言检查 ${a.passed}/${a.total} 通过`));
      box.append(line);
      if(item.failed_assertions.length)box.append(el('p','annotation','未通过断言：'+item.failed_assertions.join('、')));
    }
    target.append(box);
  }
  const tabs=el('div','detail-actions');
  const technical=el('details','technical-artifacts');technical.dataset.section='technical';technical.open=technicalOpen;technical.append(el('summary','','提示词、日志与运行记录'));const extra=el('div','detail-actions');technical.append(extra);
  for(const [name,label] of [['oracle.json','行为验证'],['evaluation.json','验证记录'],['oracle-stderr.log','验证日志'],['prompt.md','实际提示词'],['report.md','附加报告'],['answer.md','最终回答'],['events.jsonl','执行轨迹'],['stderr.log','错误日志'],['changes.json','文件改动'],['result.json','运行记录']]) {
    const button=action(label,()=>{artifactName=name;renderArtifact();},artifactName===name?'primary':'quiet');button.setAttribute('aria-pressed',String(artifactName===name));
    (['oracle.json','answer.md','changes.json'].includes(name)?tabs:extra).append(button);
  }
  target.append(tabs,technical);const pre=el('pre','experiment-log','正在读取…');target.append(pre);
  const experiment=selected,jobKey=jobId,name=artifactName;
  try {
    const data=await api(endpoint(experiment)+'/artifact?'+new URLSearchParams({job:jobKey,name}));
    if(experiment!==selected||jobKey!==jobId||name!==artifactName||!pre.isConnected)return;
    pre.textContent=(data.truncated?'显示末尾 100000 字节；完整文件保存在实验目录。\n\n':'')+(data.exists?(data.text||'此条件没有附加报告。'):'尚未生成该材料。');
    pre.scrollTop=logScroll;
  }catch(e){error(e);}
}
$('#experiments-button').addEventListener('click',()=>$('#experiments-dialog').showModal());
$('#open-activity').addEventListener('click',()=>$('#experiments-dialog').showModal());
$('#close-experiments').addEventListener('click',()=>$('#experiments-dialog').close());
$('#close-case').addEventListener('click',()=>$('#case-dialog').close());
$('#case-search').addEventListener('input',()=>{if(catalog)renderCases();});
$('#repeats').addEventListener('input',updateRun);
$('#model').addEventListener('change',()=>{updateEffort();updateRun();});
document.querySelectorAll('[name=condition]').forEach(n=>n.addEventListener('change',updateRun));
$('#experiment-form').addEventListener('submit',e=>{e.preventDefault();runSelected().catch(error);});
window.addEventListener('hashchange',()=>load().catch(error));
refreshList().then(load).catch(error);
loadCatalog().catch(e=>{$('#case-list').replaceChildren(el('p','error-block',e.message));error(e);});
setInterval(()=>{if(!document.hidden){refreshList().catch(error);const awaiting=current?.case&&!current.evaluation_id&&current.jobs.some(j=>j.status==='completed');if(current?.status==='running'||activeExperiment===selected||awaiting)load().catch(error);}},2000);
