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
for(const id of ['detail','message','evidence','evidence-title','evidence-body','store','library','counts','review-filter','close-evidence'])roots[id]=new Element('div');
roots['review-filter'].value='all';
const document={createElement:tag=>new Element(tag),querySelector:s=>roots[s.slice(1)],querySelectorAll:()=>[]};
let posted;
const fetch=async(path,options={})=>{
 if(options.method==='POST'){posted=JSON.parse(options.body);return {ok:true,json:async()=>({default_active:false,directory:'/synthetic/decisions'})};}
 return {ok:true,json:async()=>path==='/api/library'?{store:'/synthetic/memory',records:[]}:input.data};
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
 console.log('incremental DOM passed: one explicit rule, six parent references, full-review toggle, exact base sent');
}
main().catch(error=>{console.error(error);process.exitCode=1;});
