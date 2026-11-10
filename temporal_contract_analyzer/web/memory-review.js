'use strict';
const $ = selector => document.querySelector(selector);
const names = {'subscription-retirement':'订阅退休与延迟审计','paused-shared-work':'共享工作与取消恢复','deferred-boundary-binding':'延迟编辑与边界结算'};
const categories = {applicability:'适用条件',event_relation:'事件关系',preservation:'必须保留的行为',exclusion:'使用边界',verification:'验证方法'};
let selected = new URLSearchParams(location.search).get('record');
let current;
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
  for(const finding of value.labels){const box=el('div',undefined,'evidence-finding');box.append(el('h3',finding.code+' · '+finding.basis),el('p',finding.reason));for(const anchor of finding.evidence||[]){box.append(el('p',anchor.file.split('/').pop()+' : '+anchor.line,'meta'),el('blockquote',anchor.quote));if(current.audit.sources.some(s=>s.sha256===anchor.sha256))box.append(button('查看原文上下文',()=>showEvidence(anchor.sha256,'',anchor.line)));}body.append(box);}
  for(const note of value.notes||[])body.append(el('p',note,'notice'));
 }else body.append(el('pre',data.text));
 if(data.truncated)body.append(el('p','显示已截取；完整证据保留在经验库 sources/ 中。','notice'));
 if(!$('#evidence').open)$('#evidence').showModal();
}
async function library(){
 const data=await api('/api/library');$('#store').textContent=data.store;const list=$('#library');list.replaceChildren();
 const records=data.records.sort((a,b)=>Number(b.latest)-Number(a.latest)||a.id.localeCompare(b.id));
 if(!records.length){list.append(el('p','这个库还没有经验版本。','muted'));return;}
 for(const item of records){const b=button('',()=>openRecord(item.sha256));b.className='version'+(item.sha256===selected?' selected':'');b.append(el('strong',names[item.id]||item.id),el('span',item.labels.join(' / ')+' · '+(item.active?'已激活':item.status==='candidate'?'候选待审':'历史版本'),'meta'),el('small',item.version));b.dataset.sha=item.sha256;list.append(b);}
}
async function openRecord(code){
 const data=await api('/api/records/'+code);current=data.bundle;selected=code;history.replaceState(null,'','/?record='+code);render(data);for(const b of document.querySelectorAll('.version'))b.classList.toggle('selected',b.dataset.sha===code);message('');
}
function render(data){
 const b=data.bundle;const target=$('#detail');target.replaceChildren();const intro=el('div',undefined,'panel');intro.append(el('h2',names[b.id]||b.id),el('p',b.version,'meta'),el('code',b.sha256),el('p',b.labels.join(' / '),'meta'),el('p','审核这份准确版本的规则、标签、适用前提与原始证据。接受表示允许研究使用，修复收益仍需实验验证。','notice'));target.append(intro);
 const meta=el('div',undefined,'metadata');for(const [key,title] of [['requires','必须有证据支持的机制前提'],['excludes','必须被明确否定的排除机制']]){const box=el('div');box.append(el('h3',title));const ul=el('ul');for(const v of b[key])ul.append(el('li',data.predicates?.[v]||v));if(!b[key].length)ul.append(el('li','未登记；仍需核查规则正文中的使用边界。'));box.append(ul);meta.append(box);}intro.append(meta);
 const limitations=el('details');limitations.append(el('summary','查看审核来源与限制'));limitations.append(el('pre',JSON.stringify(b.review,null,2)));intro.append(limitations);
 const form=el('form');form.id='review-form';const fields=[];
 for(const rule of b.rules){const box=el('article',undefined,'rule');box.append(el('h3',rule.id+' · '+categories[rule.category]),el('p',rule.body,'body'));const evidence=el('div',undefined,'actions');for(const link of b.audit.rule_links.filter(l=>l.rule_id===rule.id)){const title=sourceName(link.source_sha256);evidence.append(button((title==='label-review.json'?'查看逐规则标签依据':title)+' '+link.pointer,()=>showEvidence(link.source_sha256,link.pointer)));}box.append(evidence);const support=field(box,'这条规则及其标签、边界是否有依据？',select([['','请选择'],['yes','有依据'],['no','不支持或证据不足']]));support.required=true;const reason=field(box,'审核理由（选填）',el('textarea'));fields.push({id:rule.id,support,reason});form.append(box);}
 const all=el('details',undefined,'panel');all.append(el('summary','库内全部来源：任务、源码、审核与结果'));const links=el('div',undefined,'actions');for(const source of b.audit.sources)links.append(button(source.path.split('/').pop(),()=>showEvidence(source.sha256)));all.append(links);form.append(all);
 const decision=el('div',undefined,'panel');decision.append(el('h2','提交这份版本的审核决定'));const reviewer=field(decision,'实际审核人姓名',el('input'));reviewer.required=true;reviewer.autocomplete='name';const choice=field(decision,'整体决定',select([['','请选择'],['accept','接受并激活'],['revise','需要修订，暂不激活'],['reject','拒绝此版本']]));choice.required=true;const scope=field(decision,'使用范围',select([['exploratory','探索性研究：效果尚待验证'],['research','研究使用']]));const reason=field(decision,'整体理由（选填）',el('textarea'));
 const check=el('label',undefined,'check');const confirmed=el('input');confirmed.type='checkbox';confirmed.required=true;check.append(confirmed,el('span','我已核对上方准确版本的全部规则、标签、适用条件和原始依据；这些判断是我的实际审核意见。'));decision.append(check);
 const submit=el('button','提交审核决定','primary');submit.type='submit';decision.append(submit,el('p','接受后自动写入 decisions/ 并激活；修订或拒绝只记录决定。不会调用模型或创建 Git 提交。','muted'));form.append(decision);target.append(form);
 if(data.decisions.length){const history=el('div',undefined,'panel history');history.append(el('h3','此版本已有审核记录'));for(const d of data.decisions)history.append(el('p',d.reviewer+' · '+d.decision+' · '+d.reason));target.append(history);}
 form.addEventListener('submit',async event=>{event.preventDefault();if(!form.reportValidity())return;if(choice.value==='accept'&&fields.some(f=>f.support.value!=='yes')){message('接受前，每条规则都必须确认为有依据；否则请选择修订或拒绝。',true);return;}submit.disabled=true;try{const result=await api('/api/records/'+b.sha256+'/decision',{reviewed:confirmed.checked,decision:{reviewer:reviewer.value.trim(),decision:choice.value,reason:reason.value.trim(),scope:scope.value,rules:fields.map(f=>({rule_id:f.id,supported:f.support.value==='yes',reason:f.reason.value.trim()}))}});await library();message((result.decision.decision==='accept'?'审核已接受，准确版本已激活。':'审核决定已记录，此操作未激活版本。')+' 保存位置：'+result.directory);form.reset();}catch(error){message(error.message,true);}finally{submit.disabled=false;}});
}
$('#close-evidence').addEventListener('click',()=>$('#evidence').close());
library().then(()=>selected?openRecord(selected):undefined).catch(error=>message(error.message,true));
