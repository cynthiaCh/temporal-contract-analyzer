'use strict';
const $ = selector => document.querySelector(selector);
const labels = {parsed:'范围内解析完成', partial:'部分解析', failed:'扫描失败', empty:'没有源码'};
const origins = {vscode:'VS Code', codex:'Codex', cli:'CLI', web:'浏览页面'};
const decisions = {confirmed:'核查成立', dismissed:'核查不成立', uncertain:'尚不确定'};
let items = [], offset = 0, total = 0, selected, current, tab = 'findings', detailRequest = 0, listRequest = 0;
const pageSize = 30;

function element(tag, className, text) {
  const node = document.createElement(tag);
  if (className) node.className = className;
  if (text !== undefined) node.textContent = text;
  return node;
}
function button(text, action, className = 'quiet') {
  const node = element('button', className, text);
  node.type = 'button';
  node.addEventListener('click', () => Promise.resolve().then(action).catch(showError));
  return node;
}
function showError(error) { $('#notice').textContent = error.message || String(error); $('#notice').classList.remove('hidden'); }
function clearError() { $('#notice').classList.add('hidden'); }
async function api(url, data) {
  const options = data === undefined ? {} : {method:'POST', headers:{'Content-Type':'application/json','X-TCA-Request':'local'}, body:JSON.stringify(data)};
  const response = await fetch(url, options);
  const result = await response.json();
  if (!response.ok) throw new Error(result.error || `请求失败：${response.status}`);
  return result;
}
function date(value) { return new Date(value).toLocaleString('zh-CN', {hour12:false}); }
function badge(status) { return element('span', 'pill '+status, labels[status] || status); }
function reportURL(id) { return '/api/reports/' + encodeURIComponent(id); }
function artifactLink(id, name, label) {
  const link = element('a', 'link-button', label);
  link.href = reportURL(id)+'/artifact?name='+encodeURIComponent(name);
  link.target = '_blank'; link.rel = 'noopener';
  return link;
}

async function loadReports() {
  const ticket = ++listRequest;
  const query = new URLSearchParams({search:$('#search').value, status:$('#status').value, origin:$('#origin').value, limit:pageSize, offset});
  const result = await api('/api/reports?'+query);
  if (ticket !== listRequest) return;
  items = result.items; total = result.total;
  $('#total').textContent = `${total} 份`;
  $('#page-label').textContent = total ? `${offset+1}–${Math.min(offset+pageSize,total)} / ${total}` : '0 份';
  $('#previous').disabled = offset === 0;
  $('#next').disabled = offset+pageSize >= total;
  const list = $('#report-list'); list.replaceChildren();
  for (const meta of items) {
    const row = element('a', 'report-row'+(meta.report_id === selected ? ' selected' : ''));
    row.href = '#report='+meta.report_id;
    row.append(element('div', 'row-title', meta.label || meta.project));
    row.append(element('div', 'row-subtitle', `${meta.project} · ${meta.scope.mode === 'file' ? meta.scope.path : '整个目录'}`));
    const bottom = element('div', 'row-bottom'); bottom.append(badge(meta.status), element('span', '', origins[meta.origin] || meta.origin)); row.append(bottom);
    row.append(element('div', 'row-subtitle', date(meta.created_at)));
    list.append(row);
  }
  if (!items.length) list.append(element('p','muted', '没有符合条件的报告。可新建扫描，或清除筛选条件。'));
  if (result.invalid.length) showError(new Error(`${result.invalid.length} 条归档元数据无法读取；请检查报告库。`));
}

async function openReport(id) {
  const ticket = ++detailRequest;
  selected = id;
  $('#detail').replaceChildren(element('p', 'loading', '正在读取归档并校验内容…'));
  for (const row of document.querySelectorAll('.report-row')) row.classList.toggle('selected', row.hash === '#report='+id);
  try {
    const value = await api(reportURL(id));
    if (ticket !== detailRequest) return;
    current = value; tab = 'findings'; render();
  } catch (error) {
    if (ticket === detailRequest) $('#detail').replaceChildren(element('div','error-block', '无法读取报告：'+error.message));
  }
}

function openScan(meta) {
  const form = $('#scan-form'); form.reset();
  form.elements.parent_report_id.value = '';
  $('#scan-error').textContent = ''; $('#scan-parent').textContent = '';
  if (meta) {
    form.elements.candidate.value = meta.candidate_root + (meta.scope.mode === 'file' ? '/'+meta.scope.path : '');
    form.elements.project.value = meta.project;
    form.elements.task_id.value = meta.task_id;
    form.elements.parent_report_id.value = meta.report_id;
    $('#scan-parent').textContent = '将关联到当前报告；新扫描读取当前磁盘内容。';
  }
  $('#scan-dialog').showModal(); form.elements.candidate.focus();
}

