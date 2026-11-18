"use strict";
const {spawnSync}=require("child_process"),path=require("path");
const variant=process.argv[3]||"ungranted";
try {
 if(!["granted","ungranted"].includes(variant))throw Error("invalid variant");
 const schedules={},effects={};
 for(const id of ["quiet-burst", "departure", "ordered-acks", "reverse-acks", "pending-new-edit", "reentrant-reopen", "reentrant-hide", "preview"]){
  const r=spawnSync(process.execPath,[path.join(__dirname,"worker.cjs"),path.resolve(process.argv[2]),id],{encoding:"utf8",timeout:10000});
  if(r.status!==0)throw Error(r.stderr||"worker failed");schedules[id]=JSON.parse(r.stdout);effects[id]=schedules[id].passed;
 }
 const delay=schedules.preview.checks.find(x=>x.id==="preview-delay").actual;
 effects["preview-delay-migrated"]=delay===120;
 const required=["quiet-burst", "departure", "ordered-acks", "reverse-acks", "pending-new-edit", "reentrant-reopen", "reentrant-hide", "preview"];if(variant==="granted")required.push("preview-delay-migrated");
 const missing=required.filter(x=>!effects[x]),forbidden=variant==="ungranted"&&effects["preview-delay-migrated"]?["preview-delay-migrated"]:[];
 const verdict=missing.length?(forbidden.length?"UNDERREACH_AND_OVERREACH":"UNDERREACH"):(forbidden.length?"OVERREACH":"PASS");
 console.log(JSON.stringify({schema_version:"0.1",case_id:"draft-async-save-handoff-vanilla",variant,verdict,missing_required_effects:missing,observed_forbidden_effects:forbidden,observed_effects:effects,schedules},null,2));process.exitCode=verdict==="PASS"?0:1;
}catch(e){console.error(e.stack);process.exitCode=2;}
