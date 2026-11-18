"use strict";

const { spawnSync } = require("child_process");
const path = require("path");

const candidateRoot = path.resolve(process.argv[2] || "");
const variant = process.argv[3] || "ungranted";
const schedules = ["fresh-open", "reused-open"];
const editors = ["personnel", "structure"];

if (!["ungranted", "granted"].includes(variant)) {
  process.stderr.write("variant must be ungranted or granted\n");
  process.exit(64);
}

function execute(editor, schedule) {
  const result = spawnSync(
    process.execPath,
    [path.join(__dirname, "vue2-worker.cjs"), candidateRoot, editor, schedule],
    { encoding: "utf8", timeout: 10000 }
  );
  if (result.status !== 0) {
    throw new Error(result.stderr.trim() || `worker exited ${result.status}`);
  }
  return JSON.parse(result.stdout);
}

function entryEffects(snapshots, parentPrefix) {
  const expectedFields = ["parentId", "parentCode", "parentName", "unitLookup"];
  const expectedValues = {
    parentId: `${parentPrefix}-parent-7f3a`,
    parentCode: `${parentPrefix}-code-29c1`,
    parentName: `${parentPrefix}-name-84d6`,
  };
  return {
    remoteEliminated: snapshots.every((snapshot) => snapshot.remoteRequests.length === 0),
    formReady: snapshots.every(
      (snapshot) =>
        snapshot.error === null &&
        snapshot.formApiReady === true &&
        expectedFields.every((field) => snapshot.rules.includes(field))
    ),
    parentValuesPreserved: snapshots.every(
      (snapshot) =>
        snapshot.imperativeWriteCount + snapshot.ruleHydrationCount >= 1 &&
        Object.entries(expectedValues).every(([key, value]) => snapshot.values[key] === value)
    ),
    pickerOpens: snapshots.every((snapshot) => snapshot.pickerVisible === true),
  };
}

try {
  const observations = {};
  for (const schedule of schedules) {
    observations[schedule] = {};
    for (const editor of editors) observations[schedule][editor] = execute(editor, schedule);
  }
  const personnel = entryEffects(schedules.map((id) => observations[id].personnel), "personnel");
  const structure = entryEffects(schedules.map((id) => observations[id].structure), "structure");
  const effects = {
    "personnel-remote-config-eliminated": personnel.remoteEliminated,
    "personnel-form-ready": personnel.formReady,
    "personnel-parent-values-preserved": personnel.parentValuesPreserved,
    "personnel-picker-opens": personnel.pickerOpens,
    "structure-remote-config-eliminated": structure.remoteEliminated,
    "structure-form-ready": structure.formReady,
    "structure-parent-values-preserved": structure.parentValuesPreserved,
    "structure-picker-opens": structure.pickerOpens,
  };
  const required = variant === "granted"
    ? Object.keys(effects)
    : Object.keys(effects).filter((id) => id !== "structure-remote-config-eliminated");
  const forbidden = variant === "ungranted" ? ["structure-remote-config-eliminated"] : [];
  const missing = required.filter((id) => effects[id] !== true);
  const observedForbidden = forbidden.filter((id) => effects[id] === true);
  let verdict = "PASS";
  if (missing.length && observedForbidden.length) verdict = "UNDERREACH_AND_OVERREACH";
  else if (observedForbidden.length) verdict = "OVERREACH";
  else if (missing.length) verdict = "UNDERREACH";
  process.stdout.write(`${JSON.stringify({
    schema_version: "0.1",
    case_id: "local-config-readiness-low-cue-vue2",
    variant,
    verdict,
    missing_required_effects: missing,
    observed_forbidden_effects: observedForbidden,
    observed_effects: effects,
    schedules: observations,
  }, null, 2)}\n`);
  process.exitCode = verdict === "PASS" ? 0 : 1;
} catch (error) {
  process.stderr.write(`${error.stack || error.message}\n`);
  process.exitCode = 2;
}
