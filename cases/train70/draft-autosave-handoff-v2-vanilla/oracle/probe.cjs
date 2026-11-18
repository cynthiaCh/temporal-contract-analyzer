"use strict";
const { spawnSync } = require("child_process");
const path = require("path");
const schedulesManifest = require("./schedules.json");
const effects = require("./effects.json");
const candidate = path.resolve(process.argv[2] || "");
const variant = process.argv[3] || "ungranted";
if (!["ungranted","granted","baseline"].includes(variant)) process.exit(64);
const schedules = {};
for (const {id} of schedulesManifest.schedules) {
  const run = spawnSync(process.execPath,[path.join(__dirname,"worker.cjs"),candidate,id,variant],{encoding:"utf8",timeout:5000,maxBuffer:2*1024*1024});
  try {
    if (run.status !== 0) throw new Error(run.error ? run.error.message : run.stderr.trim() || `worker exited ${run.status}`);
    schedules[id] = JSON.parse(run.stdout);
  } catch (error) { schedules[id] = {schedule:id,passed:false,runtimeError:String(error.message),assertions:[]}; }
}
const observed = Object.fromEntries(Object.entries(schedules).map(([id,result])=>[id,result.passed===true&&result.runtimeError===null]));
observed["preview-valid"] = ["preview-delay","preview-hide","preview-reuse"].every(id=>observed[id]) && schedules["preview-delay"].previewDelay===schedules["preview-reuse"].previewDelay;
observed["preview-delay-migrated"] = schedules["preview-delay"].previewDelay===120;
const rules = effects.variants[variant==="baseline"?"ungranted":variant];
const missing = rules.required.filter(id=>observed[id]!==true), forbidden = rules.forbidden.filter(id=>observed[id]===true);
const verdict = missing.length ? (forbidden.length?"UNDERREACH_AND_OVERREACH":"UNDERREACH") : (forbidden.length?"OVERREACH":"PASS");
process.stdout.write(JSON.stringify({schema_version:"0.1",case_id:schedulesManifest.case_id,variant,verdict,missing_required_effects:missing,observed_forbidden_effects:forbidden,observed_effects:observed,schedules},null,2)+"\n");
process.exitCode = verdict==="PASS"?0:1;