function render() {
  const {metadata:meta, report} = current;
  const detail = $('#detail'); detail.replaceChildren();
  const header = element('div', 'detail-header');
  header.append(element('span','eyebrow', 'ARCHIVED ANALYSIS'));
  const title = element('div','detail-title'); title.append(element('h2','',meta.label || meta.project), badge(meta.status)); header.append(title);
  const info = element('div','detail-meta');
  for (const value of [date(meta.created_at), origins[meta.origin] || meta.origin, meta.input_kind === 'editor_snapshot' ? '含编辑器快照' : '磁盘源码', 'v'+meta.tool_version]) info.append(element('span','',value));
  header.append(info, element('code','',meta.report_id), element('p','detail-path',meta.candidate_root+(meta.scope.mode === 'file' ? '/'+meta.scope.path : '')));
  const actions = element('div','detail-actions');
  actions.append(button('以此为基线扫描',()=>openScan(meta)));
  actions.append(button('复制报告 ID',async()=>{await navigator.clipboard.writeText(meta.report_id);}));
  if (report) actions.append(artifactLink(meta.report_id,'report.html','完整报告 ↗'),artifactLink(meta.report_id,'report.json','JSON ↗'));
  actions.append(artifactLink(meta.report_id,'snapshot.json','输入快照 ↗'));
  header.append(actions); detail.append(header);
  if (!report) {
    detail.append(element('div','summary-strip','本次扫描未产生分析结果；失败信息已归档。'),element('div','error-block',meta.error || '未知错误'));
  } else {
    const strip = element('div','summary-strip');
    for (const [number, label] of [[report.summary.review_hints,'条待核查'],[`${report.summary.parsed_files}/${report.summary.files}`,'文件解析完成'],[report.summary.events,'个语法事件']]) {
      const metric = element('div','metric'); metric.append(element('strong','',number),element('span','',label)); strip.append(metric);
    }
    detail.append(strip,element('p','scope-notice', '这里展示归档时的源码和结果。提示是审查线索；没有命中不代表安全。'+(report.files.some(f=>f.language==='vue') ? ' Vue 当前仅分析脚本语法，未建模模板与框架调度。' : '')));
  }
  const tabs = element('div','tabs'); tabs.setAttribute('role','tablist');
  for (const [key, label] of [['findings','证据与核查'],['source','源码快照'],['compare','前后对比'],['provenance','归档信息'],['delivery','Agent 交付']]) {
    const node = button(label,()=>{tab=key;render();},'tab'+(tab===key?' active':''));
    node.setAttribute('role','tab'); node.setAttribute('aria-selected',String(tab===key)); tabs.append(node);
  }
  detail.append(tabs);
  const content = element('div','tab-content'); content.id = 'tab-content'; detail.append(content);
  if (tab==='findings') renderFindings(content);
  if (tab==='source') renderSource(content);
  if (tab==='provenance') renderProvenance(content);
  if (tab==='delivery') renderDeliveries(content);
  if (tab==='compare') renderComparison(content).catch(showError);
}

function renderFindings(content) {
  const {report, metadata:meta, notes} = current;
  if (!report) { content.append(element('p','muted','扫描失败，没有可核查的规则提示。')); return; }
  const events = new Map(report.files.flatMap(file=>file.events.map(event=>[event.id,event])));
  for (const file of report.files.filter(f=>f.status!=='parsed')) content.append(element('p','error-block', `${file.path} · ${file.error?.message || file.status}`));
  for (const finding of report.findings) {
    const card = element('article','finding');
    const head = element('div','finding-head'); head.append(element('code','',finding.rule),element('span','',finding.id));
    card.append(head, element('h3','',finding.message));
    for (const [label, value] of [['成立条件',finding.condition],['核查问题',finding.review_question]]) {
      const text = element('p'); text.append(element('span','',label+'：'),document.createTextNode(value)); card.append(text);
    }
    const evidence = element('div','evidence');
    for (const id of finding.evidence) {
      const event = events.get(id); if (!event) continue;
      evidence.append(button(`${event.path}:${event.line} · ${event.kind}`,()=>{tab='source';render();loadSource(event.path,event.line,event.end_line).catch(showError);},'source-link'),element('pre','',event.text));
    }
    card.append(evidence);
    const review = element('details','review-box'); review.append(element('summary','','人工核查记录'));
    const ownNotes = notes.filter(n=>n.finding_id===finding.id);
    if (ownNotes.length) review.open = true;
    for (const note of ownNotes) review.append(element('div','annotation', `${decisions[note.decision]} · ${date(note.created_at)}\n${note.note}`));
    const form = element('form','note-form');
    const decision = element('select'); decision.setAttribute('aria-label','核查判断');
    for (const [value,label] of Object.entries(decisions)) { const option=element('option','',label);option.value=value;decision.append(option); }
    decision.value='uncertain';
    const note = element('textarea');note.placeholder='记录依据、测试或尚缺的信息。原始报告保持不变。';note.maxLength=10000;note.setAttribute('aria-label','核查依据');
    const save=element('button','quiet','追加核查记录');save.type='submit';
    form.append(decision,note,save);
    form.addEventListener('submit',async event=>{
      event.preventDefault();save.disabled=true;
      try { const saved=await api(reportURL(meta.report_id)+'/notes',{finding_id:finding.id,decision:decision.value,note:note.value}); if(current.metadata.report_id===meta.report_id){current.notes.push(saved);render();} }
      catch(error){showError(error);save.disabled=false;}
    });
    review.append(form);card.append(review);content.append(card);
  }
  if (!report.findings.length) content.append(element('p','muted', '当前规则没有产生提示。请结合解析覆盖、未建模行为和项目测试继续核查。'));
}

