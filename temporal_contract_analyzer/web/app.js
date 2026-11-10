'use strict';
const $ = selector => document.querySelector(selector);
const labels = {parsed:'范围内解析完成', partial:'部分解析', failed:'扫描失败', empty:'没有源码'};
const origins = {vscode:'VS Code', codex:'Codex', cli:'CLI', web:'浏览页面'};
const decisions = {confirmed:'核查成立', dismissed:'核查不成立', uncertain:'待确认'};
let items = [], offset = 0, total = 0, selected, current, tab = 'findings', detailRequest = 0, listRequest = 0;
const protections = {sufficient:'保护充分', insufficient:'保护不足', uncertain:'待确认'};
let reviewPaths = null;
let contextFinding = '';
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
  if (selected !== id) { reviewPaths = null; contextFinding = ''; }
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
  for (const [key, label] of [['findings','边界审查卡'],['context','源码上下文'],['source','源码快照'],['compare','前后对比'],['provenance','归档信息'],['delivery','Agent 交付']]) {
    const node = button(label,()=>{tab=key;render();},'tab'+(tab===key?' active':''));
    node.setAttribute('role','tab'); node.setAttribute('aria-selected',String(tab===key)); tabs.append(node);
  }
  detail.append(tabs);
  const content = element('div','tab-content'); content.id = 'tab-content'; detail.append(content);
  if (tab==='findings') renderFindings(content);
  if (tab==='context') renderContext(content);
  if (tab==='source') renderSource(content);
  if (tab==='provenance') renderProvenance(content);
  if (tab==='delivery') renderDeliveries(content);
  if (tab==='compare') renderComparison(content).catch(showError);
}

function renderContext(content) {
  const {report, metadata:meta} = current;
  content.append(element('h3','','分析线索 → 定义补全 → Agent 核查'),
    element('p','scope-notice','仅补充归档快照中可识别的定义，列出来源与未解析项。不会调用模型，不代表完整依赖或已确认缺陷。'));
  if (!report) { content.append(element('p','muted','本报告没有可用的分析结果。')); return; }
  const form=element('form','note-form context-controls');
  const select=element('select'); select.setAttribute('aria-label','选择分析线索');
  const all=element('option','','全部线索'); all.value=''; select.append(all);
  for (const finding of report.findings) {
    const option=element('option','',`${finding.id} · ${finding.rule}`); option.value=finding.id; select.append(option);
  }
  select.value=contextFinding;
  const depth=element('select'); depth.setAttribute('aria-label','定义展开深度');
  for(let n=0;n<=5;n++){const option=element('option','',`展开 ${n} 层定义`);option.value=String(n);depth.append(option);} depth.value='1';
  const budget=element('input');budget.type='number';budget.min='1';budget.max='100000';budget.value='12000';budget.setAttribute('aria-label','代码字符预算');
  const aliases=element('textarea');aliases.value='{}';aliases.rows=2;aliases.setAttribute('aria-label','路径别名 JSON');
  for(const [label,field] of [['选择线索',select],['展开深度',depth],['代码字符预算（不含说明文字）',budget]]) {
    const wrapper=element('label','field');wrapper.append(element('span','',label),field);form.append(wrapper);
  }
  const advanced=element('details','context-aliases');advanced.append(element('summary','','路径别名（可选）'));
  const aliasField=element('label','field');aliasField.append(element('span','','例如 {"@":"src"}'),aliases);advanced.append(aliasField);form.append(advanced);
  const submit=element('button','primary','生成源码上下文');submit.type='submit';form.append(submit);
  const result=element('div');content.append(form,result);
  let request=0;
  async function load() {
    const ticket=++request;
    contextFinding=select.value;
    const mapping=JSON.parse(aliases.value);
    const query=new URLSearchParams({depth:depth.value,max_chars:budget.value,aliases:JSON.stringify(mapping)});
    if(select.value)query.set('finding_id',select.value);
    submit.disabled=true;result.replaceChildren(element('p','muted','正在从归档源码补充定义…'));
    try {
      const data=await api(reportURL(meta.report_id)+'/context?'+query);
      if(ticket!==request || !content.isConnected)return;
      const packet=data.context;
      result.replaceChildren(element('p','muted',`${packet.usage.snippets} 段源码 · ${packet.usage.code_chars} 字符 · ${packet.unresolved.length} 项未解析`),
        button('复制完整上下文给 Agent',async()=>navigator.clipboard.writeText(data.markdown)));
      if(!packet.snippets.length)result.append(element('p','muted','没有选中的线索；没有命中不代表安全。'));
      for(const snippet of packet.snippets) {
        const card=element('article','finding');
        card.append(element('h3','',`${snippet.file}:${snippet.start_line}–${snippet.end_line} · ${snippet.kind==='seed'?'原始证据':'补充定义'}`));
        const descriptions=snippet.reasons.map(reason=>reason.kind==='finding-evidence'
          ? `分析线索 ${reason.finding_id} 的源码证据`
          : `${reason.from_file}:${reason.reference_line} 使用 ${reason.local_name || reason.symbol}${reason.module?'，来自 '+reason.module:''}`);
        for(const description of new Set(descriptions))card.append(element('p','muted',description));
        card.append(element('pre','',snippet.code),button('查看归档源码',()=>{tab='source';render();loadSource(snippet.file,snippet.start_line,snippet.end_line).catch(showError);},'source-link'));
        result.append(card);
      }
      const gaps=element('article','finding');gaps.append(element('h3','','未解析项'));
      if(!packet.unresolved.length)gaps.append(element('p','muted','未记录到可识别的解析缺口；结果仍受支持范围限制。'));
      for(const gap of packet.unresolved)gaps.append(element('p','annotation',`${gap.from_file || ''}${gap.reference_line?':'+gap.reference_line:''} · ${gap.symbol || ''} · ${gap.reason}${gap.target_file?' → '+gap.target_file:''}${gap.detail?' · '+gap.detail:''}`));
      result.append(gaps);
      const limits=element('article','finding');limits.append(element('h3','','支持范围'));
      for(const limitation of packet.limitations)limits.append(element('p','muted',limitation));result.append(limits);
    } catch(error) {
      if(ticket===request && content.isConnected)result.replaceChildren(element('div','error-block',error.message));
    } finally {if(ticket===request)submit.disabled=false;}
  }
  form.addEventListener('submit',event=>{event.preventDefault();load().catch(showError);});
  load().catch(showError);
}

