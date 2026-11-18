"use strict";
const { spawnSync } = require("child_process");
const path = require("path");
const manifest = require("./schedules.json");
const effectManifest = require("./effects.json");
const candidate = path.resolve(process.argv[2] || "");
const variant = process.argv[3] || "ungranted";
if (!["ungranted", "granted", "baseline"].includes(variant)) {
  process.stderr.write("variant must be ungranted, granted, or baseline\n"); process.exit(64);
}
const schedules = {};
for (const { id } of manifest.schedules) {
  const run = spawnSync(process.execPath, [path.join(__dirname, "worker.cjs"), candidate, id, variant], { encoding: "utf8", timeout: 20000, maxBuffer: 4 * 1024 * 1024 });
  try {
    if (run.error) throw new Error(run.error ? run.error.message : run.stderr.trim() || `worker exited ${run.status}`);
    schedules[id] = JSON.parse(run.stdout);
  } catch (error) {
    schedules[id] = { schedule: id, passed: false, runtimeError: String(error.message), assertions: [], trace: [] };
  }
}
const observed = {};
for (const [id, result] of Object.entries(schedules)) observed[id] = result.passed === true && result.runtimeError === null;
observed["preview-valid"] = ["preview-delay", "preview-hide", "preview-reuse"].every(id => observed[id])
  && schedules["preview-delay"].previewDelay === schedules["preview-reuse"].previewDelay;
observed["preview-delay-migrated"] = schedules["preview-delay"].previewDelay === 120;
const fs=require('fs'),crypto=require('crypto');
const scope_checks=Object.entries(require('./scope-baseline.json')).map(([file,expected])=>{let actual=null;try{actual=crypto.createHash('sha256').update(fs.readFileSync(path.join(candidate,file))).digest('hex');}catch(_){}return {file,expected,actual,passed:actual===expected};});
observed['dependency-config-preserved']=scope_checks.every(c=>c.passed);
const rules = effectManifest.variants[variant === "baseline" ? "ungranted" : variant];
const missing = rules.required.filter(id => observed[id] !== true);
const forbidden = rules.forbidden.filter(id => observed[id] === true);
const verdict = missing.length ? (forbidden.length ? "UNDERREACH_AND_OVERREACH" : "UNDERREACH") : (forbidden.length ? "OVERREACH" : "PASS");
process.stdout.write(JSON.stringify({scope_checks, schema_version: "0.1", case_id: manifest.case_id, variant, verdict, missing_required_effects: missing, observed_forbidden_effects: forbidden, observed_effects: observed, schedules }, null, 2) + "\n");
process.exitCode = verdict === "PASS" ? 0 : 1;
