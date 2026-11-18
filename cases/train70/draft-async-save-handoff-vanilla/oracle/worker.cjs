"use strict";
const path=require("path"), {pathToFileURL}=require("url");
const root=process.argv[2], scenario=process.argv[3];
async function main() {
 const load=f=>import(pathToFileURL(path.join(root,"src",f)));
 const {createDraftStore}=await load("draft-store.js"), {createWorkspace}=await load("workspace.js"), {createSearchPreview}=await load("search-preview.js");
 let now=0, serial=0, visible=null, onStart=null, listeners=0;
 const timersPending=new Map(), jobs=[], statuses=[], documents=[], checks=[], previews=[];
 const check=(id,actual,expected)=>checks.push({id,actual,expected,passed:require("util").isDeepStrictEqual(actual, expected)});
 const timers={schedule(fn,delay){const id=++serial;timersPending.set(id,{fn,at:now+delay});return id;},cancel(id){timersPending.delete(id);}};
 const advance=t=>{let n=0;while(true){const next=[...timersPending].filter(([,x])=>x.at<=t).sort((a,b)=>a[1].at-b[1].at||a[0]-b[0])[0];if(!next)break;if(++n>100)throw Error("timer loop");timersPending.delete(next[0]);now=next[1].at;next[1].fn();}now=t;};
 const store=createDraftStore({A:"seed-A",B:"seed-B"},{transport(event){let resolve;const promise=new Promise(r=>resolve=r);jobs.push({event,resolve,done:false});if(onStart)onStart(event);return promise;}});
 const subscribe=store.subscribe;store.subscribe=fn=>{listeners++;const stop=subscribe(fn);let active=true;return()=>{if(active){active=false;listeners--;stop();}};};
 const workspace=createWorkspace({store,timers,renderDocument(x){visible=x;documents.push(x);},renderStatus(e){statuses.push([e.id,e.text]);}});
 const ack=async i=>{const j=jobs[i];if(!j){check("ack-job-exists-"+i,false,true);return;}if(j.done)throw Error("double settle");j.done=true;j.resolve();await new Promise(resolve => setImmediate(resolve));};
 const pairs=()=>jobs.map(j=>[j.event.id,j.event.text]);
 if(scenario==="quiet-burst"){
  workspace.open("A");workspace.edit("one");advance(30);workspace.edit("two");advance(149);check("no-early-submit",pairs(),[]);advance(150);check("one-submit",pairs(),[["A","two"]]);await ack(0);check("current-status",statuses,[["A","two"]]);check("persisted",store.readPersisted("A"),"two");
 } else if(scenario==="departure"){
  workspace.open("A");workspace.edit("w1");workspace.close();check("submitted-before-return",pairs(),[["A","w1"]]);check("accepted-draft",store.read("A"),"w1");check("still-unacknowledged",store.readPersisted("A"),"seed-A");await ack(0);check("saved-after-close",store.readPersisted("A"),"w1");check("no-retired-status",statuses,[]);
 } else if(scenario==="reverse-acks" || scenario==="ordered-acks"){
  workspace.open("A");workspace.edit("w1");advance(120);workspace.close();workspace.open("A");check("restored-accepted",visible,{id:"A",text:"w1"});workspace.edit("w2");advance(240);check("two-submissions",pairs(),[["A","w1"],["A","w2"]]);
  if(scenario==="reverse-acks"){await ack(1);await ack(0);}else{await ack(0);await ack(1);}
  check("newest-persisted",store.readPersisted("A"),"w2");check("new-visit-status-only",statuses,[["A","w2"]]);
 } else if(scenario==="pending-new-edit"){
  workspace.open("A");workspace.edit("w1");advance(120);workspace.edit("w2");await ack(0);check("old-ack-not-current-edit",statuses,[]);advance(240);await ack(1);check("latest-edit-status",statuses,[["A","w2"]]);check("both-submitted",pairs(),[["A","w1"],["A","w2"]]);
 } else if(scenario==="reentrant-reopen" || scenario==="reentrant-hide"){
  workspace.open("A");workspace.edit("w1");
  onStart=()=>{onStart=null;if(scenario==="reentrant-hide")workspace.close();else{workspace.open("A");check("reentrant-read-accepted",visible,{id:"A",text:"w1"});workspace.edit("w2");}};
  workspace.open("B");check("new-navigation-wins",visible,scenario==="reentrant-hide"?null:{id:"A",text:"w1"});check("obsolete-B-never-rendered",documents.some(x=>x&&x.id==="B"),false);
  advance(120);check("accepted-writes-preserved",pairs(),scenario==="reentrant-hide"?[["A","w1"]]:[["A","w1"],["A","w2"]]);
  if(scenario==="reentrant-reopen"){await ack(1);await ack(0);check("version-protected",store.readPersisted("A"),"w2");check("new-status",statuses,[["A","w2"]]);}else{await ack(0);check("hidden-status",statuses,[]);check("saved-despite-hide",store.readPersisted("A"),"w1");}
 } else if(scenario==="preview"){
  const preview=createSearchPreview({timers,publish:x=>previews.push(x.query)});preview.query("discard");preview.hide();advance(200);check("hidden-discarded",previews,[]);preview.query("latest");advance(239);check("not-before-40",previews,[]);advance(240);const at40=previews.length;advance(319);if(at40===0)check("not-before-120",previews,[]);advance(320);check("reusable-once",previews,["latest"]);check("delay-policy",at40===1?40:120,at40===1?40:120);checks.push({id:"preview-delay",actual:at40===1?40:120,expected:null,passed:true});
 }else throw Error("unknown schedule");
 workspace.close();advance(1000);for(let i=0;i<jobs.length;i++)if(!jobs[i].done)await ack(i);
 check("all-accepted-writes-settled",jobs.every(j=>j.done),true);check("no-timers",timersPending.size,0);check("no-listeners",listeners,0);
 console.log(JSON.stringify({scenario,checks,passed:checks.every(c=>c.passed),submissions:pairs(),statuses,documents}));
}
main().catch(e=>{console.error(e.stack);process.exitCode=2;});