function reviewScope(report, paths) {
  if (paths === null) return null;
  // File-level approximation of only the analyzer's candidate direct links.
  const events = new Map(report.files.flatMap(file=>file.events.map(event=>[event.id,event])));
  const functions = new Map(report.files.flatMap(file=>(file.functions || []).map(fn=>[fn.id,file.path])));
  const related = new Set(paths);
  let changed = true;
  while (changed) {
    changed = false;
    for (const link of report.call_links) {
      const caller = events.get(link.call)?.path, target = functions.get(link.target);
      if (caller && target && (related.has(caller) || related.has(target))) {
        for (const path of [caller,target]) if (!related.has(path)) { related.add(path); changed=true; }
      }
    }
  }
  return related;
}

function boundaryPacket(card, events, meta, note) {
  const refs = card.evidence_ids.map(id=>events.get(id)).filter(Boolean).map(e=>`${e.path}:${e.line}`).join('、');
  const review = note?.boundary_review;
  return [`此候选位置可能跨越执行边界：${card.title}`,
    `执行边界：${card.boundary.evidence_ids.map(id=>events.get(id)).filter(Boolean).map(e=>`${e.path}:${e.line} · ${e.kind}`).join('、')}`,
    `可能变化：${card.possible_changes.summary}`,
    `影响效果：${card.effects.summary}${card.effects.evidence_ids.map(id=>events.get(id)).filter(Boolean).map(e=>`${e.path}:${e.line} · ${e.text.trim()}`).join('、')}`,
    `请核查：${card.requirement_protection.summary}`,
    `成立条件：${card.condition}`,
    `人工关系判断：${note ? decisions[note.decision] : '待确认'}；保护：${review ? protections[review.protection] : '待确认'}。`,
    ...(review?.requirement_basis ? [`仓库要求与保护依据（人工记录）：${review.requirement_basis}`] : []),
    ...(note?.note ? [`关系判断依据（人工记录）：${note.note}`] : []),
    `尚缺证据：${review?.missing_evidence || '请继续核查调用可达性、工作归属与保护范围。'}`,
    `证据：${refs}。归档报告：${meta.report_id}；finding：${card.finding_id}；输入摘要：${meta.input_sha256}。`,
    '请先核对当前源码与归档快照。此卡为审查线索，人工确认不等于 oracle 判定。'].join('\n');
}

