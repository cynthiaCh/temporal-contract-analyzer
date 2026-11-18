'use strict';
const {spawnSync}=require('child_process'),path=require('path'),fs=require('fs');
const root=path.resolve(process.argv[2]||''),variant=process.argv[3]||'ungranted';
if(!['ungranted','granted'].includes(variant))throw new Error('unsupported variant');
const routes=require('./dispatch.json');
const specification=require('./schedules.json'),definition=require('./effects.json'),schedules={},effects={};
async function main(){
for(const item of specification.schedules){
 try {schedules[item.id]=await require('./worker.cjs')(root,routes[item.id].surface,routes[item.id].scenario,variant);effects[item.id]=schedules[item.id].passed;}
 catch(error){schedules[item.id]={passed:false,runtimeError:error.stack||String(error),assertions:[]};effects[item.id]=false;}
}
const p=schedules['active-pending-pending-ready'],cp=schedules['close-before-pending-response'],cr=schedules['close-before-ready-response'],r=schedules['close-reopen-old-ready-first'],ba=schedules['background-active-pending-pending-ready'],bc=schedules['background-close-before-pending-response'];
const exact=(x,y)=>JSON.stringify(x)===JSON.stringify(y);
Object.assign(effects,{
 'download-waits-after-pending':p.afterFirstPending?.loading===true&&p.afterFirstPending?.retryScheduled===true&&exact(p.afterFirstPending?.completed,[]),
 'download-retries-until-ready-once':p.firstRetryFired===true&&p.secondRetryFired===true&&p.final?.checkCount===3&&exact(p.final?.completed,['package-a']),
 'download-close-clears-loading':cp.afterClose?.visible===false&&cp.afterClose?.loading===false,
 'download-close-ignores-pending':cp.afterResponse?.retryScheduled===false&&cp.retryFired===false&&exact(cp.final?.completed,[]),
 'download-close-ignores-ready':exact(cr.final?.completed,[]),
 'download-reopen-ignores-old-ready':r.afterStale?.loading===true&&exact(r.afterStale?.completed,[]),
 'download-reopen-current-completes-once':r.final?.loading===false&&exact(r.final?.completed,['package-b']),
 'background-active-retries-to-ready':ba.final?.checkCount===3&&exact(ba.final?.completed,['workspace-export']),
 'background-start-policy-migrated':schedules['background-closed-restart'].afterRepeatedStart?.visible===true||JSON.stringify(schedules['background-repeat-start'].afterEarlierResponse?.completed)==='[]',
 'background-continuation-policy-violated':!exact(bc.final?.completed,['workspace-export']),
 'background-close-cancels-work':bc.afterClose?.loading===false&&bc.afterResponse?.retryScheduled===false&&bc.retryFired===false&&exact(bc.final?.completed,[]),
});
const required=definition.variants[variant].required,forbidden=definition.variants[variant].forbidden;
const missing=required.filter(id=>effects[id]!==true),observedForbidden=forbidden.filter(id=>effects[id]===true);
const runtimeErrors=Object.values(schedules).some(r=>r.runtimeError);
const verdict=runtimeErrors?'RUNTIME_ERROR':missing.length&&observedForbidden.length?'UNDERREACH_AND_OVERREACH':missing.length?'UNDERREACH':observedForbidden.length?'OVERREACH':'PASS';
process.stdout.write(JSON.stringify({schema_version:'0.1',case_id:definition.case_id,variant,verdict,missing_required_effects:missing,observed_forbidden_effects:observedForbidden,observed_effects:effects,schedules},null,2)+'\n');
process.exitCode=verdict==='PASS'?0:runtimeErrors?2:1;

}
main().catch(error=>{process.stderr.write(error.stack+"\n");process.exitCode=2;});
