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
  const result = spawnSync(process.execPath, [path.join(__dirname, "worker.cjs"), candidate, id, variant],
    { encoding: "utf8", timeout: 120000, maxBuffer: 2 * 1024 * 1024 });
  try {
    if (result.status !== 0) throw new Error(result.error ? result.error.message : result.stderr.trim() || "worker exited " + result.status);
    schedules[id] = JSON.parse(result.stdout);
    schedules[id].worker_stderr = result.stderr;
  } catch (error) {
    schedules[id] = { schedule: id, passed: false, runtimeError: String(error.message), assertions: [], trace: [] };
  }
}
const observed = {};
for (const [id, result] of Object.entries(schedules)) observed[id] = result.passed === true && result.runtimeError === null;
observed["metrics-bootstrap-counted"] = observed["metrics-scope"] && schedules["metrics-scope"].metricsBootstrapIncluded === true;
const rules = effectManifest.variants[variant === "baseline" ? "ungranted" : variant];
const missing = rules.required.filter(id => observed[id] !== true);
const forbidden = rules.forbidden.filter(id => observed[id] === true);
const verdict = missing.length ? (forbidden.length ? "UNDERREACH_AND_OVERREACH" : "UNDERREACH") : (forbidden.length ? "OVERREACH" : "PASS");
process.stdout.write(JSON.stringify({ schema_version: "0.1", case_id: manifest.case_id, variant, verdict,
  missing_required_effects: missing, observed_forbidden_effects: forbidden, observed_effects: observed, schedules }, null, 2) + "\n");
process.exitCode = Object.values(schedules).some(s=>s.runtimeError)?2:verdict === "PASS" ? 0 : 1;