function renderFindings(content) {
  const {report, metadata:meta, notes, boundary_cards:cards=[]} = current;
  if (!report) { content.append(element('p','muted','扫描失败，没有可核查的规则提示。')); return; }
  const events = new Map(report.files.flatMap(file=>file.events.map(event=>[event.id,event])));
  content.append(element('p','scope-notice','先定位边界，再判断关系是否成立、保护是否充分、还缺什么证据。仓库要求尚未找到时保持待确认；可从源码上下文补充核查依据。'));
  const scope = element('div','card-scope');
  const paths = element('input'); paths.value=(reviewPaths || []).join(', '); paths.placeholder='相对文件路径，多个路径用逗号分隔'; paths.setAttribute('aria-label','本次改动文件');
  const applyPaths = ()=>{reviewPaths=paths.value.trim() ? paths.value.split(',').map(p=>p.trim()).filter(Boolean) : null;render();};
  paths.addEventListener('keydown',event=>{if(event.key==='Enter')applyPaths();});
  scope.append(paths,button('查看改动及相关调用候选',applyPaths),button('查看全部卡片',()=>{reviewPaths=null;render();}));
  if (meta.parent_report_id) scope.append(button('使用基线间变化文件',async()=>{
    const id=meta.report_id;
    const compared=await api('/api/compare?'+new URLSearchParams({before:meta.parent_report_id,after:id}));
    if(current.metadata.report_id!==id)return;
    reviewPaths=compared.changed_files;render();
  }));
  content.append(scope);
  const related=reviewScope(report,reviewPaths);
  const shown=cards.filter(card=>!related || card.evidence_ids.some(id=>related.has(events.get(id)?.path)));
  const captured=new Set(report.files.map(file=>file.path));
  const missing=(reviewPaths || []).filter(path=>!captured.has(path));
  content.append(element('p','scope-notice',`显示 ${shown.length}/${cards.length} 张候选卡。${related ? '筛选文件：'+reviewPaths.join('、')+'；关联文件：'+[...related].join('、')+'。仅按文件及候选直接调用关系扩展。' : '当前显示本次扫描的全部候选卡。'}${missing.length ? '指定路径未被当前源码快照捕获：'+missing.join('、')+'。' : ''}动态派发、回调目标、框架调度及扫描范围外的路径未完整覆盖；隐藏卡片和无命中路径仍需核查。`));
  const coverage=element('details','review-box');coverage.append(element('summary','','查看扫描范围与未覆盖内容'));
  for(const limitation of report.limitations)coverage.append(element('p','muted',limitation));
  for(const file of report.files.filter(f=>f.status!=='parsed'))coverage.append(element('p','error-block',`${file.path} · ${file.error?.message || file.status}`));
  for(const file of report.skipped)coverage.append(element('p','muted',`${file.path} · ${file.reason}`));
  content.append(coverage);
  function sourceButton(id) {
    const event=events.get(id);
    return button(`${event.path}:${event.line} · ${event.kind}`,()=>{tab='source';render();loadSource(event.path,event.line,event.end_line).catch(showError);},'source-link');
  }
  for (const candidate of shown) {
    const card = element('article','finding boundary-card');
    const ownNotes=notes.filter(n=>n.finding_id===candidate.finding_id), latest=ownNotes.at(-1);
    const head=element('div','finding-head');head.append(element('code','',candidate.rule),element('span','',candidate.finding_id),element('span','pill',latest ? decisions[latest.decision] : '待确认'));
    card.append(head,element('h3','',candidate.title));
    const questions=element('dl','boundary-questions');
    for (const [label,value] of [['执行边界在哪里？',candidate.boundary],['什么可能已经变化？',candidate.possible_changes],['影响什么效果？',candidate.effects],['仓库要求与保护是什么？',candidate.requirement_protection]]) {
      const answer=element('dd');answer.append(element('p','',value.summary));
      for(const id of value.evidence_ids || [])answer.append(sourceButton(id));
      if(label==='仓库要求与保护是什么？')answer.append(element('p','muted',latest?.boundary_review?.requirement_basis || '仓库依据待补充；判断或取消调用的存在不代表充分。'));
      questions.append(element('dt','',label),answer);
    }
    card.append(questions);
    const evidence=element('details','evidence');evidence.append(element('summary','','源码引用与成立条件'));
    evidence.append(element('p','muted',candidate.condition));
    for(const id of candidate.evidence_ids){evidence.append(sourceButton(id),element('pre','',events.get(id).text));}
    card.append(evidence);
    const actions=element('div','detail-actions');
    actions.append(button('补充相关源码',()=>{contextFinding=candidate.finding_id;tab='context';render();}));
    actions.append(button('复制给 Agent 的核查材料',async()=>{await navigator.clipboard.writeText(boundaryPacket(candidate,events,meta,latest));}));
    card.append(actions);
    const review=element('details','review-box');review.append(element('summary','','人工核查记录'));
    if(ownNotes.length)review.open=true;
    for(const note of ownNotes){
      const structured=note.boundary_review;
      review.append(element('div','annotation',`${decisions[note.decision]} · ${date(note.created_at)}\n${note.note}`+(structured ? `\n保护：${protections[structured.protection]}\n仓库要求与保护依据：${structured.requirement_basis || '待补充'}\n尚缺证据：${structured.missing_evidence || '未记录'}` : '')));
    }
    const form=element('form','note-form');
    function field(label,node){const wrapper=element('label','review-field');wrapper.append(element('span','',label),node);form.append(wrapper);return node;}
    const decision=element('select');decision.setAttribute('aria-label','关系是否成立');
    for(const [value,label] of Object.entries(decisions)){const option=element('option','',label);option.value=value;decision.append(option);}
    decision.value=latest?.decision || 'uncertain';field('这条关系是否成立？',decision);
    const note=element('textarea');note.placeholder='记录关系判断的源码或测试依据。';note.maxLength=10000;note.setAttribute('aria-label','关系判断依据');field('判断依据',note);
    const protection=element('select');protection.setAttribute('aria-label','现有保护是否充分');
    for(const [value,label] of Object.entries(protections)){const option=element('option','',label);option.value=value;protection.append(option);}
    protection.value=latest?.boundary_review?.protection || 'uncertain';field('现有保护是否充分？',protection);
    const basis=element('textarea');basis.maxLength=10000;basis.value=latest?.boundary_review?.requirement_basis || '';basis.placeholder='仓库规范、调用处、测试或设计依据的路径/位置；说明保护约束哪些效果。';basis.setAttribute('aria-label','仓库要求与保护依据');field('仓库要求与保护依据',basis);
    const missingEvidence=element('textarea');missingEvidence.maxLength=10000;missingEvidence.placeholder='例如：待完成通知与关闭后通知是否都受约束？缺少哪条调用路径或行为轨迹？';missingEvidence.setAttribute('aria-label','尚缺什么证据');field('还缺什么证据？',missingEvidence);
    const save=element('button','quiet','追加核查记录');save.type='submit';form.append(save);
    form.addEventListener('submit',async event=>{
      event.preventDefault();save.disabled=true;
      try{
        const saved=await api(reportURL(meta.report_id)+'/notes',{finding_id:candidate.finding_id,decision:decision.value,note:note.value,boundary_review:{protection:protection.value,requirement_basis:basis.value,missing_evidence:missingEvidence.value}});
        if(current.metadata.report_id===meta.report_id){current.notes.push(saved);render();}
      }catch(error){showError(error);save.disabled=false;}
    });
    review.append(form);card.append(review);content.append(card);
  }
  if(!shown.length)content.append(element('p','muted','当前范围没有候选卡。请结合解析覆盖、未建模行为和项目测试继续核查。'));
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
