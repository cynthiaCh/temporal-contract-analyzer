'use strict';
const $ = selector => document.querySelector(selector);
const systemText = window.TCAReportText;
const labels = {parsed:'Parsed within scope', partial:'Partially parsed', failed:'Scan failed', empty:'No source'};
const origins = {vscode:'VS Code', codex:'Codex', cli:'CLI', web:'Browser'};
const decisions = {confirmed:'Supported', dismissed:'Not supported', uncertain:'Uncertain'};
let items = [], offset = 0, total = 0, selected, current, tab = 'findings', detailRequest = 0, listRequest = 0;
const protections = {sufficient:'Sufficient', insufficient:'Insufficient', uncertain:'Uncertain'};
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
function showError(error) { $('#notice').textContent = systemText(error.message || String(error)); $('#notice').classList.remove('hidden'); }
function clearError() { $('#notice').classList.add('hidden'); }
async function api(url, data) {
  const options = data === undefined ? {} : {method:'POST', headers:{'Content-Type':'application/json','X-TCA-Request':'local'}, body:JSON.stringify(data)};
  const response = await fetch(url, options);
  const result = await response.json();
  if (!response.ok) throw new Error(result.error || `Request failed: ${response.status}`);
  return result;
}
function date(value) { return new Date(value).toLocaleString('en-GB', {hour12:false}); }
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
  $('#total').textContent = `${total} reports`;
  $('#page-label').textContent = total ? `${offset+1}–${Math.min(offset+pageSize,total)} / ${total}` : '0 reports';
  $('#previous').disabled = offset === 0;
  $('#next').disabled = offset+pageSize >= total;
  const list = $('#report-list'); list.replaceChildren();
  for (const meta of items) {
    const row = element('a', 'report-row'+(meta.report_id === selected ? ' selected' : ''));
    row.href = '#report='+meta.report_id;
    row.append(element('div', 'row-title', meta.label || meta.project));
    row.append(element('div', 'row-subtitle', `${meta.project} · ${meta.scope.mode === 'file' ? meta.scope.path : 'Whole directory'}`));
    const bottom = element('div', 'row-bottom'); bottom.append(badge(meta.status), element('span', '', origins[meta.origin] || meta.origin)); row.append(bottom);
    row.append(element('div', 'row-subtitle', date(meta.created_at)));
    list.append(row);
  }
  if (!items.length) list.append(element('p','muted', 'No matching reports. Start a scan or clear the filters.'));
  if (result.invalid.length) showError(new Error(`${result.invalid.length} report metadata entries could not be read. Check the store.`));
}

async function openReport(id) {
  const ticket = ++detailRequest;
  if (selected !== id) { reviewPaths = null; contextFinding = ''; }
  selected = id;
  $('#detail').replaceChildren(element('p', 'loading', 'Reading and verifying the archived report...'));
  for (const row of document.querySelectorAll('.report-row')) row.classList.toggle('selected', row.hash === '#report='+id);
  try {
    const value = await api(reportURL(id));
    if (ticket !== detailRequest) return;
    current = value; tab = 'findings'; render();
  } catch (error) {
    if (ticket === detailRequest) $('#detail').replaceChildren(element('div','error-block', 'Could not read report: '+systemText(error.message)));
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
    $('#scan-parent').textContent = 'The new report will link to this baseline and scan the current files on disk.';
  }
  $('#scan-dialog').showModal(); form.elements.candidate.focus();
}

