'use strict';
const path=require('path');const candidate=path.resolve(process.argv[2]),schedule=process.argv[3];const assertions=[],trace=[];let adapter,error=null,scopeMigrated=false;
const check=(id,actual,expected)=>assertions.push({id,passed:JSON.stringify(actual)===JSON.stringify(expected),actual,expected});const settle=()=>new Promise(r=>setImmediate(r));
(async()=>{try{
 const runtime=require('./adapter.json').runtime;if(['java','python3','php','ruby','go'].includes(runtime)){const launch=require('./native-launch.cjs').launch(candidate,__dirname);adapter=require('./bridge.cjs')(launch.command,{env:launch.env});}else adapter=await require('./framework-loader.cjs').load(candidate);
 let next=0,now=0;const timers=new Map(),requests=[];
 const clock={schedule(fn,delay){const id=++next;timers.set(id,{fn,at:now+delay});trace.push({type:'schedule',id,at:now+delay});return id;},cancel(id){timers.delete(id);trace.push({type:'cancel',id});return null;}};
 function create(background=false){return adapter.createController({background,token:background?'export-a':'file-a'},{...clock,check(token){trace.push({type:'request',token});return new Promise(resolve=>requests.push({token,resolve}));}});}
 async function response(ready,index=0){const r=requests.splice(index,1)[0];if(!r){check('expected-real-request',false,true);return;}trace.push({type:'response',token:r.token,ready});r.resolve(ready);await settle();}
 async function tick(){now+=10;for(const [id,t]of [...timers])if(t.at<=now){timers.delete(id);t.fn();}await settle();}
 const background=schedule.startsWith('background-'),a=create(background),snap=()=>a.call('snapshot');a.call('start');check('request-entry-loading',snap().loading,true);
 if(schedule==='active-pending-pending-ready'||schedule==='background-active'){
  for(let n=0;n<2;n++){await response(false);check('pending-stays-loading',snap().loading,true);check('pending-not-delivered',snap().completed,[]);check('pending-schedules-retry',snap().retryScheduled,true);await tick();}
  await response(true);check('three-actual-checks',snap().checkCount,3);check('one-ready-delivery',snap().completed,[background?'export-a':'file-a']);check('ready-clears-loading',snap().loading,false);check('ready-no-retry',timers.size,0);
 }else if(schedule==='close-before-pending-response'||schedule==='close-before-ready-response'){
  a.call('close');check('close-clears-loading',snap().loading,false);await response(schedule==='close-before-ready-response');await tick();check('retired-output-silent',snap().completed,[]);check('retired-no-timer',timers.size,0);check('retired-no-new-check',snap().checkCount,1);check('retired-no-retry-flag',snap().retryScheduled,false);
 }else if(schedule==='close-reopen-old-ready-first'){
  a.call('close');a.call('reopen','file-b');await response(true);check('old-response-no-delivery',snap().completed,[]);check('current-request-remains-loading',snap().loading,true);await response(true);check('new-generation-only',snap().completed,['file-b']);
 }else if(schedule==='close-scheduled-retry'){
  await response(false);a.call('close');check('actual-retry-cancelled',timers.size,0);await tick();check('closed-check-count',snap().checkCount,1);check('closed-loading',snap().loading,false);check('closed-output',snap().completed,[]);
 }else if(schedule==='dispose-inflight'){
  a.dispose();await response(true);check('unmount-no-final-delivery',snap().completed,[]);await tick();check('unmount-no-timer',timers.size,0);
 }else if(schedule==='background-close-policy'){
  a.call('close');await response(false);await tick();if(requests.length)await response(true);const state=snap();scopeMigrated=JSON.stringify(state.completed)==='[]'&&state.loading===false&&state.retryScheduled===false&&state.checkCount===1;
  check('complete-consumer-policy',scopeMigrated||JSON.stringify(state.completed)==='["export-a"]'&&state.loading===false&&state.checkCount===2,true);
 }else throw Error(schedule);
 a.dispose();check('dispose-clears-timers',timers.size,0);
 }catch(e){error=String(e.stack||e);}finally{if(adapter)adapter.finish();}process.stdout.write(JSON.stringify({schedule,passed:error===null&&assertions.length>0&&assertions.every(a=>a.passed),runtimeError:error,assertions,trace,scopeMigrated})+'\n');})();
