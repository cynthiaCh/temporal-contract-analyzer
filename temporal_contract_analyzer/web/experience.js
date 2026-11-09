'use strict';
const $=s=>document.querySelector(s);
const states={prepared:'待预分析',analyzing:'预分析中',analysis_review:'待审核 Contract 与分类',analysis_citation_review:'引用待修正',analysis_approved:'分析已审核',training:'AUTO 与反思中',candidate_review:'待审核候选经验',candidate_approved:'经验已审核，待回验',revalidating:'开发回验中',ready_to_freeze:'达到改善门槛，待冻结',frozen:'已冻结研究经验',no_improvement:'无开发改善，测试未启动',auto_passed:'两次 AUTO 已通过，停止学习',testing:'A/B 测试中',completed:'测试完成',stopped:'异常停止',cancelled:'已取消',interrupted:'服务中断',rejected:'审核拒绝'};
let selected=null,signature='',busy=false,items=[];
function el(tag,text,cls){const n=document.createElement(tag);if(text!==undefined)n.textContent=text;if(cls)n.className=cls;return n;}
async function api(path,body){const r=await fetch(path,body===undefined?{}:{method:'POST',headers:{'Content-Type':'application/json','X-TCA-Request':'local'},body:JSON.stringify(body)});const data=await r.json();if(!r.ok)throw Error(data.error||r.statusText);return data;}
function notice(error){$('#notice').textContent=error.message;$('#notice').classList.remove('hidden');}
async function mutate(path,data){if(busy)return;busy=true;$('#notice').classList.add('hidden');try{const item=await api(path,data);if(item.id){selected=item.id;location.hash=item.id;}signature='';await refresh();}catch(e){notice(e);}finally{busy=false;}}
function button(label,fn){const b=el('button',label);b.type='button';b.addEventListener('click',()=>Promise.resolve().then(fn).catch(notice));return b;}
function details(parent,label,value){const box=el('details');box.append(el('summary',label),el('pre',typeof value==='string'?value:JSON.stringify(value,null,2)));parent.append(box);}
function plan(){const test=$('#kind').value==='test';$('#parent-field').hidden=!test;$('#parent').required=test;$('#reflection-effort').disabled=test;$('#plan').textContent=test?'冻结经验后才可创建。预分析与人工审核后，固定运行 B1 / A1 / A2 / B2，共 4 次独立修复；测试不反思、不更新经验。':'预分析与人工审核 → 两次 AUTO → 一次反思 → 经验审核 → 两次开发回验 → 有改善才可冻结。最多 6 个模型会话。';}
async function refresh(){
 const data=await api('/api/experience');items=data.items;$('#active').textContent=data.active?'当前运行：'+data.active+'；其他运行需等待。':'当前无活动实验。';
 const list=$('#campaigns');list.replaceChildren();if(!items.length)list.append(el('p','暂无批次，新建后从预分析开始。','muted'));
 for(const item of items)list.append(button(`${item.kind==='test'?'测试':'开发'} · ${item.case.id} · ${states[item.status]||item.status} · ${item.id}`,()=>{location.hash=item.id;}));
 const prior=$('#parent').value;$('#parent').replaceChildren();for(const item of items.filter(x=>x.status==='frozen'&&x.kind==='development')){const o=el('option',item.case.id+' · '+item.id);o.value=item.id;$('#parent').append(o);}if(items.some(x=>x.id===prior))$('#parent').value=prior;
 selected=location.hash.slice(1)||selected;
 if(selected){const item=items.find(x=>x.id===selected)||await api('/api/experience/'+encodeURIComponent(selected));const next=JSON.stringify(item);if(signature!==next){render(item);signature=next;}}
}
function action(item,name,body={}){return mutate('/api/experience/'+item.id+'/'+name,body);}
function render(item){
 const target=$('#detail');target.hidden=false;target.replaceChildren();target.append(el('h2',`${item.kind==='test'?'冻结经验 A/B 测试':'经验开发训练'} · ${states[item.status]||item.status}`),el('p',item.case.id+' · '+item.id),el('p',item.source_relationship,'muted'));
 target.append(el('p',`模型 ${item.model} / ${item.effort}；反思 ${item.reflection_effort}；每会话 ${item.timeout} 秒。`,'muted'));
 if(item.error)target.append(el('p',item.error,'scope-notice'));
 const controls=el('div',undefined,'experience-actions');
 if(item.status==='prepared')controls.append(button('开始预分析（调用模型）',()=>action(item,'analyze')));
 if(item.status==='analysis_approved')controls.append(button(item.kind==='test'?'开始 A/B 测试（4 次修复）':'开始训练（两次 AUTO＋一次反思）',()=>action(item,item.kind==='test'?'test':'train')));
 if(item.status==='candidate_approved')controls.append(button('开始两次开发回验',()=>action(item,'revalidate')));
 if(item.status==='ready_to_freeze')controls.append(button('冻结研究经验',()=>action(item,'freeze')));
 if(['analyzing','training','revalidating','testing'].includes(item.status))controls.append(button('取消当前运行',()=>action(item,'cancel')));
 if(item.status==='frozen')controls.append(button('使用此经验新建测试',()=>{$('#kind').value='test';plan();$('#parent').value=item.id;$('#create-form').scrollIntoView({behavior:'smooth'});}));
 target.append(controls);
 if(item.citation_issues?.length){
  target.append(el('h3','引用校验问题'));
  target.append(el('p',item.status==='stopped'?'旧批次保留停止状态，以下为只读诊断，不会续跑。':'仅需修正引用；不会重新调用模型。通过引用校验后仍须单独审核 Contract。','scope-notice'));
  for(const issue of item.citation_issues){const found=issue.matching_lines.length?`逐字引用可在第 ${issue.matching_lines.join('、')} 行找到。`:'当前文件中找不到该连续片段；请对照原文重新摘取，不使用省略号拼接。';details(target,`${issue.field} · ${issue.file}:${issue.line}`,`模型引用：${issue.quote}\n声明行原文：${issue.actual_line||'（文件不存在或行号超出范围）'}${issue.actual_line_truncated?'（此处显示截取，完整正文见协议材料）':''}\n${found}`);}
 }
 if(item.analysis){details(target,'候选 Contract、七类标签及源码引用',item.analysis);}
 if(['analysis_review','analysis_citation_review','candidate_review'].includes(item.status))review(target,item);
 if(item.candidate_text)details(target,'反思经验正文（维护端接收的文本）',item.candidate_text);
 if(item.candidate)details(target,'规则依据与适用／排除条件',item.candidate);
 if(item.admission)target.append(el('p',item.admission.reason,'scope-notice'));
 if(item.route){target.append(el('p',`路由：${item.route.condition} / ${item.route.reason}`));if(item.prompts_identical)target.append(el('p','未投放经验，A/B 提示逐字相同。任何结果差异不能归因于经验。','scope-notice'));details(target,'路由前提和排除条件核查',item.route);}
 const roles=item.kind==='test'?['analysis','B1','A1','A2','B2']:['analysis','AUTO-1','AUTO-2','reflection','REVALIDATE-1','REVALIDATE-2'];
 const table=el('table');const head=el('tr');for(const name of ['槽位','执行','整题与行为','相对原始代码'])head.append(el('th',name));const thead=el('thead');thead.append(head);table.append(thead);const body=el('tbody');
 for(const role of roles){const job=item.jobs.find(j=>j.role===role);const row=el('tr');const out=job?.outcome;let score='尚未评分';if(out){const failed=new Set([...(out.missing_required_effects||[]),...(out.observed_forbidden_effects||[])]);const known=Object.entries(out.observed_effects||{}).filter(([,v])=>typeof v==='boolean');score=`${out.verdict} · ${known.filter(([k])=>!failed.has(k)).length}/${Object.keys(out.observed_effects||{}).length} 行为满足`;}const d=job?.original_delta;row.append(el('td',role),el('td',job?job.status:'未启动'),el('td',score),el('td',d?`改善 ${d.gained.join(', ')||'无'}；退步 ${d.lost.join(', ')||'无'}；未知 ${d.unknown.join(', ')||'无'}`:'—'));body.append(row);}table.append(body);const wrap=el('div',undefined,'table-wrap');wrap.append(table);target.append(wrap);
 if(item.comparisons)details(target,'每次回验相对每份 AUTO 的完整得失',item.comparisons);
 if(item.test_summary)details(target,'A/B 整题结果与相对得失（两次重复仅作描述）',{groups:item.test_summary,comparisons:item.test_comparisons});
 details(target,'完整运行记录、评分向量与审核决定',item);
 const known=item.jobs.filter(j=>j.usage);const fields=['input_tokens','cached_input_tokens','output_tokens','total_tokens'];const totals={};for(const field of fields){totals[field]={known_subtotal:known.reduce((n,j)=>n+(Number.isFinite(j.usage[field])?j.usage[field]:0),0),unknown_sessions:item.jobs.filter(j=>j.status!=='prepared'&&!Number.isFinite(j.usage?.[field])).length};}
 details(target,'CLI 返回的会话用量（缺失字段保持未知，缓存不额外相加）',totals);
 const artifacts=el('div',undefined,'artifact-buttons');const viewer=el('pre','选择材料查看原文。');const names=['protocol.json',...Object.keys(item.pinned||{})];for(const job of item.jobs){names.push('jobs/'+job.id+'/prompt.md');const base=job.artifact_root||`jobs/${job.id}/execution/jobs/${job.id}`;for(const file of ['answer.md','changes.json','events.jsonl','stderr.log'])names.push(base+'/'+file);}
 for(const name of names)artifacts.append(button(name,async()=>{const a=await api('/api/experience/'+item.id+'/artifact?name='+encodeURIComponent(name));viewer.textContent=a.exists?a.text+(a.truncated?'\n[显示截取，完整材料保存在磁盘]':''):'材料尚未生成。';}));const box=el('details');box.append(el('summary','证据、提示词、补丁和原始日志'),artifacts,viewer);target.append(box);
}
function review(target,item){
 const correcting=item.status==='analysis_citation_review';const analysis=correcting||item.status==='analysis_review';const panel=el('section',undefined,'review-panel');panel.append(el('h3',correcting?'修正引用':analysis?'审核候选分析':'审核反思经验'));
 panel.append(el('p',correcting?'仅修改 evidence 内的 file、line、quote。Contract、分类、前提和未知须保持不变；原始模型输出保留。':analysis?'仅根据当前任务与源码核对义务方向、引用、机制前提和未知范围。可修正 JSON，原始模型输出仍保留。':'逐条核对规则正文、支持依据、适用条件、保留义务与反例。不把观察当作已验证因果；审核通过后仍须开发回验。'));
 let editor;if(analysis){const label=el('label','候选分析 JSON');editor=el('textarea',undefined,'code');editor.value=JSON.stringify(item.analysis,null,2);editor.id='review-analysis';label.append(editor);panel.append(label);}
 else {details(panel,'开发证据与实际补丁', '在下方证据材料中打开 reflection-evidence.json，对照 AUTO 的完整行为、补丁与公开交付。');}
 const reasonLabel=el('label','审核依据');const reason=el('textarea');reason.id='review-reason';reason.rows=3;reason.required=true;reason.maxLength=4000;reasonLabel.append(reason);panel.append(reasonLabel);
 const checkLabel=el('label');const check=el('input');check.type='checkbox';check.id='review-confirm';checkLabel.append(check,document.createTextNode(correcting?'我已对照原文修正引用；后续仍需审核 Contract。':'我已核对以上内容；此记录为操作人的人工审核，不代表独立评审。'));panel.append(checkLabel);
 const actions=el('div',undefined,'experience-actions');
 actions.append(button(correcting?'校验引用修正（不调用模型）':'审核通过',()=>{if(!check.checked||!reason.value.trim())throw Error('请填写审核依据并确认已核对。');return action(item,correcting?'correct-citations':analysis?'review-analysis':'review-candidate',{approved:true,reason:reason.value,...(analysis?{analysis:JSON.parse(editor.value)}:{})});}));if(!correcting)actions.append(button('拒绝并停止本批',()=>{if(!reason.value.trim())throw Error('请填写拒绝依据。');return action(item,analysis?'review-analysis':'review-candidate',{approved:false,reason:reason.value});}));panel.append(actions);target.append(panel);
}
$('#kind').addEventListener('change',plan);$('#refresh').addEventListener('click',()=>refresh().catch(notice));window.addEventListener('hashchange',()=>{selected=location.hash.slice(1);signature='';refresh().catch(notice);});
$('#create-form').addEventListener('submit',event=>{event.preventDefault();mutate('/api/experience',{kind:$('#kind').value,case_id:$('#case').value,parent_id:$('#parent').value,model:$('#model').value,effort:$('#effort').value,reflection_effort:$('#reflection-effort').value,timeout:Number($('#timeout').value),source_relationship:$('#relationship').value});});
async function init(){const catalog=await api('/api/case-options');for(const item of catalog.cases){const o=el('option',(item.title||item.id)+(item.supported?'':' · '+item.unavailable_reason));o.value=item.id;o.disabled=!item.supported;$('#case').append(o);}for(const name of catalog.models||[]){const o=el('option');o.value=name;$('#models').append(o);}plan();await refresh();}
init().catch(notice);setInterval(()=>{if(!busy)refresh().catch(notice);},2000);
