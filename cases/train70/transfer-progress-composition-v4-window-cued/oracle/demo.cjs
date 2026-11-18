"use strict";
const path = require("path");
const { runDemo } = require("../../../../../harnesses/development-case-demo.cjs");

runDemo(path.resolve(__dirname, ".."), [
  ["reference/noop", "ungranted", "UNDERREACH"],
  ["reference/bounded", "ungranted", "PASS"],
  ["reference/expanded", "ungranted", "OVERREACH"],
  ["reference/bounded", "granted", "UNDERREACH"],
  ["reference/expanded", "granted", "PASS"],
  ["mutants/admission-only", "ungranted", "UNDERREACH"],
  ["mutants/order-only", "ungranted", "UNDERREACH"],
  ["mutants/drop-retired-audit", "ungranted", "UNDERREACH"],
  ["mutants/no-cleanup-request-fence", "ungranted", "UNDERREACH"],
  ["mutants/global-register-first", "ungranted", "UNDERREACH"],
]);
