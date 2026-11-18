'use strict';
const path=require('path'),candidate=path.resolve(process.argv[2]),schedule=process.argv[3];const assertions=[],trace=[];let adapter,error=null;
const check=(id,actual,expected)=>assertions.push({id,passed:JSON.stringify(actual)===JSON.stringify(expected),actual,expected});const settle=()=>new Promise(r=>setImmediate(r));
(async()=>{try{
 const runtime=require('./adapter.json').runtime;if(['java','php','ruby','go'].includes(runtime)){const l=require('./native-launch.cjs').launch(candidate,__dirname);adapter=require('./bridge.cjs')(l.command,{env:l.env});}else adapter=await require('./framework-loader.cjs').load(candidate);
 let acknowledge,abortRead;const cleanupGate=new Promise(r=>acknowledge=r);let open=false,closes=0,closeEntered=false,blocked=false;const seen=[];
 async function* producer(){open=true;try{for(const row of [11,29,47]){if(schedule==='cancel-scan'&&row===29){blocked=true;await new Promise((_,reject)=>abortRead=()=>{const e=Error('cancelled');e.cancelled=true;reject(e);});}seen.push(row);yield row;}}finally{closeEntered=true;trace.push({type:'cleanup-entered'});await cleanupGate;open=false;closes++;trace.push({type:'cleanup-acknowledged'});}}
 const retained=producer();const records={next:()=>retained.next(),aclose:()=>retained.return(),abort:()=>{if(abortRead)abortRead();}};
 const predicate=row=>{if(schedule==='predicate-error')throw Error('predicate failed');return schedule==='early-match'&&row===11;};
 const config={predicateError:schedule==='predicate-error',match:schedule==='early-match'?11:null};
 const a=adapter.createController(config,{records,predicate,next:()=>records.next().catch(e=>({done:false,cancelled:!!e.cancelled})),close:()=>records.aclose(),cancelInput:()=>records.abort()});a.call('start');
 for(let i=0;i<15&&!closeEntered&&!blocked&&!a.call('snapshot').done;i++)await settle();if(schedule==='cancel-scan'){check('cancel-at-real-suspended-read',blocked,true);a.call('cancel');await settle();}
 for(let i=0;i<10&&!closeEntered&&!a.call('snapshot').done;i++)await settle();const before=a.call('snapshot');check('cleanup-entered-before-completion',closeEntered,true);check('completion-waits-for-cleanup-ack',before.done,false);check('resource-still-owned-at-gate',open,true);acknowledge();
 for(let i=0;i<15&&!a.call('snapshot').done;i++)await settle();const outcome=a.call('snapshot');check('operation-completes',outcome.done,true);check('resource-closed-at-completion',open,false);check('cleanup-exactly-once',closes,1);check('original-terminal-kind',outcome.kind,schedule==='cancel-scan'?'cancelled':schedule==='predicate-error'?'error':'return');
 if(schedule==='early-match'){check('selected-row-preserved',outcome.value,11);check('no-extra-consumption',seen,[11]);}if(schedule==='exhaustion'){check('absence-preserved',outcome.value,null);check('all-rows-consumed',seen,[11,29,47]);}if(schedule==='predicate-error')check('original-error-message',outcome.message,'predicate failed');
 // Oracle cleanup occurs only after recorded operation observations.
 await retained.return();a.dispose();
 }catch(e){error=String(e.stack||e);}finally{if(adapter)adapter.finish();}process.stdout.write(JSON.stringify({schedule,passed:error===null&&assertions.length>0&&assertions.every(a=>a.passed),runtimeError:error,assertions,trace})+'\n');})();
