'use strict';
const $ = selector => document.querySelector(selector);
const stageStates = {recorded:'有记录',unknown:'待核实',not_started:'未启动',not_performed:'本批未执行',
  blocked:'材料阻断',frozen:'已冻结版本',rejected:'未接纳'};
let catalog, current, generation=0;
function el(tag, cls, text) {const n=document.createElement(tag);if(cls)n.className=cls;if(text!==undefined)n.textContent=text;return n;}
function notice(error) {$('#notice').textContent=error.message;$('#notice').classList.remove('hidden');}
async function api(path) {const response=await fetch(path);const data=await response.json();if(!response.ok)throw new Error(data.error||'读取失败');return data;}
function batchURL(id,stage='case') {return '#'+new URLSearchParams({batch:id,stage});}
function endpoint(id) {return '/api/development/'+encodeURIComponent(id);}
function button(label, callback, cls='quiet') {const n=el('button',cls,label);n.type='button';n.addEventListener('click',()=>Promise.resolve().then(callback).catch(notice));return n;}
function objectView(label,value) {const box=el('details','development-record');box.append(el('summary','',label),el('pre','development-text',JSON.stringify(value,null,2)));return box;}
function pill(state) {return el('span','pill development-state '+state,stageStates[state]||state);}
function archiveLink(item) {const link=el('a','report-row');link.href=batchURL(item.id);const title=el('div','section-heading');title.append(el('strong','row-title',item.title),el('span','pill',item.reused?'复用冻结经验':item.status?.startsWith('STOP')?'已停止':'历史记录'));link.append(title,el('div','row-subtitle',item.id));if(item.case)link.append(el('p','',item.case));if(item.experience)link.append(el('p','muted','经验版本：'+item.experience));if(item.stop)link.append(el('p','development-stop','停止记录：'+(item.stop.reason||JSON.stringify(item.stop))));return link;}
function renderList() {
  const query=$('#development-search').value.trim().toLowerCase();
  const items=catalog.items.filter(item=>`${item.id} ${item.case||''} ${item.experience||''}`.toLowerCase().includes(query));
  $('#development-count').textContent=`${items.length} 个批次 · 每批单独展示，不合并通过率`;
  const list=$('#development-list');list.replaceChildren();items.forEach(item=>list.append(archiveLink(item)));
  if(!items.length)list.append(el('p','muted',catalog.items.length?'没有匹配的批次。':'此归档目录下尚无受支持的经验开发记录。可读取单案例经验对照与两案例试验的现有归档。'));
  if(catalog.warnings.length)list.append(objectView('无法读取的归档（不当作零结果）',catalog.warnings));
}
async function refresh() {
  const [records,taxonomy]=await Promise.all([api('/api/development'),api('/api/taxonomy')]);
  catalog=records;$('#development-root').textContent=catalog.root;
  const labels=$('#taxonomy-labels');labels.replaceChildren();
  taxonomy.codebook.forEach(row=>{const item=el('details','taxonomy-label');item.append(el('summary','',`${row.code} · ${row.name_zh}`),el('p','',row.family),el('p','muted',row.inclusion_rule));labels.append(item);});
  $('#taxonomy-version').textContent=`版本：${taxonomy.schema_version} · 五组提示模板、五条题库问题分别保留为模板和条目，不作为当前分类。`;
  renderList();await load();
}
async function load() {
  const ticket=++generation,params=new URLSearchParams(location.hash.slice(1)),id=params.get('batch');
  $('#development-browser').hidden=!!id;$('#development-detail').hidden=!id;
  $('#notice').classList.add('hidden');
  if(!id)return;
  $('#development-detail').replaceChildren(el('p','muted','正在读取开发材料…'));
  const data=await api(endpoint(id));if(ticket!==generation)return;current=data;render(params.get('stage')||'case');
}
function render(stageId) {
  const target=$('#development-detail');target.replaceChildren();
  const back=el('a','back-link','← 经验开发归档');back.href='/development';target.append(back);
  const header=el('div','detail-header');header.append(el('span','eyebrow','ARCHIVED DEVELOPMENT / 真实归档'),el('h1','',current.title),el('p','detail-path',current.id));target.append(header);
  const short=el('div','development-context');short.append(el('span','local-badge','只读 · 不调用模型'),el('span','muted',current.reused?'本批复用经验，没有新增反思':'经验开发／探索性评价，具体范围见原记录'));target.append(short);
  if(current.stop)target.append(el('p','development-stop','批次停止：'+(current.stop.reason||JSON.stringify(current.stop))));
  const scope=el('details','development-record');scope.append(el('summary','','范围、模型与计量'),el('p','',typeof current.scope==='string'?current.scope:JSON.stringify(current.scope||'范围见原报告')));
  for(const [name,value] of [['模型角色',current.roles],['本批成本（原记录）',current.cost]])if(value)scope.append(objectView(name,value));
  current.notices.forEach(text=>scope.append(el('p','muted',text)));target.append(scope);
  for(const link of current.links){const a=el('a','development-source-link',link.label);a.href=batchURL(link.id);target.append(a);}
  const nav=el('nav','development-stages');nav.setAttribute('aria-label','开发材料步骤');
  const stage=current.stages.find(s=>s.id===stageId)||current.stages[0];
  current.stages.forEach((item,index)=>{const b=button('',()=>{location.hash=batchURL(current.id,item.id);},'development-step'+(item===stage?' selected':''));b.append(el('span','development-step-number',String(index+1).padStart(2,'0')),el('strong','',item.title),pill(item.status));b.setAttribute('aria-pressed',String(item===stage));nav.append(b);});target.append(nav);
  const content=el('section','development-content');content.dataset.stage=stage.id;content.append(el('h2','',stage.title),el('p','muted',stage.description));stage.notes.forEach(text=>content.append(el('p','development-note',text)));
  if(['not_started','not_performed','unknown','blocked'].includes(stage.status))content.append(el('p','development-empty',stageStates[stage.status]+'：依据本批实际记录展示，后续材料不会自动推定为已完成。'));
  if(stage.id==='case')renderCases(content);
  if(stage.id==='feedback')renderFeedback(content);
  if(stage.id==='reflection')renderExperience(content);
  if(stage.id==='validation')renderValidation(content);
  if(stage.rows.length)renderRows(content,stage.rows);
  if(stage.id==='freeze') {
    content.append(el('p','development-note','已冻结版本 ≠ 已验证有效。候选接纳、整题通过和生产启用分别解释。'));
    for(const item of current.decision?.decisions||[]){const card=el('div','finding');card.append(el('strong','',item.case+' · '+(item.generated===true?'生成候选经验':item.generated===false?'未生成经验':'生成状态未知')));if(item.reason)card.append(el('p','',item.reason==='both_AUTO_pass_no_experience_generated'?'两次 AUTO 均通过，按原规则不生成经验。':item.reason));const admission=item.admission||{};if(typeof admission.admitted==='boolean')card.append(el('p','',admission.admitted?'归档决定：接纳为研究候选；保留全部限制。':'归档决定：未接纳。'));if(admission.reviewer)card.append(el('p','muted','评价身份：'+admission.reviewer));if(admission.limits?.length)card.append(objectView('接纳记录中的问题与限制',admission.limits));content.append(card);}
    if(current.decision)content.append(objectView('原始冻结／接纳决定',current.decision));
  }
  renderArtifacts(content,stage.artifacts);target.append(content);
}
function renderFeedback(target) {
  const records=current.feedback_records||[{case:'反馈来源',...current.feedback}];
  records.forEach(record=>{
    if(!record.rows?.length&&!record.standard&&!record.explanations)return;
    target.append(el('h3','',record.case));
    if(record.standard)target.append(el('p','development-note','归档标准要求：'+record.standard));
    if(record.preserve_success)target.append(el('p','development-note','需保留：'+record.preserve_success));
    if(record.rows?.length){
      const table=el('table'),head=el('tr');['来源运行／关系','要求值','比较原值','实际值','行为差异'].forEach(name=>head.append(el('th','',name)));const thead=el('thead');thead.append(head);table.append(thead);const body=el('tbody');
      const value=x=>typeof x==='boolean'?String(x):'未知';
      record.rows.forEach(row=>{const line=el('tr');line.append(el('td','',`${row.run||''} / ${row.relation}`),el('td','',value(row.expected)),el('td','',value(row.before)),el('td','',value(row.actual)),el('td','',row.state));body.append(line);});table.append(body);const details=el('details','development-record');details.open=record.rows.length<=12;details.append(el('summary','',`${record.rows.length} 项要求与实际行为对照`));const wrap=el('div','table-wrap');wrap.append(table);details.append(wrap);target.append(details);
    }
    if(record.explanations)target.append(objectView('原因解释／假设（原记录，不自动视为已证实因果）',record.explanations));
    if(record.unknown_causes)target.append(objectView('未知原因',record.unknown_causes));
  });
}
function renderCases(target) {
  const list=el('div','development-cases');
  current.cases.forEach(row=>{const card=el('div','finding');card.append(el('strong','',`${row.alias||'案例'} · ${row.role==='test'?'测试':row.role==='train'?'开发':'同题开发／评价'}`),el('p','',row.case||'案例信息见原始材料'));if(row.independent_unit_id)card.append(el('p','muted','来源单元：'+row.independent_unit_id));list.append(card);});target.append(list);
  target.append(el('p','development-note','自动 Contract 是模型的候选理解；标准 Contract 是有依据的评价要求。此页展示研究材料，不把标准答案交付给维护 Agent。'));
  for(const contract of current.contracts||[]){
    const parts=[];
    if(contract.taxonomy_version==='temporal-obligation-taxonomy-7-v1'&&Array.isArray(contract.obligation_labels))parts.push('七类义务：'+(contract.obligation_labels.map(item=>typeof item==='string'?item:item.code).join('、')||'未知'));
    if(contract.primary_class)parts.push(`历史四类路由：${contract.primary_class}（未自动换算）`);
    const box=el('details','development-record');box.append(el('summary','',`${contract.case} · 候选 Contract · ${parts.join('；')||'类别未记录'}`),el('p','development-note','归档模型原文；引用存在与冻结均不代表其语义正确。'),el('pre','development-text experience-prose',contract.text));target.append(box);
  }
  if(current.preparation)target.append(objectView('材料准入与停止证据',current.preparation));
}
function renderExperience(target) {
  const texts=[...(current.experiences||[])];
  if(current.experience_text)texts.push({case:current.experience||'本批经验',text:current.experience_text});
  texts.forEach(item=>{target.append(el('h3','',item.case+(item.version?' · '+item.version:'')));if(item.text){target.append(el('pre','development-text experience-prose',item.text.text));if(item.text.truncated)target.append(el('p','muted','显示前120000字符；完整材料保存在归档中。'));}for(const [label,value] of [['适用前提',item.requires],['排除条件',item.excludes]])if(value)target.append(objectView(label,value));});
  if(current.experience_diff){const box=el('details','development-record');box.open=true;box.append(el('summary','','经验变化：归档 E1 → 本批经验'),el('pre','development-text',current.experience_diff.text||'两个版本正文一致。'));if(current.experience_diff.truncated)box.append(el('p','muted','差异基于有长度限制的正文片段，不能视为完整差异。'));target.append(box);}
}
function renderValidation(target) {
  if(current.groups?.length){const wrap=el('div','development-comparison');current.groups.forEach(group=>{const box=el('div','finding');const valid=group.valid_denominator;box.append(el('strong','',group.condition),el('p','development-score',typeof valid==='number'&&valid>0?`${group.complete_passed??'未知'} / ${valid} 整题通过`:'无有效评分 · 通过率不可计算'),el('p','muted',`实际启动 ${group.started??'未知'} 次；仅本批分母`));wrap.append(box);});target.append(wrap);}
  if(current.comparisons?.length)target.append(objectView('回验相对各次基线的改善与退步',current.comparisons));
  if(current.test_runs?.length){const box=el('details','development-record');box.append(el('summary','','独立列示测试槽位与路由（不并入开发结果）'));current.test_runs.forEach(test=>{box.append(el('h3','',test.case));renderRows(box,test.runs);if(test.route)box.append(objectView('原始路由记录',test.route));});target.append(box);}
}
function renderRows(target,rows) {
  const table=el('table'),head=el('tr');['运行／条件','行为评分','已通过行为项','运行记录状态','丢失原正确行为'].forEach(name=>head.append(el('th','',name)));const thead=el('thead');thead.append(head);table.append(thead);const body=el('tbody');
  rows.forEach(row=>{const line=el('tr'),loss=el('td');line.append(el('td','',`${row.slot||'来源运行'} · ${row.condition||'见原记录'}`),el('td','',row.valid===true?(row.verdict||'有效；结论见原记录'):row.valid===false?'无有效评分':'评分有效性待核实'),el('td','',row.valid===true&&row.passed!=null&&row.total!=null?`${row.passed}/${row.total}${row.unknown?' · '+row.unknown+'项未知':''}`:'—'),el('td','',row.status));
    if(Array.isArray(row.losses)&&row.losses.length)loss.textContent=row.losses.join('、');else loss.textContent=row.valid===true?'见完整行为／比较记录':'未知';line.append(loss);body.append(line);});table.append(body);const wrap=el('div','table-wrap');wrap.append(table);target.append(wrap);
}
function renderArtifacts(target,artifacts) {
  if(!artifacts.length){target.append(el('p','muted','此步骤没有可读取的关联文件；不补造记录。'));return;}
  const box=el('section','development-artifacts');box.append(el('h3','','证据与原始材料'));const controls=el('div','detail-actions');const viewer=el('pre','development-text artifact-viewer','选择材料查看原文。');
  let request=0;
  artifacts.forEach(item=>{controls.append(button(item.label,async()=>{const ticket=++request;viewer.textContent='正在读取 '+item.name+'…';const batch=current.id;const data=await api(endpoint(batch)+'/artifact?'+new URLSearchParams({name:item.name}));if(ticket!==request||!viewer.isConnected)return;viewer.textContent=(data.truncated?'显示前120000字符；完整文件在归档中。\n\n':'')+data.text;}));});box.append(controls,viewer);target.append(box);
}
$('#development-search').addEventListener('input',()=>catalog&&renderList());
$('#refresh-development').addEventListener('click',()=>refresh().catch(notice));
window.addEventListener('hashchange',()=>load().catch(notice));
refresh().catch(notice);
