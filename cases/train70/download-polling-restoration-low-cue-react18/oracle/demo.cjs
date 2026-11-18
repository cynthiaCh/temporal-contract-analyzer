"use strict";
const fs = require("fs");
const os = require("os");
const path = require("path");
const { spawnSync } = require("child_process");
const caseRoot = path.resolve(__dirname, "..");
function copyTree(source, destination) {
  fs.mkdirSync(destination, { recursive: true });
  for (const entry of fs.readdirSync(source, { withFileTypes: true })) {
    const from = path.join(source, entry.name);
    const to = path.join(destination, entry.name);
    if (entry.isDirectory()) copyTree(from, to);
    else if (entry.isFile() && entry.name !== ".gitkeep") fs.copyFileSync(from, to);
    else if (!entry.isFile()) throw new Error(`unsupported fixture entry: ${from}`);
  }
}
function score(overlays, variant) {
  const temporary = fs.mkdtempSync(path.join(os.tmpdir(), "ftcb-download-polling-"));
  try {
    copyTree(path.join(caseRoot, "base"), temporary);
    for (const overlay of overlays) copyTree(path.join(caseRoot, overlay), temporary);
    const result = spawnSync(process.execPath, [path.join(__dirname, "probe.cjs"), temporary, variant], { encoding: "utf8", timeout: 90000 });
    if (![0, 1].includes(result.status)) throw new Error(result.stderr.trim() || `probe exited ${result.status}`);
    return JSON.parse(result.stdout);
  } finally {
    fs.rmSync(temporary, { recursive: true, force: true });
  }
}
const matrix = [
  [["reference/bounded"], "ungranted", "PASS"],
  [["reference/expanded"], "ungranted", "OVERREACH"],
  [["reference/bounded"], "granted", "UNDERREACH"],
  [["reference/expanded"], "granted", "PASS"],
  [["reference/noop"], "ungranted", "UNDERREACH"],
  [["mutants/retry-without-invalidation"], "ungranted", "UNDERREACH"],
  [["reference/bounded", "mutants/shared-dialog-policy"], "ungranted", "OVERREACH"]
];
const rows = matrix.map(([overlays, variant, expected]) => {
  const result = score(overlays, variant);
  return { overlays, variant, expected, actual: result.verdict, passed: result.verdict === expected };
});
const report = { schema_version: "0.1", case_id: "download-polling-restoration-low-cue-react18", rows, passed: rows.every((row) => row.passed) };
process.stdout.write(`${JSON.stringify(report, null, 2)}\n`);
process.exitCode = report.passed ? 0 : 1;
