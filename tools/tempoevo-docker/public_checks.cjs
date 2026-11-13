// Public examples derived from task/README APIs, not hidden schedules/assertions.
'use strict';
const fs=require('fs'),path=require('path'),cp=require('child_process'),assert=require('assert/strict');
const {pathToFileURL}=require('url');
const cfg=JSON.parse(fs.readFileSync('/checks/case.json','utf8')),candidate=process.argv.at(-1),oracle=path.join('/opt/swe-tempoc',path.dirname(cfg.manifest),'oracle');
const rows=[];const tick=async()=>{for(let i=0;i<12;i++)await Promise.resolve();};
async function check(name,fn){try{const actual=await fn();rows.push({check:name,passed:true,actual});}catch(e){rows.push({check:name,passed:false,actual:e.actual??null,expected:e.expected??null,error:String(e.message)});}}
function timers(){let now=0,next=0;const work=new Map();return{schedule(fn,delay){work.set(++next,{fn,at:now+delay});return next;},cancel(id){work.delete(id);},advance(ms){const end=now+ms;for(;;){const due=[...work].filter(([k,v])=>v.at<=end).sort((a,b)=>a[1].at-b[1].at||a[0]-b[0])[0];if(!due)break;work.delete(due[0]);now=due[1].at;due[1].fn();}now=end;}};}
function nativeCommand(){
 const runtime='/opt/swe-tempoc/results/student-case-expansion-runtime/native',env={...process.env,PYTHONDONTWRITEBYTECODE:'1'};
 if(cfg.runtime==='python3')return{command:['/usr/bin/python3','-B',path.join(oracle,'driver.py'),candidate],env};
 if(cfg.runtime==='php')return{command:[runtime+'/usr/bin/php7.4','-n','-d','extension='+runtime+'/usr/lib/php/20190902/json.so',oracle+'/driver.php',candidate],env};
 if(cfg.runtime==='ruby'){env.LD_LIBRARY_PATH=runtime+'/usr/lib/x86_64-linux-gnu';env.RUBYLIB=runtime+'/usr/lib/ruby/2.7.0:'+runtime+'/usr/lib/x86_64-linux-gnu/ruby/2.7.0';return{command:[runtime+'/usr/bin/ruby2.7',oracle+'/driver.rb',candidate],env};}
 const build=fs.mkdtempSync('/tmp/public-native-'),java=cfg.runtime==='java',source=java?'Workflow.java':'workflow.go',driver=java?'Driver.java':'driver.go';
 fs.copyFileSync(path.join(candidate,'src',source),path.join(build,source));fs.copyFileSync(path.join(oracle,driver),path.join(build,driver));let cmd;
 if(java){env.LD_LIBRARY_PATH='/usr/lib/jvm/java-11-openjdk-amd64/lib/jli';cmd=[runtime+'/usr/lib/jvm/java-11-openjdk-amd64/bin/javac','-d',build,build+'/'+source,build+'/'+driver];}
 else{env.GOROOT=runtime+'/usr/lib/go-1.13';env.GOCACHE='/tmp/go-cache';env.GO111MODULE='off';cmd=[env.GOROOT+'/bin/go','build','-o',build+'/public-check',build+'/'+source,build+'/'+driver];}
 const run=cp.spawnSync(cmd[0],cmd.slice(1),{env,encoding:'utf8',timeout:90000});if(run.status!==0){process.stderr.write(run.stderr||'Compiler failed');throw Error('Public candidate compilation failed; compiler receipt retained on host.');}
 return{command:java?['java','-cp',build,'Driver']:[build+'/public-check'],env};
}
async function api(){
 if(cfg.runtime==='jquery'){
  const {JSDOM}=require('/opt/swe-tempoc/.swe-tempoc/js/node_modules/jsdom');const dom=new JSDOM('<div id="view"></div>');global.window=dom.window;global.document=dom.window.document;
  const work=fs.mkdtempSync('/tmp/public-js-');fs.cpSync(candidate,work,{recursive:true});fs.symlinkSync('/opt/swe-tempoc/.swe-tempoc/js/node_modules',work+'/node_modules');
  const s=await import(pathToFileURL(work+'/src/services.js')),w=await import(pathToFileURL(work+'/src/workspace.js'));return{...s,...w,element:document.querySelector('#view')};
 }
 const launch=nativeCommand();const bridge=require(oracle+'/bridge.cjs');return cfg.family==='autosave'?bridge(launch.command,{env:launch.env}):bridge.connect(launch.command,launch.env);
}
async function autosave(a){
 function setup(){const t=timers(),docs=[],status=[],previews=[];const store=a.createDraftStore({A:'before',B:'second',C:'third'});const w=a.createWorkspace({element:a.element,store,timers:t,archive:{append(){}},renderDocument:x=>docs.push(x),renderStatus:x=>status.push(x),renderSubmission(){},onSaved(){}});return{t,docs,status,store,w,previews};}
 await check('public_quiet_burst_latest',()=>{const x=setup();x.w.open('A');x.w.edit('one');x.w.edit('two');assert.equal(x.store.read('A'),'before');x.t.advance(120);assert.equal(x.store.read('A'),'two');x.w.dispose();return{beforeQuiet:'before',afterQuiet:'two'};});
 await check('public_departure_persists_latest',()=>{const x=setup();x.w.open('A');x.w.edit('saved');x.w.open('B');assert.equal(x.store.read('A'),'saved');assert.equal(x.docs.at(-1).id,'B');x.w.dispose();return{departedText:'saved',current:'B'};});
 await check('public_nested_navigation_remains_authoritative',()=>{const x=setup();x.w.open('A');x.w.edit('saved');let entered=false;const stop=x.store.subscribe(event=>{if(!entered&&event.id==='A'){entered=true;x.w.open('B');}});x.w.open('C');assert.equal(entered,true);assert.equal(x.docs.at(-1).id,'B');stop();x.w.dispose();return{current:'B'};});
 await check('public_preview_discard_and_reuse',()=>{const x=setup(),t=x.t,values=[];const preview=a.createSearchPreview({timers:t,publish:x=>values.push(x.query)});preview.query('discard');preview.hide();t.advance(80);assert.deepEqual(values,[]);preview.query('keep');t.advance(40);assert.deepEqual(values,['keep']);return values;});
}
async function query(a){
 await check('public_initial_paused_departure',async()=>{const calls=[],c=a.createClient({timers:timers(),queryFn:ctx=>{calls.push(ctx.key);return Promise.resolve('value');}},{online:false});const h=c.subscribe('A');assert.equal(c.snapshot('A').fetchStatus,'paused');c.unsubscribe(h);c.online(true);await tick();assert.deepEqual(calls,[]);c.dispose();return{requests:0};});
 await check('public_shared_observer_keeps_work',async()=>{const calls=[],c=a.createClient({timers:timers(),queryFn:ctx=>{calls.push(ctx.key);return Promise.resolve('value');}},{online:false});const first=c.subscribe('A'),second=c.subscribe('A');c.unsubscribe(first);c.online(true);await tick();assert.deepEqual(calls,['A']);assert.equal(c.snapshot('A').data,'value');c.unsubscribe(second);c.dispose();return{requests:1,data:'value'};});
 await check('public_unconsumed_active_result_retained',async()=>{let finish;const c=a.createClient({timers:timers(),queryFn:()=>new Promise(resolve=>finish=resolve)});const h=c.subscribe('A');c.unsubscribe(h);finish('retained');await tick();assert.equal(c.snapshot('A').data,'retained');c.dispose();return{data:'retained'};});
}
async function transfer(a){
 function feed(initial,decode=x=>x){const target=new EventTarget();const emit=packet=>{const event=new Event('progress');event.detail=packet;target.dispatchEvent(event);};return{target,decode,emit,start(){if(initial!==undefined)emit(initial);}};}
 function setup(){const shown=[],audit=[],records=[];const w=a.createTransferWorkspace({transport(){},onCancel(){},record:x=>records.push(x),showQueued(){},recordProgress:x=>audit.push(x),showProgress:x=>shown.push(x)});return{w,shown,audit,records};}
 await check('public_initial_cached_progress',()=>{const x=setup();x.w.select({id:'A',progressFeed:feed({loaded:1})});assert.deepEqual(x.shown.map(x=>x.frame.loaded),[1]);x.w.dispose();return{shown:[1]};});
 await check('public_out_of_order_display_with_retained_audit',async()=>{const pending=[],f=feed(undefined,p=>new Promise(resolve=>pending.push(()=>resolve(p)))),x=setup();x.w.select({id:'A',progressFeed:f});f.emit({loaded:1});f.emit({loaded:2});pending[1]();await tick();pending[0]();await tick();assert.deepEqual(x.shown.map(x=>x.frame.loaded),[2]);assert.deepEqual(x.audit.map(x=>x.frame.loaded),[2,1]);x.w.dispose();return{shown:[2],audit:[2,1]};});
 await check('public_queue_shape_preserved',()=>{const x=setup();x.w.select({id:'A',size:10});assert.deepEqual(x.records,[{fileId:'A',attemptId:1,visitId:1,kind:'select'}]);x.w.dispose();return x.records;});
}
(async()=>{let a;try{a=await api();if(cfg.family==='autosave')await autosave(a);else if(cfg.family==='query')await query(a);else await transfer(a);a.close?.();console.log(JSON.stringify({passed:rows.every(x=>x.passed),observations:rows,regressions:rows.filter(x=>!x.passed&&(cfg.baseline_passed_checks||[]).includes(x.check)),unknowns:['Public examples are not exhaustive; gold is independent.']}));process.exit(0);}catch(e){console.log(JSON.stringify({valid:false,passed:false,error:String(e.message),failure_type:'infrastructure_error'}));process.exit(0);}})();