function renderSource(content) {
  const files = current.report?.files || [];
  if (!files.length) { content.append(element('p','muted','这条记录没有捕获到源码。'));return; }
  const toolbar=element('div','source-toolbar');const select=element('select');select.id='source-select';select.setAttribute('aria-label','归档源码文件');
  for(const file of files){const option=element('option','',file.path);option.value=file.path;select.append(option);}
  select.addEventListener('change',()=>loadSource(select.value).catch(showError));
  toolbar.append(select,element('span','muted','归档快照'));content.append(toolbar,element('div','code-view'));content.querySelector('.code-view').id='source-code';
  loadSource(select.value).catch(showError);
}
let sourceRequest=0;
async function loadSource(name,start,end) {
  const id=current.metadata.report_id,ticket=++sourceRequest;
  const value=await api(reportURL(id)+'/source?path='+encodeURIComponent(name));
  if(ticket!==sourceRequest || tab!=='source' || current.metadata.report_id!==id)return;
  $('#source-select').value=name;
  const code=$('#source-code');code.replaceChildren();
  value.text.split(/\r\n|\n|\r/).forEach((text,index)=>{
    const row=element('div','code-line'+(start&&index+1>=start&&index+1<=(end||start)?' highlight':''));
    row.append(element('span','line-number',index+1),element('span','code-text',text || ' '));code.append(row);
  });
  code.querySelector('.highlight')?.scrollIntoView({block:'nearest'});
}

function renderProvenance(content) {
  const {metadata:meta,report}=current;
  const list=element('dl','provenance');
  const values={'报告 ID':meta.report_id,'项目':meta.project,'任务 ID':meta.task_id || '未指定','基线报告':meta.parent_report_id || '未关联','扫描范围':meta.scope.mode==='file'?meta.scope.path:'整个目录','输入类型':meta.input_kind,'未保存内容':meta.overlays.join(', ') || '无','输入摘要':meta.input_sha256 || '未产生','工具摘要':meta.tool_sha256 || '未产生','工具版本':meta.tool_version,'可用实验层':meta.layers.join(', ') || '无（解析未完整）'};
  for(const [label,value] of Object.entries(values)){list.append(element('dt','',label),element('dd','',value));}
  content.append(list,element('p','integrity','读取时已核验归档字节和输入绑定。这不证明分析结论正确，也不是防篡改签名。'));
  content.append(button('重新校验归档',async()=>{await api(reportURL(meta.report_id)+'/verify',{});showError(new Error('归档校验通过；分析语义未验证。'));}));
  if(report){
    const table=element('table');const head=element('tr');for(const label of ['文件','解析状态','范围 / 错误'])head.append(element('th','',label));table.append(head);
    for(const file of report.files){const row=element('tr');for(const value of [file.path,file.status,file.error?.message||file.analysis_scope||''])row.append(element('td','',value));table.append(row);}
    const wrap=element('div','table-wrap');wrap.append(table);content.append(element('h3','','文件覆盖'),wrap);
    for(const limit of report.limitations)content.append(element('p','muted',limit));
    if(report.skipped.length){content.append(element('h3','','跳过的文件与目录'));for(const item of report.skipped)content.append(element('p','muted',`${item.path} · ${item.reason}`));}
  }
}

