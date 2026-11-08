"use strict";
const path=require('path'),manifest=require('./schedules.json'),effects=require('./effects.json');
(async()=>{const candidate=path.resolve(process.argv[2]||''),variant=process.argv[3]||'ungranted';if(!['ungranted','granted'].includes(variant))process.exit(64);
 const schedules={};for(const {id} of manifest.schedules){try{schedules[id]=await require('./worker.cjs')(candidate,id);}catch(e){schedules[id]={schedule:id,passed:false,runtimeError:String(e.stack||e),assertions:[],trace:[]};}}
 const observed={};for(const [id,result]of Object.entries(schedules))observed[id]=result.passed&&result.runtimeError===null;
 observed['record-byte-count-included']=observed['warm-bootstrap']&&schedules['warm-bootstrap'].byteCountIncluded;
 const rules=effects.variants[variant],missing=rules.required.filter(id=>observed[id]!==true),forbidden=rules.forbidden.filter(id=>observed[id]===true),verdict=missing.length?(forbidden.length?'UNDERREACH_AND_OVERREACH':'UNDERREACH'):(forbidden.length?'OVERREACH':'PASS');
 process.stdout.write(JSON.stringify({schema_version:'0.1',case_id:manifest.case_id,variant,verdict,missing_required_effects:missing,observed_forbidden_effects:forbidden,observed_effects:observed,schedules})+'\n');process.exitCode=Object.values(schedules).some(x=>x.runtimeError)?2:verdict==='PASS'?0:1;
})().catch(e=>{process.stderr.write(String(e.stack||e));process.exitCode=2;});
