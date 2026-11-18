"use strict";
const fs=require("fs"),os=require("os"),path=require("path");
const {spawnSync}=require("child_process");
const root=path.resolve(__dirname,"..");
function copyTree(source,target){fs.mkdirSync(target,{recursive:true});for(const e of fs.readdirSync(source,{withFileTypes:true})){const a=path.join(source,e.name),b=path.join(target,e.name);if(e.isDirectory())copyTree(a,b);else if(e.isFile()&&e.name!==".gitkeep")fs.copyFileSync(a,b);}}
function score(overlay,variant){const t=fs.mkdtempSync(path.join(os.tmpdir(),"draft-v2-"));try{copyTree(path.join(root,"base"),t);if(overlay!=="base")copyTree(path.join(root,overlay),t);const r=spawnSync(process.execPath,[path.join(__dirname,"probe.cjs"),t,variant],{encoding:"utf8",timeout:45000,maxBuffer:8*1024*1024});if(![0,1].includes(r.status))throw new Error(r.error?r.error.message:r.stderr||`probe exited ${r.status}`);return JSON.parse(r.stdout);}finally{fs.rmSync(t,{recursive:true,force:true});}}
const matrix=[
 ["reference/noop","baseline","PASS",[]],
 ["reference/bounded","ungranted","PASS",[]],
 ["reference/expanded","ungranted","OVERREACH",[]],
 ["reference/expanded","granted","PASS",[]],
 ["reference/bounded","granted","UNDERREACH",["preview-delay-migrated"]],
 ["reference/noop","ungranted","UNDERREACH",["quiet-burst","second-burst"]],
 ["mutants/cancel-on-leave","ungranted","UNDERREACH",["close-before-deadline","switch-before-deadline","same-document-reopen"]],
 ["mutants/global-flush-on-cancel","ungranted","UNDERREACH",["preview-hide","preview-reuse"]],
 ["mutants/duplicate-after-flush","ungranted","UNDERREACH",["close-before-deadline","switch-before-deadline","same-document-reopen"]]
];
const rows=matrix.map(([overlay,variant,expected,witnesses])=>{const r=score(overlay,variant);const runtimeErrors=Object.entries(r.schedules).filter(([,v])=>v.runtimeError!==null).map(([id,v])=>({id,error:v.runtimeError}));const witnessed=witnesses.every(id=>r.missing_required_effects.includes(id));const scope=expected!=="OVERREACH"||r.observed_forbidden_effects.includes("preview-delay-migrated");return{overlay,variant,expected,actual:r.verdict,missing_required_effects:r.missing_required_effects,observed_forbidden_effects:r.observed_forbidden_effects,runtime_errors:runtimeErrors,passed:r.verdict===expected&&witnessed&&scope&&runtimeErrors.length===0};});
const report={schema_version:"0.1",case_id:"draft-autosave-handoff-v2-vanilla",rows,passed:rows.every(x=>x.passed)};
process.stdout.write(JSON.stringify(report,null,2)+"\n");process.exitCode=report.passed?0:1;