function renderDeliveries(content) {
  content.append(element('p','scope-notice','交付记录保存 MCP 准备返回的确切内容及传输状态。“已写入传输”不证明客户端收到、模型阅读或采用了材料。手工复制和普通 CLI 读取不会被自动记作 Agent 交付。'));
  const prepared=current.deliveries.filter(d=>d.state==='prepared_for_tool_response');
  if(!prepared.length){content.append(element('p','muted','暂无可观测的 Agent 报告交付记录。'));return;}
  for(const record of prepared){
    const written=current.deliveries.some(d=>d.delivery_id===record.delivery_id&&d.state==='transport_written');
    const card=element('details','finding');card.append(element('summary','',`${date(record.created_at)} · ${record.payload.material} · ${written?'已写入传输':'已准备，传输未确认'}`));
    card.append(element('p','muted',`客户端：${record.client?.name||'未知'} · 字符范围：${record.payload.offset}–${record.payload.offset+record.payload.text.length}`),element('code','',record.payload.response_text_sha256),element('pre','',record.payload.text));content.append(card);
  }
}

async function renderComparison(content) {
  const meta=current.metadata;
  const previous=await api('/api/reports?'+new URLSearchParams({project:meta.project_id,limit:500}));
  if(current.metadata.report_id!==meta.report_id||tab!=='compare')return;
  const matches=previous.items.filter(m=>m.report_id!==meta.report_id&&m.scope.mode===meta.scope.mode&&m.scope.path===meta.scope.path);
  const box=element('div','comparison');box.append(element('p','muted','比较同一项目和扫描范围的历史结果。工具或解析环境不一致时，不计算提示增减。'));
  if(!matches.length){box.append(element('p','muted','还没有可比较的同范围报告。使用“以此为基线扫描”生成下一条记录。'));content.append(box);return;}
  const controls=element('div','comparison-controls');const select=element('select');select.setAttribute('aria-label','对比基线报告');
  for(const item of matches){const option=element('option','',`${date(item.created_at)} · ${item.label||item.project} · ${item.report_id.slice(-12)}`);option.value=item.report_id;select.append(option);}
  if(matches.some(m=>m.report_id===meta.parent_report_id))select.value=meta.parent_report_id;
  const output=element('div');
  controls.append(select,button('与当前报告对比',async()=>{
    const delta=await api('/api/compare?'+new URLSearchParams({before:select.value,after:meta.report_id}));
    output.replaceChildren(element('p','scope-notice',delta.interpretation));
    if(!delta.comparable){output.append(element('p','error-block','两份报告不具备可比的完整分析条件，未计算提示变化。'));return;}
    for(const [label,values] of [['新增提示',delta.added_hints.map(f=>`${f.path} · ${f.rule}`)],['消失提示',delta.removed_hints.map(f=>`${f.path} · ${f.rule}`)],['变化文件',delta.changed_files]]){
      output.append(element('h3','',`${label} · ${values.length}`));const list=element('ul');for(const value of values)list.append(element('li','',value));output.append(list);
    }
  }));box.append(controls,output);content.append(box);
}

$('#new-scan').addEventListener('click',()=>openScan());
$('#close-scan').addEventListener('click',()=>$('#scan-dialog').close());
$('#scan-form').addEventListener('submit',async event=>{
  event.preventDefault();const submit=$('#scan-submit');submit.disabled=true;submit.textContent='正在扫描并归档…';$('#scan-error').textContent='';
  const data=Object.fromEntries(new FormData(event.target));for(const key of Object.keys(data))if(!data[key])delete data[key];
  try{const result=await api('/api/scans',data);$('#scan-dialog').close();$('#search').value='';$('#status').value='';$('#origin').value='';offset=0;await loadReports();location.hash='report='+result.report_id;}
  catch(error){$('#scan-error').textContent=error.message;}
  finally{submit.disabled=false;submit.textContent='扫描并归档';}
});
$('#refresh').addEventListener('click',()=>{clearError();loadReports().catch(showError);if(selected)openReport(selected);});
let searchTimer;
for(const id of ['search','status','origin'])$('#'+id).addEventListener(id==='search'?'input':'change',()=>{clearTimeout(searchTimer);offset=0;searchTimer=setTimeout(()=>loadReports().catch(showError),200);});
$('#previous').addEventListener('click',()=>{offset=Math.max(0,offset-pageSize);loadReports().catch(showError);});
$('#next').addEventListener('click',()=>{offset+=pageSize;loadReports().catch(showError);});
function route(){const id=new URLSearchParams(location.hash.slice(1)).get('report');if(id)openReport(id);}
window.addEventListener('hashchange',route);
api('/api/state').then(state=>{$('#store-path').textContent=state.store;$('#version').textContent='Analyzer '+state.version;}).catch(showError);
loadReports().then(route).catch(showError);
setInterval(()=>{if(!document.hidden)loadReports().catch(()=>{});},10000);
