'use strict';
const path=require('path');
async function main(candidate,surface,scenario,variant){
 const config=require('./adapter.json');
 const assertions=[];let api,flush,resolve,fire,inspect,unmount,stop=()=>{};
 if(['java','python3','php','ruby','go'].includes(config.runtime)){
  const launch=require('./native-launch.cjs').launch(candidate,__dirname),bridge=require('./bridge.cjs').connect(launch.command,launch.env),req=bridge.request;
  req('init',surface,surface==='download'?'package-a':'workspace-export');
  api={};for(const name of ['start','close','reopen','snapshot'])api[name]=(...a)=>req(name,...a);
  flush=async action=>{if(action)action();req('drain');};resolve=(index,ready)=>req('resolve',index,ready);
  fire=()=>req('fire');inspect=()=>req('inspect');unmount=()=>req('unmount');stop=()=>bridge.stop();
 }else{
  const requests=[],retries=new Map();let serial=0,published=0;
  const host={check(token){let resolve;const promise=new Promise(accept=>resolve=accept);requests.push({token,resolve});return promise;},schedule(fn){retries.set(++serial,fn);return serial;},cancel(id){retries.delete(id);},publish(){published++;}};
  const mounted=await require('./framework-loader.cjs').mount(candidate,config,host,surface,surface==='download'?'package-a':'workspace-export');
  ({api,flush,unmount}=mounted);resolve=(index,ready)=>{if(!requests[index])throw new Error('request absent '+index);requests[index].resolve(ready);};
  fire=()=>{const first=[...retries.entries()][0];if(!first)return false;retries.delete(first[0]);first[1]();return true;};
  inspect=()=>({state:api.snapshot(),requests:requests.map(x=>x.token),timers:retries.size,published});stop=mounted.closeDOM;
 }
 const copy=value=>JSON.parse(JSON.stringify(value)),state=()=>copy(api.snapshot()),eq=(x,y)=>JSON.stringify(x)===JSON.stringify(y);
 const check=(id,actual,expected)=>assertions.push({id,passed:eq(actual,expected),actual,expected});
 const foreground=surface==='download',cancels=foreground||variant==='granted',token=foreground?'package-a':'workspace-export';
 const record={initial:state()};let disposed=false;
 await flush(()=>api.start());
 if(scenario==='pending-then-ready'||scenario==='long-pending'){
  const count=scenario==='long-pending'?4:2;
  for(let index=0;index<count;index++){
   await flush(()=>resolve(index,false));
   const s=state();if(index===0)record.afterFirstPending=s;if(index===1)record.afterSecondPending=s;
   check('poll-pending-keeps-loading-'+index,{loading:s.loading,retryScheduled:s.retryScheduled,completed:s.completed},{loading:true,retryScheduled:true,completed:[]});
   check('one-retry-queued-'+index,inspect().timers,1);
   let fired;await flush(()=>{fired=fire();});
   check('pending-produces-actual-next-check-'+index,fired,true);
   if(index===0)record.firstRetryFired=fired;if(index===1)record.secondRetryFired=fired;
   if(!fired)break;
  }
  if(inspect().requests.length===count+1)await flush(()=>resolve(count,true));
  check('ready-delivers-once',state().completed,[token]);check('ready-clears-loading',state().loading,false);check('ready-removes-timers',inspect().timers,0);
  check('entry-token-used-for-every-check',inspect().requests,Array(count+1).fill(token));
 }else if(scenario==='close-pending'||scenario==='close-ready'||scenario==='close-queued-ready'){
  if(scenario==='close-queued-ready')resolve(0,true);
  await flush(()=>api.close());record.afterClose=state();const before=copy(inspect());
  if(scenario!=='close-queued-ready')await flush(()=>resolve(0,scenario==='close-ready'));
  record.afterResponse=state();let fired;await flush(()=>{fired=fire();});record.retryFired=fired;
  if(!cancels&&fired)await flush(()=>resolve(1,true));
  check('surface-is-hidden',state().visible,false);
  if(cancels){
   check('owner-close-clears-loading',record.afterClose.loading,false);
   check('closed-response-does-not-deliver-or-retry',{completed:state().completed,timers:inspect().timers,retryFired:fired},{completed:[],timers:0,retryFired:false});
   check('closed-response-cannot-publish',inspect().published,before.published);
  }else{check('workspace-close-preserves-delivery',state().completed,[token]);check('workspace-close-allows-pending-retry',scenario==='close-ready'?true:fired,true);}
 }else if(scenario==='close-scheduled'||scenario==='dispose-scheduled'){
  await flush(()=>resolve(0,false));check('pending-has-timer-before-retirement',inspect().timers,1);
  if(scenario==='dispose-scheduled'){await flush(unmount);disposed=true;}else await flush(()=>api.close());
  const before=copy(inspect());let fired;await flush(()=>{fired=fire();});
  if(!cancels&&!disposed){if(fired)await flush(()=>resolve(1,true));check('workspace-timer-survives-panel-close',fired,true);check('workspace-scheduled-delivery',state().completed,[token]);}
  else {check('retirement-removes-physical-timer',before.timers,0);check('retired-timer-cannot-fire',fired,false);check('retired-timer-makes-no-request',inspect().requests,before.requests);}
 }else if(scenario==='reopen-stale'||scenario==='reopen-same-token'||scenario==='reopen-reverse'){
  await flush(()=>api.close());const next=scenario==='reopen-same-token'?token:'package-b';await flush(()=>api.reopen(next));
  if(scenario==='reopen-reverse'){
   await flush(()=>resolve(1,true));const before=copy(inspect());await flush(()=>resolve(0,false));
   check('old-pending-after-new-ready-is-inert',inspect(),before);
  }else{
   await flush(()=>resolve(0,true));record.afterStale=state();
   check('old-ready-cannot-complete-new-generation',{loading:state().loading,completed:state().completed,timers:inspect().timers},{loading:true,completed:[],timers:0});
   await flush(()=>resolve(1,true));
  }
  check('current-generation-delivers-once',state().completed,[next]);check('current-ready-clears-loading',state().loading,false);
  check('reopen-captures-current-token',inspect().requests,[token,next]);
 }else if(scenario==='dispose-inflight'){
  await flush(unmount);disposed=true;const before=copy(inspect());await flush(()=>resolve(0,false));check('disposed-pending-response-is-inert',inspect(),before);
 }else if(scenario==='immediate-ready'){
  await flush(()=>resolve(0,true));check('single-ready-one-delivery',state().completed,[token]);check('single-ready-one-request',state().checkCount,1);check('single-ready-no-retry',inspect().timers,0);
 }else if(scenario==='multi-reopen'){
  await flush(()=>api.reopen('package-b'));await flush(()=>api.reopen('package-c'));await flush(()=>resolve(2,true));const before=copy(inspect());
  await flush(()=>resolve(0,true));await flush(()=>resolve(1,false));check('all-earlier-generations-inert',inspect(),before);check('latest-token-is-owner',state().completed,['package-c']);
 }else if(scenario==='background-closed-restart'||scenario==='background-repeat-start'){
  if(scenario==='background-closed-restart')await flush(()=>api.close());
  await flush(()=>api.start());
  record.afterRepeatedStart=state();
  check('background-start-preserves-panel-visibility',state().visible,scenario==='background-repeat-start'||variant==='granted');
  await flush(()=>resolve(0,true));
  record.afterEarlierResponse=state();
  check('workspace-earlier-response-remains-owned',state().completed,variant==='granted'?[]:[token]);
  await flush(()=>resolve(1,true));
  check('workspace-repeat-start-deduplicates-token',state().completed,[token]);
  check('workspace-repeat-start-two-service-calls',inspect().requests,[token,token]);
  check('workspace-repeat-start-no-timers',inspect().timers,0);
 }else throw new Error('unknown scenario '+scenario);
 if(!disposed&&!['java','python3','php','ruby','go'].includes(config.runtime)){const node=document.querySelector('section');check('framework-rendered-state',{visible:node?.dataset.visible,loading:node?.dataset.loading},{visible:String(state().visible),loading:String(state().loading)});}
 record.final=state();record.requests=inspect().requests;record.timers=inspect().timers;
 record.assertions=assertions;record.passed=assertions.every(a=>a.passed);record.runtimeError=null;
 if(!disposed)await flush(unmount);stop();
 return record;
}
module.exports=main;
if(require.main===module)main(path.resolve(process.argv[2]),process.argv[3],process.argv[4],process.argv[5]).then(record=>process.stdout.write(JSON.stringify(record))).catch(error=>{process.stderr.write((error.stack||String(error))+'\n');process.exitCode=2;});
