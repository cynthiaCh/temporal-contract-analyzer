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

function score(overlay, variant) {
  const temporary = fs.mkdtempSync(path.join(os.tmpdir(), "ftcb-listener-order-"));
  try {
    copyTree(path.join(caseRoot, "base"), temporary);
    copyTree(path.join(caseRoot, overlay), temporary);
    const completed = spawnSync(process.execPath, [path.join(__dirname, "probe.cjs"), temporary, variant], {
      encoding: "utf8",
      timeout: 30000,
    });
    if (![0, 1].includes(completed.status)) {
      throw new Error(completed.stderr.trim() || `probe exited ${completed.status}`);
    }
    return JSON.parse(completed.stdout);
  } finally {
    fs.rmSync(temporary, { recursive: true, force: true });
  }
}

const matrix = [
  ["reference/bounded", "ungranted", "PASS"],
  ["reference/expanded", "ungranted", "OVERREACH"],
  ["reference/bounded", "granted", "UNDERREACH"],
  ["reference/expanded", "granted", "PASS"],
  ["reference/alternative", "ungranted", "PASS"],
  ["mutants/order-only", "ungranted", "UNDERREACH"],
  ["mutants/no-delivery-fence", "ungranted", "UNDERREACH"],
  ["mutants/channel-identity", "ungranted", "UNDERREACH"],
  ["mutants/late-owner", "ungranted", "UNDERREACH"],
  ["mutants/visit-only", "ungranted", "UNDERREACH"],
  ["reference/noop", "ungranted", "UNDERREACH"],
  ["mutants/bootstrap-only", "ungranted", "UNDERREACH"],
  ["mutants/late-subscription", "ungranted", "UNDERREACH"],
];
const rows = matrix.map(([overlay, variant, expected]) => {
  const result = score(overlay, variant);
  return { overlay, variant, expected, actual: result.verdict, passed: result.verdict === expected };
});
const report = {schema_version: "0.1", case_id: "listener-snapshot-order-vanilla", rows, passed: rows.every((row) => row.passed)};
process.stdout.write(`${JSON.stringify(report, null, 2)}\n`);
process.exitCode = report.passed ? 0 : 1;
