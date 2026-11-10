'use strict';
const $ = selector => document.querySelector(selector);
const names = {'subscription-retirement':'Subscription Retirement and Deferred Auditing','paused-shared-work':'Shared Work and Cancellation Recovery','deferred-boundary-binding':'Deferred Editing and Boundary Settlement'};
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
function sourceName(code){return (current.audit.sources.find(s=>s.sha256===code)?.path||code).split('/').pop();}
async function showEvidence(code,pointer='',line=null){
 const path='/api/records/'+current.sha256+'/sources/'+code+'?pointer='+encodeURIComponent(pointer)+(line===null?'':'&line='+line);
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
 const data=await api('/api/library');$('#store').textContent=data.store;records=data.records.sort((a,b)=>Number(b.latest)-Number(a.latest)||a.id.localeCompare(b.id));renderLibrary();
}
function renderLibrary(){
 const list=$('#library');list.replaceChildren();const pending=records.filter(r=>!r.reviewed).length;$('#counts').textContent='Pending '+pending+' · Reviewed '+(records.length-pending)+' · Total '+records.length;
 if(!records.length){list.append(el('p','This store has no experience versions.','muted'));return;}
 const filter=$('#review-filter').value;
 for(const reviewed of [false,true]){
  if(filter==='pending'&&reviewed||filter==='reviewed'&&!reviewed)continue;
  const group=records.filter(r=>r.reviewed===reviewed);if(!group.length)continue;list.append(el('h3',(reviewed?'Reviewed':'Pending')+' ('+group.length+')','group-heading'));
  for(const item of group){const b=button('',()=>openRecord(item.sha256));b.className='version'+(item.sha256===selected?' selected':'');const state=reviewed?'✓ Reviewed · '+decisionText(item.last_decision.decision):'Awaiting review';b.append(el('strong',names[item.id]||item.id),el('span',state,'review-state '+(reviewed?'reviewed':'pending')),el('span',item.labels.join(' / ')+' · '+(item.latest?'Latest version':'Historical version')+(item.active?' · Active':''),'meta'),el('small',item.version));if(reviewed)b.append(el('small',item.last_decision.reviewer+' · '+reviewedAt(item.last_decision.at)));b.dataset.sha=item.sha256;b.dataset.reviewed=String(reviewed);list.append(b);}
 }
 if(!list.childElementCount)list.append(el('p',filter==='pending'?'No versions are awaiting review.':'No versions have been reviewed yet.','muted'));
}
async function openRecord(code){
 const data=await api('/api/records/'+code);current=data.bundle;selected=code;history.replaceState(null,'','/?record='+code);render(data);for(const b of document.querySelectorAll('.version'))b.classList.toggle('selected',b.dataset.sha===code);message('');
}
function render(data,rereview=false){
 const b=data.bundle;const target=$('#detail');target.replaceChildren();const intro=el('div',undefined,'panel');intro.append(el('h2',names[b.id]||b.id),el('p',b.version,'meta'),el('code',b.sha256),el('p',b.labels.join(' / '),'meta'),el('p','Review the rules, labels, applicability and evidence for this exact version. Acceptance permits research use; repair benefit requires evaluation.','notice'));target.append(intro);
 const last=data.decisions[data.decisions.length-1];const readonly=Boolean(last)&&!rereview;
 intro.append(el('p',last?'✓ Reviewed · '+decisionText(last.decision)+' · '+last.reviewer+' · '+reviewedAt(last.at):'Awaiting review','review-state '+(last?'reviewed':'pending')));
 const meta=el('div',undefined,'metadata');for(const [key,title] of [['requires','Required mechanism premises'],['excludes','Exclusions that must be contradicted']]){const box=el('div');box.append(el('h3',title));const ul=el('ul');for(const v of b[key])ul.append(el('li',predicateDescriptions[v]||v));if(!b[key].length)ul.append(el('li','None registered. Check the boundaries in the rules as well.'));box.append(ul);meta.append(box);}intro.append(meta);
 const limitations=el('details');limitations.append(el('summary','Review provenance and limitations'));limitations.append(el('pre',JSON.stringify(b.review,null,2)));intro.append(limitations);
 const form=el('form');form.id='review-form';const fields=[];
 for(const rule of b.rules){const box=el('article',undefined,'rule');box.append(el('h3',rule.id+' · '+categories[rule.category]),el('p',rule.body,'body'));const evidence=el('div',undefined,'actions');for(const link of b.audit.rule_links.filter(l=>l.rule_id===rule.id)){const title=sourceName(link.source_sha256);evidence.append(button((title==='label-review.json'?'Label evidence':title)+' '+link.pointer,()=>showEvidence(link.source_sha256,link.pointer)));}box.append(evidence);if(readonly){const finding=last.rules.find(r=>r.rule_id===rule.id);box.append(el('p','Saved finding: '+(finding.supported?'Supported':'Unsupported or insufficient evidence'),'review-state reviewed'));box.append(el('p','Review reason: '+(finding.reason||'Not provided'),'muted'));}else{const support=field(box,'Are this rule, its labels and boundaries supported?',select([['','Select an option'],['yes','Supported'],['no','Unsupported or insufficient evidence']]));support.required=true;const reason=field(box,'Review reason (optional)',el('textarea'));fields.push({id:rule.id,support,reason});}form.append(box);}
 const all=el('details',undefined,'panel');all.append(el('summary','All retained sources: tasks, code, reviews and outcomes'));const links=el('div',undefined,'actions');for(const source of b.audit.sources)links.append(button(source.path.split('/').pop(),()=>showEvidence(source.sha256)));all.append(links);form.append(all);
 if(readonly){const result=el('div',undefined,'panel');result.append(el('h2','Saved review decision'),el('p',decisionText(last.decision)+' · '+last.reviewer+' · '+reviewedAt(last.at)),el('p','Overall reason: '+(last.reason||'Not provided')),button('Review this version again',()=>render(data,true)));form.append(result);target.append(form);renderHistory(target,data.decisions);return;}
 const decision=el('div',undefined,'panel');decision.append(el('h2','Submit a review decision'));const reviewer=field(decision,'Reviewer name',el('input'));reviewer.required=true;reviewer.autocomplete='name';const choice=field(decision,'Overall decision',select([['','Select an option'],['accept','Accept and activate'],['revise','Request revision'],['reject','Reject this version']]));choice.required=true;const scope=field(decision,'Use scope',select([['exploratory','Exploratory research: effectiveness unverified'],['research','Research use']]));const reason=field(decision,'Overall reason (optional)',el('textarea'));
 const check=el('label',undefined,'check');const confirmed=el('input');confirmed.type='checkbox';confirmed.required=true;check.append(confirmed,el('span','I have reviewed all rules, labels, applicability conditions, source evidence and retained repair outcomes for this exact version. These findings reflect my own review.'));decision.append(check);
 const submit=el('button','Submit decision','primary');submit.type='submit';decision.append(submit,el('p','Acceptance records the decision in decisions/ and activates this version. Revision or rejection does not accept it. No model call or Git commit is made.','muted'));form.append(decision);target.append(form);
 renderHistory(target,data.decisions);
 form.addEventListener('submit',async event=>{event.preventDefault();if(!form.reportValidity())return;if(choice.value==='accept'&&fields.some(f=>f.support.value!=='yes')){message('Acceptance requires a supported finding for every rule. Otherwise, request revision or reject this version.',true);return;}submit.disabled=true;try{const result=await api('/api/records/'+b.sha256+'/decision',{reviewed:confirmed.checked,decision:{reviewer:reviewer.value.trim(),decision:choice.value,reason:reason.value.trim(),scope:scope.value,rules:fields.map(f=>({rule_id:f.id,supported:f.support.value==='yes',reason:f.reason.value.trim()}))}});await library();render(await api('/api/records/'+b.sha256));message((result.decision.decision==='accept'?'Review accepted. This exact version is active.':'Review decision recorded. This action did not activate the version.')+' Saved to: '+result.directory);}catch(error){message(error.message,true);}finally{submit.disabled=false;}});
}
function renderHistory(target,rows){if(!rows.length)return;const history=el('div',undefined,'panel history');history.append(el('h3','Review history'));for(const d of rows)history.append(el('p',d.reviewer+' · '+decisionText(d.decision)+' · '+reviewedAt(d.at)+(d.reason?' · '+d.reason:'')));target.append(history);}
$('#close-evidence').addEventListener('click',()=>$('#evidence').close());
$('#review-filter').addEventListener('change',renderLibrary);
library().then(()=>selected?openRecord(selected):undefined).catch(error=>message(error.message,true));
