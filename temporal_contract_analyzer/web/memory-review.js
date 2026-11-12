'use strict';
const $ = selector => document.querySelector(selector);
const categories = {applicability:'Applicability',event_relation:'Event relations',preservation:'Preservation',exclusion:'Exclusions',verification:'Verification'};
// Display translations only; the versioned taxonomy and stored evidence remain unchanged.
const predicateDescriptions = {
 shared_lifetime:'Shared state or work may outlive an individual consumer.',
 observer_lifetime:'Multiple consumers share the same work through distinct subscription or observer identities.',
 attempt_resource:'Each execution attempt has its own cancellation resource or completion identity.',
 lazy_consumption:'Accessing the cancellation capability synchronously records actual consumption; its ownership can be checked against current evidence.',
 async_resume:'Paused or retrying work can resume through an asynchronous continuation.',
 deferred_batch:'Consecutive inputs are coalesced into deferred work that may remain pending.',
 boundary_persistence:'Current documentation requires accepted persistence obligations to settle before a departure or submission boundary returns.',
 entry_snapshot:'An accepted operation is bound to its entry selection or data; later reentry must not rewrite its established obligations.',
 inline_reentry:'Settlement or notification synchronously invokes callbacks that may reenter navigation or editing.',
 effect_lifetimes:'Persistent results and current UI feedback have distinguishable ownership and validity periods.',
 different_ownership_policy:'The current task explicitly requires an ownership policy that contradicts separating shared state from individual attempts.',
 discard_boundary_policy:'The current task explicitly permits discarding the target accepted persistence obligation instead of settling it.',
 no_lazy_shared_mechanism:'Current evidence explicitly establishes that the repair target has no shared-state and lazy-consumption mechanism.'
};
let selected = new URLSearchParams(location.search).get('record');
let current;
let records=[];
const decisions={accept:'Accepted',revise:'Revision requested',reject:'Rejected'};
function decisionText(decision){return decisions[decision]||decision;}
function reviewedAt(value){return new Date(value).toLocaleString('en-GB');}
function el(tag,text,className){const n=document.createElement(tag);if(text!==undefined)n.textContent=text;if(className)n.className=className;return n;}
function message(text,error=false){$('#message').textContent=text;$('#message').classList.toggle('error',error);}
async function api(path,body){const response=await fetch(path,body===undefined?{}:{method:'POST',headers:{'Content-Type':'application/json','X-TCA-Request':'local'},body:JSON.stringify(body)});const data=await response.json();if(!response.ok)throw Error(data.error||response.statusText);return data;}
function button(text,fn){const b=el('button',text);b.type='button';b.addEventListener('click',()=>Promise.resolve().then(fn).catch(e=>message(e.message,true)));return b;}
function field(parent,label,node){const id='field-'+Math.random().toString(36).slice(2);node.id=id;const l=el('label',label);l.htmlFor=id;parent.append(l,node);return node;}
function select(options){const n=el('select');for(const [value,text] of options){const o=el('option',text);o.value=value;n.append(o);}return n;}
function requestId(){return globalThis.crypto?.randomUUID?.()||Date.now().toString(36)+'-'+Math.random().toString(36).slice(2);}
function sourceName(code){return (current.audit.sources.find(s=>s.sha256===code)?.path||code).split('/').pop();}
async function showEvidence(code,pointer='',line=null,recordCode=current.sha256){
 const path='/api/records/'+recordCode+'/sources/'+code+'?pointer='+encodeURIComponent(pointer)+(line===null?'':'&line='+line);
 const data=await api(path);$('#evidence-title').textContent=data.name+(data.pointer?' · '+data.pointer:'');const body=$('#evidence-body');body.replaceChildren();
 const value=data.value;
 if(value&&Array.isArray(value.labels)&&value.labels.some(l=>typeof l==='object')){
  for(const finding of value.labels){const box=el('div',undefined,'evidence-finding');box.append(el('h3',finding.code+' · '+finding.basis),el('p',finding.reason));for(const anchor of finding.evidence||[]){box.append(el('p',anchor.file.split('/').pop()+' : '+anchor.line,'meta'),el('blockquote',anchor.quote));if(current.audit.sources.some(s=>s.sha256===anchor.sha256))box.append(button('View source context',()=>showEvidence(anchor.sha256,'',anchor.line)));}body.append(box);}
  for(const note of value.notes||[])body.append(el('p',note,'notice'));
 }else body.append(el('pre',data.text));
 if(data.truncated)body.append(el('p','Display truncated. Complete evidence remains in the memory sources/ directory.','notice'));
 if(!$('#evidence').open)$('#evidence').showModal();
}
async function library(){
 const data=await api('/api/library');if(data.review_api_version!=='experience-review-v3')throw Error('This review server is running older Python code. Restart the review service before reviewing new workflow candidates.');$('#store').textContent=data.store;records=data.records.sort((a,b)=>Number(b.latest)-Number(a.latest)||a.id.localeCompare(b.id));renderLibrary();
}
function renderLibrary(){
 const list=$('#library');list.replaceChildren();const pending=records.filter(r=>!r.reviewed).length;$('#counts').textContent='Unreviewed '+pending+' · Reviewed '+(records.length-pending)+' · Total '+records.length;
 if(!records.length){list.append(el('p','This store has no experience versions.','muted'));return;}
 const filter=$('#review-filter').value;
 for(const reviewed of [false,true]){
  if(filter==='pending'&&reviewed||filter==='reviewed'&&!reviewed)continue;
  const group=records.filter(r=>r.reviewed===reviewed);if(!group.length)continue;list.append(el('h3',(reviewed?'Reviewed records':'Unreviewed records')+' ('+group.length+')','group-heading'));
  for(const item of group){const b=button('',()=>openRecord(item.sha256));b.className='version'+(item.sha256===selected?' selected':'');const state=item.display?.state||(reviewed?'Content '+decisionText(item.last_decision.decision):'AI check not recorded');b.append(el('strong',item.display?.title||'Experience record'),el('span',state,'review-state '+(reviewed?'reviewed':'pending')),el('span',item.labels.join(' / ')+' · '+(item.latest?'Latest record':'Historical record')+(item.active?(item.default_eligible?' · Default active':' · Historical selection (not default)'):''),'meta'),el('small',item.version));if(reviewed)b.append(el('small',item.last_decision.reviewer+' · '+reviewedAt(item.last_decision.at)));b.dataset.sha=item.sha256;b.dataset.reviewed=String(reviewed);list.append(b);}
 }
 if(!list.childElementCount)list.append(el('p',filter==='pending'?'No unreviewed records.':'No versions have been reviewed yet.','muted'));
}
async function openRecord(code){
 const data=await api('/api/records/'+code);current=data.bundle;selected=code;history.replaceState(null,'','/?record='+code);render(data);for(const b of document.querySelectorAll('.version'))b.classList.toggle('selected',b.dataset.sha===code);message('');
}
function renderActivation(target,data){
 const state=data.activation;const code=data.bundle.sha256;
 const box=el('div',undefined,'panel');box.append(el('h3','Retrieval version'),el('p',state.current_sha256===code?'This exact version is active.':state.current_sha256?'Another version is active. This version is retained for review and history.':'No version of this experience is active.'));
 box.append(el('p',state.default_eligible?'Passed cross-source development screening. Content acceptance is also required.':'Legacy or pending validation: excluded from the new default retrieval view.'));
 box.append(button('View development screening',async()=>{const value=await api('/api/records/'+code+'/screening');$('#evidence-title').textContent='Development screening';$('#evidence-body').replaceChildren(el('pre',JSON.stringify(value,null,2)));if(!$('#evidence').open)$('#evidence').showModal();}));
 if(state.current_sha256&&state.current_sha256!==code)box.append(button('View active version',()=>openRecord(state.current_sha256)));
 if(state.can_activate||state.can_rollback){
  const actor=field(box,'Operator name',el('input'));const reason=field(box,'Selection reason (optional)',el('textarea'));
  const action=state.can_rollback?'rollback':'activate';
  box.append(button(state.can_rollback?'Roll back to this accepted version':'Activate this accepted version',async()=>{
   if(!actor.value.trim())throw Error('Enter the actual operator name.');
   await api('/api/records/'+code+'/'+action,{actor:actor.value.trim(),reason:reason.value.trim(),expected_current:state.current_sha256});
   await library();render(await api('/api/records/'+code));message('Active retrieval version updated. Existing frozen batches are unchanged.');
  }));
 }
 target.append(box);
}
function renderManualEditor(target,data,draft={}){
 const panel=el('details',undefined,'panel manual-editor');panel.append(el('summary','Edit rules manually'));
 panel.append(el('p','Saving creates an immutable proposal, not acceptance. An authorized worker must check this exact edit before content acceptance and fresh effect validation.','muted'));
 const actor=field(panel,'Editor name',el('input'));actor.value=draft.actor||'';
 const reason=field(panel,'Modification reason',el('textarea'));reason.value=draft.reason||'';
 const editId=draft.request_id||requestId();
 const labels=field(panel,'Obligation labels (comma-separated R/O/B/L/I/F/A)',el('input'));labels.value=(draft.labels||data.bundle.labels).join(', ');
 const requires=field(panel,'Required mechanism predicates (comma-separated)',el('input'));requires.value=(draft.requires||data.bundle.requires).join(', ');
 const excludes=field(panel,'Excluded predicates (comma-separated)',el('input'));excludes.value=(draft.excludes||data.bundle.excludes).join(', ');
 const editors=data.bundle.rules.map(rule=>{
  const box=el('div',undefined,'manual-rule');box.append(el('h3',rule.id));
  const category=field(box,'Category',select(Object.entries(categories)));
  const body=field(box,'Rule text',el('textarea'));body.rows=5;
  const saved=draft.rules?.find(r=>r.id===rule.id)||rule;category.value=saved.category;body.value=saved.body;
  const before=data.review_plan?.rules.find(r=>r.rule_id===rule.id)?.before;
  const actions=el('div',undefined,'actions');
  if(before&&(before.body!==rule.body||before.category!==rule.category))actions.append(button('Use Before for '+rule.id,()=>{body.value=before.body;category.value=before.category;}));
  actions.append(button('Use current text for '+rule.id,()=>{body.value=rule.body;category.value=rule.category;}));box.append(actions);panel.append(box);
  return {id:rule.id,category,body};
 });
 const tokens=node=>node.value.split(',').map(x=>x.trim()).filter(Boolean);
 const capture=()=>({actor:actor.value,reason:reason.value,request_id:editId,labels:tokens(labels),requires:tokens(requires),excludes:tokens(excludes),rules:editors.map(r=>({id:r.id,category:r.category.value,body:r.body.value}))});
 const save=button('Save as new version',async()=>{
  const request=capture();
  if(!request.actor.trim()||!request.reason.trim()||request.rules.some(r=>!r.body.trim())){message('Enter your name, modification reason and nonempty rule text.',true);return;}
  save.disabled=true;
  try{const result=await api('/api/records/'+data.bundle.sha256+'/revise',request);await library();await openRecord(result.sha256);message('New version saved. AI checking is pending on an authorized worker; this page dispatched no model.');}
  finally{save.disabled=false;}
 });
 panel.append(save);target.append(panel);return capture;
}
function renderWorkflow(target,data){
 const w=data.workflow;if(!w)return;
 const last=data.decisions[data.decisions.length-1];const panel=el('div',undefined,'panel workflow-status');
 panel.append(el('h3','Exact-version workflow'),el('p','AI evidence check: '+w.ai_status),el('p','Human content: '+(last?decisionText(last.decision):(w.ai_status==='passed'?'Awaiting human content review':'Not yet eligible for content acceptance'))),el('p','Effect validation: '+w.validation_status),el('p','Workflow state: '+w.status));
 const authorized=last?.enable_authorization?.authorized&&w.authorization_withdrawal?.decision_sha256!==last.sha256;
 panel.append(el('p','Enable after validation: '+(authorized?'Authorized by '+last.reviewer:'Not authorized / withdrawn')));
 if(w.enable_blocker)panel.append(el('p',w.enable_blocker,'notice'));
 if(w.ai_status!=='passed')panel.append(el('p','This candidate is visible, but content acceptance waits for its actual AI evidence check. You may inspect, edit, request revision or reject. This page never dispatches models.','notice'));
 if(w.handoff_source)panel.append(el('p','Recovered from the original reflection without changing its rule text: '+w.handoff_source,'meta'));
 if(w.origin_root)panel.append(el('p','Execution needs an explicitly authorized worker. Opening or submitting this page never launches models.','muted'),el('pre',w.worker_command||'python3 -B -m temporal_contract_analyzer experience-evolution work --root '+w.origin_root+' --execute --watch'));
 else panel.append(el('p','No authorized v3 origin is attached. Prepare a new v3 batch with candidate_sha256 to check/validate this proposal.','notice'));
 if(w.ai_result?.increment_review){const comparisons=el('div',undefined,'increment-comparisons');comparisons.append(el('h4','Rule-by-rule increment comparison'));for(const row of w.ai_result.increment_review.comparisons){const box=el('article');box.append(el('h4',row.rule_id+' · '+row.classification));for(const match of row.matches)box.append(el('p','Prior '+match.experience_sha256+' / '+match.rule_id+': '+match.covered));box.append(el('p','Uncovered increment: '+(row.uncovered_increment||'None stated')),el('p',row.reason));comparisons.append(box);}panel.append(comparisons);}
 if(w.ai_result){const detail=el('details');detail.append(el('summary','AI check: evidence, limits and blockers'),el('pre',JSON.stringify(w.ai_result,null,2)));panel.append(detail);}
 if(w.edit)panel.append(el('p','Edited by '+w.edit.actor+': '+w.edit.reason,'meta'));
 if(authorized){const actor=field(panel,'Operator withdrawing enable authorization',el('input'));const reason=field(panel,'Withdrawal reason (optional)',el('textarea'));panel.append(button('Withdraw automatic enable authorization',async()=>{if(!actor.value.trim())throw Error('Enter the actual operator name.');await api('/api/records/'+data.bundle.sha256+'/revoke-enable',{actor:actor.value.trim(),reason:reason.value.trim()});await openRecord(data.bundle.sha256);message('Enable authorization withdrawn. Content acceptance is retained.');}));}
 target.append(panel);
}
function render(data,rereview=false,fullReview=false,manualRules=new Set(),draft={}){
 const b=data.bundle;const target=$('#detail');target.replaceChildren();const intro=el('div',undefined,'panel');intro.append(el('h2',data.display?.title||'Experience record'),el('p','Experience identity: '+b.id,'meta'),el('p','Version: '+b.version,'meta'),el('p','Version digest: '+b.sha256.slice(0,8)+'…','meta'),el('p','Source batch: '+(data.display?.source_batch||'Not recorded'),'meta'),el('p','Parent: '+(data.display?.parent_description||b.parent_sha256||'None'),'meta'),el('code',b.sha256),el('p',b.labels.join(' / '),'meta'),el('p','Review the rules, labels, applicability and evidence for this exact version. Acceptance permits research use; repair benefit requires evaluation.','notice'));target.append(intro);
 renderActivation(target,data);
 renderWorkflow(target,data);
 const captureManual=renderManualEditor(target,data,draft.manual);
 const last=data.decisions[data.decisions.length-1];const readonly=Boolean(last)&&!rereview;
 intro.append(el('p',last?'✓ Reviewed · '+decisionText(last.decision)+' · '+last.reviewer+' · '+reviewedAt(last.at):(data.display?.state||'AI check not recorded'),'review-state '+(last?'reviewed':'pending')));
 const meta=el('div',undefined,'metadata');for(const [key,title] of [['requires','Required mechanism premises'],['excludes','Exclusions that must be contradicted']]){const box=el('div');box.append(el('h3',title));const ul=el('ul');for(const v of b[key])ul.append(el('li',predicateDescriptions[v]||v));if(!b[key].length)ul.append(el('li','None registered. Check the boundaries in the rules as well.'));box.append(ul);meta.append(box);}intro.append(meta);
 const limitations=el('details');limitations.append(el('summary','Review provenance and limitations'));limitations.append(el('pre',JSON.stringify(b.review,null,2)));intro.append(limitations);
 const delta=data.review_plan;
 const incremental=!readonly&&!rereview&&!fullReview&&delta?.mode==='incremental';
 const form=el('form');form.id='review-form';const fields=[];
 let captureDraft=()=>draft;
 const inheritedCount=incremental?delta.inherited_rule_ids.filter(id=>!manualRules.has(id)).length:0;
 if(delta?.parent_sha256){
  const summary=el('div',undefined,'panel review-delta');summary.append(el('h3','Changes from parent'),button('View parent version',()=>openRecord(delta.parent_sha256)));
  summary.append(el('p',incremental?(b.rules.length-inheritedCount)+' rule(s) require a new finding; '+inheritedCount+' unchanged rule(s) reference the accepted parent review.':'Full review: each rule requires an explicit finding.'));
  if(delta.shared_context_changes.length)summary.append(el('p','Shared context changed: '+delta.shared_context_changes.join(', ')+'. Parent findings cannot be inherited.','notice'));
  for(const removed of delta.removed_rules)summary.append(el('h3','Removed '+removed.id),el('p',removed.body,'body'));
  if(!readonly&&!rereview&&delta.mode==='incremental')summary.append(button(incremental?'Review all rules instead':'Use accepted parent findings',()=>render(data,false,incremental,new Set(),captureDraft())));
  form.append(summary);
 }
 const inheritedGroup=el('details',undefined,'panel inherited-rules');
 if(incremental)inheritedGroup.append(el('summary',inheritedCount+' unchanged rules — referenced parent findings'));
 for(const rule of b.rules){
  const change=delta?.rules.find(r=>r.rule_id===rule.id);
  const inherited=incremental&&change?.inheritable&&!manualRules.has(rule.id);
  const box=el('article',undefined,'rule'+(inherited?' inherited':''));box.append(el('h3',rule.id+' · '+categories[rule.category]));
  if(change?.before&&(change.before.body!==rule.body||change.before.category!==rule.category)){
   const pair=el('div',undefined,'rule-diff');const before=el('div');before.append(el('h4','Before · '+categories[change.before.category]),el('p',change.before.body,'body'));for(const link of change.before_evidence||[])before.append(button('Parent evidence '+link.pointer,()=>showEvidence(link.source_sha256,link.pointer,null,delta.parent_sha256)));
   const after=el('div');after.append(el('h4','After · '+categories[rule.category]),el('p',rule.body,'body'));pair.append(before,after);box.append(pair);
  }else box.append(el('p',rule.body,'body'));
  if(change?.evidence_changed)box.append(el('p','Supporting evidence changed; a new finding is required.','notice'));
  const evidence=el('div',undefined,'actions');for(const link of b.audit.rule_links.filter(l=>l.rule_id===rule.id)){const title=sourceName(link.source_sha256);evidence.append(button((title==='label-review.json'?'Label evidence':title)+' '+link.pointer,()=>showEvidence(link.source_sha256,link.pointer)));}box.append(evidence);
  if(readonly||inherited){
   const finding=readonly?last.rules.find(r=>r.rule_id===rule.id):change.inherited_finding;
   box.append(el('p',(inherited?'Referenced parent finding: ':'Saved finding: ')+(finding.supported?'Supported':'Unsupported or insufficient evidence'),'review-state reviewed'),el('p','Review reason: '+(finding.reason||'Not provided'),'muted'));
   if(finding.inherited_from){box.append(el('p','Inherited from parent '+finding.inherited_from.parent_sha256+' · decision '+finding.inherited_from.decision_sha256+' · '+finding.inherited_from.rule_id,'meta'));if(inherited)box.append(el('p',delta.parent_decision.reviewer+' · '+reviewedAt(delta.parent_decision.at),'meta'));}
   if(inherited)box.append(button('Review '+rule.id+' explicitly',()=>render(data,false,false,new Set([...manualRules,rule.id]),captureDraft())));
  }else{
   const support=field(box,'Are this rule, its labels and boundaries supported?',select([['','Select an option'],['yes','Supported'],['no','Unsupported or insufficient evidence']]));support.required=true;
   const reason=field(box,'Review reason (optional)',el('textarea'));if(draft.rules?.[rule.id]){support.value=draft.rules[rule.id].supported;reason.value=draft.rules[rule.id].reason;}fields.push({id:rule.id,support,reason});
   if(incremental&&change?.inheritable)box.append(button('Use parent finding for '+rule.id,()=>{const next=new Set(manualRules);next.delete(rule.id);render(data,false,false,next,captureDraft());}));
  }
  (inherited?inheritedGroup:form).append(box);
 }
 if(incremental&&inheritedCount)form.append(inheritedGroup);
 const all=el('details',undefined,'panel');all.append(el('summary','All retained sources: tasks, code, reviews and outcomes'));const links=el('div',undefined,'actions');for(const source of b.audit.sources)links.append(button(source.path.split('/').pop(),()=>showEvidence(source.sha256)));all.append(links);form.append(all);
 if(readonly){const result=el('div',undefined,'panel');result.append(el('h2','Saved review decision'),el('p',decisionText(last.decision)+' · '+last.reviewer+' · '+reviewedAt(last.at)),el('p','Overall reason: '+(last.reason||'Not provided')),button('Review this version again',()=>render(data,true)));form.append(result);target.append(form);renderHistory(target,data.decisions);return;}
 const decision=el('div',undefined,'panel');decision.append(el('h2','Submit a review decision'));const reviewer=field(decision,'Reviewer name',el('input'));reviewer.required=true;reviewer.autocomplete='name';const choices=[['','Select an option'],['revise','Request revision'],['reject','Reject this version']];if(!data.workflow||data.workflow.ai_status==='passed')choices.splice(1,0,['accept_only','Accept for review only']);if(data.workflow?.ai_status==='passed')choices.splice(2,0,['accept_after_validation','Accept and authorize enable after effect validation']);const choice=field(decision,'Overall decision',select(choices));choice.required=true;const scope=field(decision,'Use scope',select([['exploratory','Exploratory research: effectiveness unverified'],['research','Research use']]));if(incremental)scope.value=delta.parent_decision.scope;const reason=field(decision,'Overall reason (optional)',el('textarea'));
 const check=el('label',undefined,'check');const confirmed=el('input');confirmed.type='checkbox';confirmed.required=true;check.append(confirmed,el('span',incremental?'I reviewed the changed rules, their interactions with retained rules, and unchanged labels, applicability, evidence and outcomes. I explicitly reference the displayed parent findings for the unchanged rules.':'I have reviewed all rules, labels, applicability conditions, source evidence and retained repair outcomes for this exact version. These findings reflect my own review.'));decision.append(check);
 if(draft.reviewer!==undefined){reviewer.value=draft.reviewer;choice.value=draft.choice;scope.value=draft.scope;reason.value=draft.reason;confirmed.checked=draft.confirmed;}
 const reviewId=draft.request_id||requestId();
 captureDraft=()=>({request_id:reviewId,manual:captureManual(),rules:{...(draft.rules||{}),...Object.fromEntries(fields.map(f=>[f.id,{supported:f.support.value,reason:f.reason.value}]))},reviewer:reviewer.value,choice:choice.value,scope:scope.value,reason:reason.value,confirmed:confirmed.checked});
 const submit=el('button','Submit decision','primary');submit.type='submit';decision.append(submit,el('p','Reviews remain in decisions/. Active retrieval is selected in active.json. Reaccepting an older or incompatible version records review without replacing the active version. Use the explicit rollback action for an accepted compatible ancestor. No model call or Git commit is made.','muted'));form.append(decision);target.append(form);
 renderHistory(target,data.decisions);
 form.addEventListener('submit',async event=>{event.preventDefault();if(!form.reportValidity())return;if(choice.value.startsWith('accept')&&fields.some(f=>f.support.value!=='yes')){message('Acceptance requires supported new findings and accepted inherited findings. Otherwise, request revision or reject this version.',true);return;}if(incremental&&scope.value!==delta.parent_decision.scope){message('Changing the review scope requires choosing “Review all rules instead”.',true);return;}submit.disabled=true;try{const request={request_id:reviewId,auto_enable:choice.value==='accept_after_validation',reviewer:reviewer.value.trim(),decision:choice.value.startsWith('accept')?'accept':choice.value,reason:reason.value.trim(),scope:scope.value,rules:fields.map(f=>({rule_id:f.id,supported:f.support.value==='yes',reason:f.reason.value.trim()}))};if(incremental)request.inherit_from=delta.inherit_from;const result=await api('/api/records/'+b.sha256+'/decision',{reviewed:confirmed.checked,activate:false,expected_current:data.activation.current_sha256,decision:request});await library();render(await api('/api/records/'+b.sha256));message((result.default_active?'Review saved. This exact version is active in default retrieval.':'Review saved. Validation/enable intent is persisted; authorized workers continue separately.')+' Saved to: '+result.directory);}catch(error){message(error.message,true);}finally{submit.disabled=false;}});
}
function renderHistory(target,rows){if(!rows.length)return;const history=el('div',undefined,'panel history');history.append(el('h3','Review history'));for(const d of rows)history.append(el('p',d.reviewer+' · '+decisionText(d.decision)+' · '+reviewedAt(d.at)+(d.reason?' · '+d.reason:'')));target.append(history);}
$('#close-evidence').addEventListener('click',()=>$('#evidence').close());
$('#review-filter').addEventListener('change',renderLibrary);
$('#refresh-library').addEventListener('click',()=>library().then(()=>message('Review queue refreshed. Your current form was retained.')).catch(error=>message(error.message,true)));
library().then(()=>selected?openRecord(selected):undefined).catch(error=>message(error.message,true));
