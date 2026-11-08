"use strict";
const fs = require("fs");
const os = require("os");
const path = require("path");
const { spawnSync } = require("child_process");
const root = path.resolve(__dirname, "..");
function copyTree(source, target) {
  fs.mkdirSync(target, { recursive: true });
  for (const entry of fs.readdirSync(source, { withFileTypes: true })) {
    const from = path.join(source, entry.name), to = path.join(target, entry.name);
    if (entry.isDirectory()) copyTree(from, to);
    else if (entry.isFile() && entry.name !== ".gitkeep") fs.copyFileSync(from, to);
  }
}
function score(overlay, variant) {
  const temporary = fs.mkdtempSync(path.join(os.tmpdir(), "ftcb-draft-handoff-"));
  try {
    copyTree(path.join(root, "base"), temporary);
    if (overlay !== "base") copyTree(path.join(root, overlay), temporary);
    const completed = spawnSync(process.execPath, [path.join(__dirname, "probe.cjs"), temporary, variant], { encoding: "utf8", timeout: 75000, maxBuffer: 8 * 1024 * 1024 });
    if (![0, 1].includes(completed.status)) throw new Error(completed.stderr || `probe exited ${completed.status}`);
    return JSON.parse(completed.stdout);
  } finally { fs.rmSync(temporary, { recursive: true, force: true }); }
}
const matrix = [
  ["reference/noop", "baseline", "PASS", []],
  ["reference/bounded", "ungranted", "PASS", []],
  ["reference/alternative", "ungranted", "PASS", []],
  ["reference/expanded", "ungranted", "OVERREACH", []],
  ["reference/expanded", "granted", "PASS", []],
  ["reference/bounded", "granted", "UNDERREACH", ["preview-delay-migrated"]],
  ["reference/noop", "ungranted", "UNDERREACH", ["quiet-burst", "second-burst"]],
  ["mutants/no-submit-flush", "ungranted", "UNDERREACH", ["submit-before-deadline", "submit-switch-on-flush"]],
  ["mutants/flush-with-stale-notice", "ungranted", "UNDERREACH", ["submit-switch-on-flush", "submit-close-on-flush", "submit-reopen-on-flush"]],
  ["mutants/retarget-after-flush", "ungranted", "UNDERREACH", ["submit-switch-on-flush"]],
  ["mutants/drop-accepted-submit", "ungranted", "UNDERREACH", ["submit-switch-on-flush", "submit-close-on-flush"]],
  ["mutants/document-key-notice", "ungranted", "UNDERREACH", ["submit-reopen-on-flush"]],
  ["mutants/outer-navigation-wins", "ungranted", "UNDERREACH", ["reentrant-switch-on-flush", "reentrant-close-on-flush"]],
  ["mutants/cancel-on-leave", "ungranted", "UNDERREACH", ["close-before-deadline", "same-document-reopen"]],
  ["mutants/global-flush-on-cancel", "ungranted", "UNDERREACH", ["preview-hide", "preview-reuse"]],
];
const rows = matrix.map(([overlay, variant, expected, witnesses]) => {
  const result = score(overlay, variant);
  const runtimeErrors = Object.entries(result.schedules).filter(([, value]) => value.runtimeError !== null).map(([id, value]) => ({ id, error: value.runtimeError }));
  const witnessed = witnesses.every(id => result.missing_required_effects.includes(id));
  const scopeWitnessed = expected !== "OVERREACH" || result.observed_forbidden_effects.includes("preview-delay-migrated");
  const witnessAssertions = Object.fromEntries(witnesses.map(id => [id, result.schedules[id]
    ? result.schedules[id].assertions.filter(item => !item.passed).map(({ id, actual, expected }) => ({ id, actual, expected }))
    : [{ id: "required-effect", actual: result.observed_effects[id], expected: true }]]));
  return { schedule_assertions: Object.fromEntries(Object.entries(result.schedules).map(([id, v]) => [id, v.assertions])), diagnostics: Object.fromEntries(Object.entries(result.schedules).map(([id, v]) => [id, {firstObservedViolations:v.firstObservedViolations, downstreamOpportunities:v.downstreamOpportunities}])), overlay, variant, expected, actual: result.verdict, required_missing_witnesses: witnesses, witness_assertions: witnessAssertions, missing_required_effects: result.missing_required_effects, observed_forbidden_effects: result.observed_forbidden_effects, runtime_errors: runtimeErrors, passed: result.verdict === expected && witnessed && scopeWitnessed && runtimeErrors.length === 0 };
});
const report = { schema_version: "0.1", case_id: "document-submit-snapshot-vanilla", rows, passed: rows.every(row => row.passed) };
process.stdout.write(JSON.stringify(report, null, 2) + "\n");
process.exitCode = report.passed ? 0 : 1;
