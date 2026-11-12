// Synthetic DOM transport fixture; no browser dependencies, network or approvals.
'use strict';
const fs=require('node:fs'),vm=require('node:vm'),assert=require('node:assert/strict');
const input=JSON.parse(fs.readFileSync(0,'utf8'));
class Element {
 constructor(tag){this.tagName=tag;this.children=[];this.listeners={};this.dataset={};this.className='';this.value='';this.textContent='';this.checked=false;this.classList={toggle(){}};}
 append(...items){for(const item of items){this.children.push(item);if(this.tagName==='select'&&this.children.length===1)this.value=item.value;}}
 replaceChildren(...items){this.children=[];this.append(...items);}
 addEventListener(type,callback){this.listeners[type]=callback;}
 get childElementCount(){return this.children.length;}
 reportValidity(){return true;}
 showModal(){this.open=true;}
 close(){this.open=false;}
}
const roots={};
for(const id of ['detail','message','evidence','evidence-title','evidence-body','store','library','counts','review-filter','refresh-library','close-evidence'])roots[id]=new Element('div');
roots['review-filter'].value='all';
const document={createElement:tag=>new Element(tag),querySelector:s=>roots[s.slice(1)],querySelectorAll:()=>[]};
let posted,postCount=0,apiVersion='experience-review-v3';
const fetch=async(path,options={})=>{
 if(options.method==='POST'){postCount++;posted=JSON.parse(options.body);return {ok:true,json:async()=>({sha256:input.data.bundle.sha256,default_active:false,directory:'/synthetic/decisions'})};}
 return {ok:true,json:async()=>path==='/api/library'?{review_api_version:apiVersion,store:'/synthetic/memory',records:[]}:input.data};
};
const context=vm.createContext({document,fetch,location:{search:''},history:{replaceState(){}},URLSearchParams,DATA:input.data,console});
vm.runInContext(fs.readFileSync(input.source,'utf8'),context);
function all(node,predicate){return [...(predicate(node)?[node]:[]),...node.children.flatMap(child=>all(child,predicate))];}
const tag=name=>node=>node.tagName===name;
const article=node=>node.tagName==='article';
const ruleInputs=()=>all(roots.detail,article).flatMap(node=>all(node,tag('select')));
async function main(){
 await new Promise(resolve=>setImmediate(resolve));
 vm.runInContext('current=DATA.bundle;render(DATA)',context);
 assert.equal(ruleInputs().length,1,'Only the changed rule has a finding selector');
 const inherited=all(roots.detail,node=>node.className==='panel inherited-rules')[0];
 assert.equal(all(inherited,article).length,6);
 assert.equal(all(inherited,tag('select')).length,0,'No empty inherited-rule forms');
 assert.equal(all(roots.detail,node=>node.className==='rule-diff').length,1,'R02 before/after is shown');
 ruleInputs()[0].value='yes';
 all(roots.detail,article).flatMap(node=>all(node,tag('textarea')))[0].value='SYNTHETIC preserved draft';
 const detailBefore=roots.detail.children[0],postsBefore=postCount;
 await roots['refresh-library'].listeners.click();
 assert.equal(roots.detail.children[0],detailBefore,'Queue refresh does not rerender a draft');
 assert.equal(ruleInputs()[0].value,'yes');assert.equal(postCount,postsBefore,'Refresh only reads');
 apiVersion='old-api';await roots['refresh-library'].listeners.click();
 assert.match(roots.message.textContent,/older Python code/);assert.equal(postCount,postsBefore);
 apiVersion='experience-review-v3';
 let override=all(roots.detail,tag('button')).find(b=>b.textContent==='Review R03 explicitly');
 await override.listeners.click();assert.equal(ruleInputs().length,2,'Reviewer can identify an affected unchanged rule');
 assert.equal(ruleInputs()[0].value,'yes','Changing review granularity retains existing draft');
 assert.equal(all(roots.detail,article).flatMap(node=>all(node,tag('textarea')))[0].value,'SYNTHETIC preserved draft');
 override=all(roots.detail,tag('button')).find(b=>b.textContent==='Use parent finding for R03');
 await override.listeners.click();assert.equal(ruleInputs().length,1);
 let toggle=all(roots.detail,tag('button')).find(b=>b.textContent==='Review all rules instead');
 await toggle.listeners.click();assert.equal(ruleInputs().length,7,'Full review is an explicit option');
 toggle=all(roots.detail,tag('button')).find(b=>b.textContent==='Use accepted parent findings');
 await toggle.listeners.click();assert.equal(ruleInputs().length,1);
 const form=all(roots.detail,tag('form'))[0];
 ruleInputs()[0].value='yes';
 const selects=all(form,tag('select'));selects.find(s=>s.children.some(o=>o.value==='accept_only')).value='accept_only';
 const inputs=all(form,tag('input'));inputs.find(i=>i.type!=='checkbox').value='SYNTHETIC_BROWSER_REVIEWER';inputs.find(i=>i.type==='checkbox').checked=true;
 await form.listeners.submit({preventDefault(){}});
 assert.equal(posted.decision.rules.length,1);
 assert.equal(posted.decision.rules[0].rule_id,'R02');
 assert.deepEqual(posted.decision.inherit_from,input.data.review_plan.inherit_from);
 assert.equal(posted.activate,false);
 assert.equal(posted.reviewed,true);
 context.READONLY=input.readonly;vm.runInContext('current=READONLY.bundle;render(READONLY)',context);
 assert.equal(ruleInputs().length,0,'Saved review is read-only');
 assert.equal(all(roots.detail,node=>node.tagName==='p'&&node.textContent.startsWith('Inherited from parent ')).length,6,'Saved parent provenance remains visible');
 vm.runInContext('current=DATA.bundle;render(DATA)',context);
 let editor=all(roots.detail,node=>node.className==='panel manual-editor')[0];
 const beforeButton=all(editor,tag('button')).find(b=>b.textContent==='Use Before for R02');
 await beforeButton.listeners.click();
 let manualRules=all(editor,node=>node.className==='manual-rule');
 assert.equal(all(manualRules[1],tag('textarea'))[0].value,input.data.review_plan.rules[1].before.body);
 all(manualRules[1],tag('textarea'))[0].value='SYNTHETIC generalized mechanism';
 all(editor,tag('input'))[0].value='SYNTHETIC_EDITOR';
 all(editor,tag('textarea'))[0].value='SYNTHETIC edit reason';
 await all(roots.detail,tag('button')).find(b=>b.textContent==='Review all rules instead').listeners.click();
 editor=all(roots.detail,node=>node.className==='panel manual-editor')[0];
 manualRules=all(editor,node=>node.className==='manual-rule');
 assert.equal(all(manualRules[1],tag('textarea'))[0].value,'SYNTHETIC generalized mechanism','Review toggles retain manual wording');
 await all(editor,tag('button')).find(b=>b.textContent==='Save as new version').listeners.click();
 assert.equal(posted.actor,'SYNTHETIC_EDITOR');
 assert.equal(posted.reason,'SYNTHETIC edit reason');
 assert.equal(posted.rules[1].body,'SYNTHETIC generalized mechanism');
 assert.equal(posted.rules.length,7);
 assert.equal(posted.activate,undefined,'Saving wording does not request activation');
 context.DATA.workflow={ai_status:'pending',status:'ai_check_pending',validation_status:'not_started'};
 vm.runInContext('current=DATA.bundle;render(DATA)',context);
 assert.equal(all(roots.detail,tag('select')).some(s=>s.children.some(o=>o.value.startsWith('accept'))),false,'AI-pending workflow cannot offer acceptance');
 assert.ok(all(roots.detail,tag('p')).some(p=>p.textContent.includes('content acceptance waits')));
 console.log('incremental DOM passed: one explicit rule, six parent references, full-review toggle, exact base sent');
}
main().catch(error=>{console.error(error);process.exitCode=1;});
