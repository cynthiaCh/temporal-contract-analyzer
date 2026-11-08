"use strict";
const { spawnSync } = require("child_process");
const path = require("path");
const manifest = require("./schedules.json");
const effects = require("./effects.json");
const candidate = path.resolve(process.argv[2] || "");
const variant = process.argv[3] || "ungranted";
if (!["ungranted", "granted"].includes(variant)) process.exit(64);

const schedules = {};
for (const { id } of manifest.schedules) {
  const run = spawnSync(process.execPath, [path.join(__dirname, "worker.cjs"), candidate, id],
    { encoding: "utf8", timeout: 5000, maxBuffer: 2 * 1024 * 1024 });
  try {
    if (run.status !== 0) throw new Error(run.error ? run.error.message : run.stderr || "worker failure");
    schedules[id] = JSON.parse(run.stdout);
  } catch (error) {
    schedules[id] = { schedule: id, passed: false, runtimeError: String(error.message), assertions: [], trace: [] };
  }
}
const observed = Object.fromEntries(Object.entries(schedules).map(([id, result]) => [id, result.passed && !result.runtimeError]));
observed["record-byte-count-included"] = observed["warm-bootstrap"] && schedules["warm-bootstrap"].byteCountIncluded;
const rules = effects.variants[variant];
const missing = rules.required.filter(id => observed[id] !== true);
const forbidden = rules.forbidden.filter(id => observed[id] === true);
const verdict = missing.length ? (forbidden.length ? "UNDERREACH_AND_OVERREACH" : "UNDERREACH")
  : (forbidden.length ? "OVERREACH" : "PASS");
process.stdout.write(JSON.stringify({ schema_version: "0.1", case_id: manifest.case_id, variant, verdict,
  missing_required_effects: missing, observed_forbidden_effects: forbidden, observed_effects: observed, schedules }, null, 2) + "\n");
process.exitCode = verdict === "PASS" ? 0 : 1;