function render() {
  const {metadata:meta, report} = current;
  const detail = $('#detail'); detail.replaceChildren();
  detail.append(element('p','scope-notice','Use this page before code changes: inspect AST evidence, read related source, and save local review judgments. Analysis review for evolution and expert activation of reusable experience are separate steps.'));
  const header = element('div', 'detail-header');
  header.append(element('span','eyebrow', 'ARCHIVED ANALYSIS'));
  const title = element('div','detail-title'); title.append(element('h2','',meta.label || meta.project), badge(meta.status)); header.append(title);
  const info = element('div','detail-meta');
  for (const value of [date(meta.created_at), origins[meta.origin] || meta.origin, meta.input_kind === 'editor_snapshot' ? 'Includes editor snapshot' : 'Source from disk', 'v'+meta.tool_version]) info.append(element('span','',value));
  header.append(info, element('code','',meta.report_id), element('p','detail-path',meta.candidate_root+(meta.scope.mode === 'file' ? '/'+meta.scope.path : '')));
  const actions = element('div','detail-actions');
  actions.append(button('Scan again from this baseline',()=>openScan(meta)));
  actions.append(button('Copy report ID',async()=>{await navigator.clipboard.writeText(meta.report_id);}));
  if (report) actions.append(artifactLink(meta.report_id,'report.html','Archived report (original) ↗'),artifactLink(meta.report_id,'report.json','JSON ↗'));
  actions.append(artifactLink(meta.report_id,'snapshot.json','Input snapshot ↗'));
  header.append(actions); detail.append(header);
  if (!report) {
    detail.append(element('div','summary-strip','This scan produced no analysis. Its failure details were archived.'),element('div','error-block',systemText(meta.error) || 'Unknown error'));
  } else {
    const strip = element('div','summary-strip');
    for (const [number, label] of [[report.summary.review_hints,'hints to review'],[`${report.summary.parsed_files}/${report.summary.files}`,'files parsed'],[report.summary.events,'syntax events']]) {
      const metric = element('div','metric'); metric.append(element('strong','',number),element('span','',label)); strip.append(metric);
    }
    detail.append(strip,element('p','scope-notice', 'This report shows the source and results captured at scan time. Hints need review; no matching hint does not establish safety.'+(report.files.some(f=>f.language==='vue') ? ' Vue analysis covers script syntax; templates and framework scheduling are outside scope.' : '')));
  }
  const tabs = element('div','tabs'); tabs.setAttribute('role','tablist');
  for (const [key, label] of [['findings','Boundary review'],['context','Source context'],['source','Source snapshot'],['compare','Compare scans'],['provenance','Provenance'],['delivery','Agent deliveries']]) {
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
  content.append(element('h3','','Findings → related definitions → agent review'),
    element('p','scope-notice','Expand identifiable definitions within the archived snapshot, with origins and unresolved references. This does not call a model or establish complete dependencies or a defect.'));
  if (!report) { content.append(element('p','muted','This report has no available analysis.')); return; }
  const form=element('form','note-form context-controls');
  const select=element('select'); select.setAttribute('aria-label','Select a finding');
  const all=element('option','','All findings'); all.value=''; select.append(all);
  for (const finding of report.findings) {
    const option=element('option','',`${finding.id} · ${finding.rule}`); option.value=finding.id; select.append(option);
  }
  select.value=contextFinding;
  const depth=element('select'); depth.setAttribute('aria-label','Definition expansion depth');
  for(let n=0;n<=5;n++){const option=element('option','',`Expand ${n} definition levels`);option.value=String(n);depth.append(option);} depth.value='1';
  const budget=element('input');budget.type='number';budget.min='1';budget.max='100000';budget.value='12000';budget.setAttribute('aria-label','Source character budget');
  const aliases=element('textarea');aliases.value='{}';aliases.rows=2;aliases.setAttribute('aria-label','Path aliases JSON');
  for(const [label,field] of [['Finding',select],['Expansion depth',depth],['Source character budget (excluding explanations)',budget]]) {
    const wrapper=element('label','field');wrapper.append(element('span','',label),field);form.append(wrapper);
  }
  const advanced=element('details','context-aliases');advanced.append(element('summary','','Path aliases (optional)'));
  const aliasField=element('label','field');aliasField.append(element('span','','Example: {"@":"src"}'),aliases);advanced.append(aliasField);form.append(advanced);
  const submit=element('button','primary','Build source context');submit.type='submit';form.append(submit);
  const result=element('div');content.append(form,result);
  let request=0;
  async function load() {
    const ticket=++request;
    contextFinding=select.value;
    const mapping=JSON.parse(aliases.value);
    const query=new URLSearchParams({depth:depth.value,max_chars:budget.value,aliases:JSON.stringify(mapping)});
    if(select.value)query.set('finding_id',select.value);
    submit.disabled=true;result.replaceChildren(element('p','muted','Expanding definitions from archived source...'));
    try {
      const data=await api(reportURL(meta.report_id)+'/context?'+query);
      if(ticket!==request || !content.isConnected)return;
      const packet=data.context;
      result.replaceChildren(element('p','muted',`${packet.usage.snippets} snippets · ${packet.usage.code_chars} characters · ${packet.unresolved.length} unresolved references`),
        button('Copy context for agent review',async()=>navigator.clipboard.writeText(data.markdown)));
      if(!packet.snippets.length)result.append(element('p','muted','No findings selected. No matching hint does not establish safety.'));
      for(const snippet of packet.snippets) {
        const card=element('article','finding');
        card.append(element('h3','',`${snippet.file}:${snippet.start_line}–${snippet.end_line} · ${snippet.kind==='seed'?'Seed evidence':'Related definition'}`));
        const descriptions=snippet.reasons.map(reason=>reason.kind==='finding-evidence'
          ? `Source evidence for finding ${reason.finding_id}`
          : `${reason.from_file}:${reason.reference_line} uses ${reason.local_name || reason.symbol}${reason.module?' from '+reason.module:''}`);
        for(const description of new Set(descriptions))card.append(element('p','muted',description));
        card.append(element('pre','',snippet.code),button('View archived source',()=>{tab='source';render();loadSource(snippet.file,snippet.start_line,snippet.end_line).catch(showError);},'source-link'));
        result.append(card);
      }
      const gaps=element('article','finding');gaps.append(element('h3','','Unresolved references'));
      if(!packet.unresolved.length)gaps.append(element('p','muted','No identifiable gaps were recorded. Results remain limited to the supported analysis scope.'));
      for(const gap of packet.unresolved)gaps.append(element('p','annotation',`${gap.from_file || ''}${gap.reference_line?':'+gap.reference_line:''} · ${gap.symbol || ''} · ${gap.reason}${gap.target_file?' → '+gap.target_file:''}${gap.detail?' · '+gap.detail:''}`));
      result.append(gaps);
      const limits=element('article','finding');limits.append(element('h3','','Analysis scope'));
      for(const limitation of packet.limitations)limits.append(element('p','muted',systemText(limitation)));result.append(limits);
    } catch(error) {
      if(ticket===request && content.isConnected)result.replaceChildren(element('div','error-block',systemText(error.message)));
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
  const refs = card.evidence_ids.map(id=>events.get(id)).filter(Boolean).map(e=>`${e.path}:${e.line}`).join(', ');
  const review = note?.boundary_review;
  return [`Candidate execution boundary: ${card.title}`,
    `Execution boundary: ${card.boundary.evidence_ids.map(id=>events.get(id)).filter(Boolean).map(e=>`${e.path}:${e.line} · ${e.kind}`).join(', ')}`,
    `Possible changes: ${card.possible_changes.summary}`,
    `Affected effects: ${card.effects.summary}${card.effects.evidence_ids.map(id=>events.get(id)).filter(Boolean).map(e=>`${e.path}:${e.line} · ${e.text.trim()}`).join(', ')}`,
    `Review question: ${card.requirement_protection.summary}`,
    `Conditions and limits: ${card.condition}`,
    `Human relation judgment: ${note ? decisions[note.decision] : 'Uncertain'}; protection: ${review ? protections[review.protection] : 'Uncertain'}.`,
    ...(review?.requirement_basis ? [`Requirement and protection basis (human record): ${review.requirement_basis}`] : []),
    ...(note?.note ? [`Relation basis (human record): ${note.note}`] : []),
    `Missing evidence: ${review?.missing_evidence || 'Check call reachability, work ownership and the scope of protection.'}`,
    `Evidence: ${refs}. Archived report: ${meta.report_id}; finding: ${card.finding_id}; input hash: ${meta.input_sha256}.`,
    'Compare the current source with the archived snapshot first. This card is a review clue; a human judgment is not an oracle verdict.'].join('\n');
}

function renderFindings(content) {
  const {report, metadata:meta, notes, boundary_cards:rawCards=[]} = current;
  const cards = rawCards.map(card => ({...card, title:systemText(card.title), condition:systemText(card.condition),
    ...Object.fromEntries(['boundary','possible_changes','effects','requirement_protection'].map(key => [key, {...card[key], summary:systemText(card[key].summary)}]))}));
  if (!report) { content.append(element('p','muted','The scan failed; no rule hints are available for review.')); return; }
  const events = new Map(report.files.flatMap(file=>file.events.map(event=>[event.id,event])));
  content.append(element('p','scope-notice','Locate the boundary, check whether the relation is supported and protection is sufficient, then record missing evidence. Keep uncertain judgments when repository requirements are not established.'));
  const scope = element('div','card-scope');
  const paths = element('input'); paths.value=(reviewPaths || []).join(', '); paths.placeholder='Relative file paths, separated by commas'; paths.setAttribute('aria-label','Changed files');
  const applyPaths = ()=>{reviewPaths=paths.value.trim() ? paths.value.split(',').map(p=>p.trim()).filter(Boolean) : null;render();};
  paths.addEventListener('keydown',event=>{if(event.key==='Enter')applyPaths();});
  scope.append(paths,button('Filter to changes and related calls',applyPaths),button('Show all cards',()=>{reviewPaths=null;render();}));
  if (meta.parent_report_id) scope.append(button('Use files changed since baseline',async()=>{
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
  content.append(element('p','scope-notice',`Showing ${shown.length}/${cards.length} candidate cards. ${related ? 'Selected files: '+reviewPaths.join(', ')+'; related files: '+[...related].join(', ')+'. Expansion uses file-level candidate direct call links only. ' : 'Showing all candidate cards from this scan. '}${missing.length ? 'Paths absent from this snapshot: '+missing.join(', ')+'. ' : ''}Dynamic dispatch, callback targets, framework scheduling and paths outside the scan are not fully covered. Hidden cards and paths without hints still need review.`));
  const coverage=element('details','review-box');coverage.append(element('summary','','Scan coverage and limitations'));
  for(const limitation of report.limitations)coverage.append(element('p','muted',systemText(limitation)));
  for(const file of report.files.filter(f=>f.status!=='parsed'))coverage.append(element('p','error-block',`${file.path} · ${systemText(file.error?.message) || file.status}`));
  for(const file of report.skipped)coverage.append(element('p','muted',`${file.path} · ${systemText(file.reason)}`));
  content.append(coverage);
  function sourceButton(id) {
    const event=events.get(id);
    return button(`${event.path}:${event.line} · ${event.kind}`,()=>{tab='source';render();loadSource(event.path,event.line,event.end_line).catch(showError);},'source-link');
  }
  for (const candidate of shown) {
    const card = element('article','finding boundary-card');
    const ownNotes=notes.filter(n=>n.finding_id===candidate.finding_id), latest=ownNotes.at(-1);
    const head=element('div','finding-head');head.append(element('code','',candidate.rule),element('span','',candidate.finding_id),element('span','pill',latest ? decisions[latest.decision] : 'Uncertain'));
    card.append(head,element('h3','',candidate.title));
    const questions=element('dl','boundary-questions');
    for (const [label,value] of [['Where is the execution boundary?',candidate.boundary],['What may have changed?',candidate.possible_changes],['Which effects may be affected?',candidate.effects],['What requirements and protection apply?',candidate.requirement_protection]]) {
      const answer=element('dd');answer.append(element('p','',value.summary));
      for(const id of value.evidence_ids || [])answer.append(sourceButton(id));
      if(label==='What requirements and protection apply?')answer.append(element('p','muted',latest?.boundary_review?.requirement_basis || 'Repository evidence is still needed. A guard or cancellation call alone does not establish sufficient protection.'));
      questions.append(element('dt','',label),answer);
    }
    card.append(questions);
    const evidence=element('details','evidence');evidence.append(element('summary','','Source evidence, conditions and limits'));
    evidence.append(element('p','muted',candidate.condition));
    for(const id of candidate.evidence_ids){evidence.append(sourceButton(id),element('pre','',events.get(id).text));}
    card.append(evidence);
    const actions=element('div','detail-actions');
    actions.append(button('Expand related source',()=>{contextFinding=candidate.finding_id;tab='context';render();}));
    actions.append(button('Copy review packet for an agent',async()=>{await navigator.clipboard.writeText(boundaryPacket(candidate,events,meta,latest));}));
    card.append(actions);
    const review=element('details','review-box');review.append(element('summary','','Human review notes'));
    if(ownNotes.length)review.open=true;
    for(const note of ownNotes){
      const structured=note.boundary_review;
      review.append(element('div','annotation',`${decisions[note.decision]} · ${date(note.created_at)}\n${note.note}`+(structured ? `\n保护：${protections[structured.protection]}\nRequirement and protection basis：${structured.requirement_basis || 'To be supplied'}\nMissing evidence: ${structured.missing_evidence || 'Not recorded'}` : '')));
    }
    const form=element('form','note-form');
    function field(label,node){const wrapper=element('label','review-field');wrapper.append(element('span','',label),node);form.append(wrapper);return node;}
    const decision=element('select');decision.setAttribute('aria-label','Relation judgment');
    for(const [value,label] of Object.entries(decisions)){const option=element('option','',label);option.value=value;decision.append(option);}
    decision.value=latest?.decision || 'uncertain';field('Is the relation supported?',decision);
    const note=element('textarea');note.placeholder='Record source or test evidence for this judgment.';note.maxLength=10000;note.setAttribute('aria-label','Relation basis');field('Judgment basis',note);
    const protection=element('select');protection.setAttribute('aria-label','Protection sufficiency');
    for(const [value,label] of Object.entries(protections)){const option=element('option','',label);option.value=value;protection.append(option);}
    protection.value=latest?.boundary_review?.protection || 'uncertain';field('Is the current protection sufficient?',protection);
    const basis=element('textarea');basis.maxLength=10000;basis.value=latest?.boundary_review?.requirement_basis || '';basis.placeholder='Cite repository requirements, callers, tests or design notes, and state which effects the protection constrains.';basis.setAttribute('aria-label','Requirement and protection basis');field('Requirement and protection basis',basis);
    const missingEvidence=element('textarea');missingEvidence.maxLength=10000;missingEvidence.placeholder='For example: which call path or execution trace is needed to check pending notifications and delivery after close?';missingEvidence.setAttribute('aria-label','Missing evidence');field('What evidence is missing?',missingEvidence);
    const save=element('button','quiet','Save review note');save.type='submit';form.append(save);
    form.addEventListener('submit',async event=>{
      event.preventDefault();save.disabled=true;
      try{
        const saved=await api(reportURL(meta.report_id)+'/notes',{finding_id:candidate.finding_id,decision:decision.value,note:note.value,boundary_review:{protection:protection.value,requirement_basis:basis.value,missing_evidence:missingEvidence.value}});
        if(current.metadata.report_id===meta.report_id){current.notes.push(saved);render();}
      }catch(error){showError(error);save.disabled=false;}
    });
    review.append(form);card.append(review);content.append(card);
  }
  if(!shown.length)content.append(element('p','muted','No candidate cards in this scope. Review parsing coverage, unmodeled behavior and project tests.'));
}

function renderSource(content) {
  const files = current.report?.files || [];
  if (!files.length) { content.append(element('p','muted','This record has no captured source.'));return; }
  const toolbar=element('div','source-toolbar');const select=element('select');select.id='source-select';select.setAttribute('aria-label','Archived source file');
  for(const file of files){const option=element('option','',file.path);option.value=file.path;select.append(option);}
  select.addEventListener('change',()=>loadSource(select.value).catch(showError));
  toolbar.append(select,element('span','muted','Archived snapshot'));content.append(toolbar,element('div','code-view'));content.querySelector('.code-view').id='source-code';
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
  const values={'Report ID':meta.report_id,'Project':meta.project,'Task ID':meta.task_id || 'Not specified','Baseline report':meta.parent_report_id || 'Not linked','Scan scope':meta.scope.mode==='file'?meta.scope.path:'Whole directory','Input kind':meta.input_kind,'Unsaved overlays':meta.overlays.join(', ') || '无','Input hash':meta.input_sha256 || 'Not available','Tool hash':meta.tool_sha256 || 'Not available','Tool version':meta.tool_version,'Available frozen layers':meta.layers.join(', ') || 'None (incomplete parsing)'};
  for(const [label,value] of Object.entries(values)){list.append(element('dt','',label),element('dd','',value));}
  content.append(list,element('p','integrity','Archive bytes and input binding were verified on read. This does not establish semantic correctness or provide a tamper-proof signature.'));
  content.append(button('Verify archive again',async()=>{await api(reportURL(meta.report_id)+'/verify',{});showError(new Error('Archive verified. Analysis semantics were not verified.'));}));
  if(report){
    const table=element('table');const head=element('tr');for(const label of ['File','Parse status','Scope / error'])head.append(element('th','',label));table.append(head);
    for(const file of report.files){const row=element('tr');for(const value of [file.path,file.status,systemText(file.error?.message||file.analysis_scope)||''])row.append(element('td','',value));table.append(row);}
    const wrap=element('div','table-wrap');wrap.append(table);content.append(element('h3','','File coverage'),wrap);
    for(const limit of report.limitations)content.append(element('p','muted',systemText(limit)));
    if(report.skipped.length){content.append(element('h3','','Skipped files and directories'));for(const item of report.skipped)content.append(element('p','muted',`${item.path} · ${systemText(item.reason)}`));}
  }
}

function renderDeliveries(content) {
  content.append(element('p','scope-notice','Delivery records retain the exact MCP response material and transport status. A transport write does not prove client receipt, model attention or use. Manual copying and ordinary CLI reads are not recorded as agent deliveries.'));
  const prepared=current.deliveries.filter(d=>d.state==='prepared_for_tool_response');
  if(!prepared.length){content.append(element('p','muted','No observable agent report deliveries yet.'));return;}
  for(const record of prepared){
    const written=current.deliveries.some(d=>d.delivery_id===record.delivery_id&&d.state==='transport_written');
    const card=element('details','finding');card.append(element('summary','',`${date(record.created_at)} · ${record.payload.material} · ${written?'Transport written':'Prepared; transport unconfirmed'}`));
    card.append(element('p','muted',`Client: ${record.client?.name||'Unknown'} · Character range: ${record.payload.offset}–${record.payload.offset+record.payload.text.length}`),element('code','',record.payload.response_text_sha256),element('pre','',record.payload.text));content.append(card);
  }
}

async function renderComparison(content) {
  const meta=current.metadata;
  const previous=await api('/api/reports?'+new URLSearchParams({project:meta.project_id,limit:500}));
  if(current.metadata.report_id!==meta.report_id||tab!=='compare')return;
  const matches=previous.items.filter(m=>m.report_id!==meta.report_id&&m.scope.mode===meta.scope.mode&&m.scope.path===meta.scope.path);
  const box=element('div','comparison');box.append(element('p','muted','Compare reports for the same project and scan scope. Hint changes require compatible tool and parser environments.'));
  if(!matches.length){box.append(element('p','muted','No comparable report with the same scope yet. Use “Scan again from this baseline” to create one.'));content.append(box);return;}
  const controls=element('div','comparison-controls');const select=element('select');select.setAttribute('aria-label','Baseline report to compare');
  for(const item of matches){const option=element('option','',`${date(item.created_at)} · ${item.label||item.project} · ${item.report_id.slice(-12)}`);option.value=item.report_id;select.append(option);}
  if(matches.some(m=>m.report_id===meta.parent_report_id))select.value=meta.parent_report_id;
  const output=element('div');
  controls.append(select,button('Compare with current report',async()=>{
    const delta=await api('/api/compare?'+new URLSearchParams({before:select.value,after:meta.report_id}));
    output.replaceChildren(element('p','scope-notice',systemText(delta.interpretation)));
    if(!delta.comparable){output.append(element('p','error-block','The reports do not meet complete-analysis comparability requirements. Hint changes were not computed.'));return;}
    for(const [label,values] of [['Added hints',delta.added_hints.map(f=>`${f.path} · ${f.rule}`)],['Removed hints',delta.removed_hints.map(f=>`${f.path} · ${f.rule}`)],['Changed files',delta.changed_files]]){
      output.append(element('h3','',`${label} · ${values.length}`));const list=element('ul');for(const value of values)list.append(element('li','',value));output.append(list);
    }
  }));box.append(controls,output);content.append(box);
}

$('#new-scan').addEventListener('click',()=>openScan());
$('#close-scan').addEventListener('click',()=>$('#scan-dialog').close());
$('#scan-form').addEventListener('submit',async event=>{
  event.preventDefault();const submit=$('#scan-submit');submit.disabled=true;submit.textContent='Scanning and archiving...';$('#scan-error').textContent='';
  const data=Object.fromEntries(new FormData(event.target));for(const key of Object.keys(data))if(!data[key])delete data[key];
  try{const result=await api('/api/scans',data);$('#scan-dialog').close();$('#search').value='';$('#status').value='';$('#origin').value='';offset=0;await loadReports();location.hash='report='+result.report_id;}
  catch(error){$('#scan-error').textContent=systemText(error.message);}
  finally{submit.disabled=false;submit.textContent='Scan and archive';}
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
