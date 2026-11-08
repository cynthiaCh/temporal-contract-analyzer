"use strict";
const path = require("path");
const { pathToFileURL } = require("url");
const candidate = path.resolve(process.argv[2] || "");
const schedule = process.argv[3];
const baseline = process.argv[4] === "baseline";
const assertions = [], trace = [], rows = [], selections = [], complianceRows = [], previewRows = [];
const leases = new Map();
let nextLease = 0, visualSelection = null, runtimeError = null, previewCached = null;
const record = (type, detail = {}) => trace.push({ step: trace.length, type, ...detail });
function snapshot(value) {
  if (Array.isArray(value)) return value.map(snapshot);
  if (value && typeof value === "object") return Object.fromEntries(Object.keys(value).sort().map(key => [key, snapshot(value[key])]));
  return value;
}
const check = (id, actual, expected) => {
  const actualValue = snapshot(actual), expectedValue = snapshot(expected);
  assertions.push({ id, actual: actualValue, expected: expectedValue, passed: JSON.stringify(actualValue) === JSON.stringify(expectedValue) });
};
// Each actual EventTarget is one injected live transport subscription. The
// explicit delivery boundary models network arrival, not a framework lifecycle.
const transport = {
  subscribe(id, receive) {
    const token = ++nextLease;
    const target = new EventTarget();
    const listener = event => receive(event.value);
    target.addEventListener("record", listener);
    leases.set(token, { id, target, listener });
    record("subscribe", { token, id });
    return () => {
      target.removeEventListener("record", listener);
      leases.delete(token);
      record("release", { token, id });
    };
  },
};
function deliver(id, value) {
  record("network-delivery", { id, value });
  // Subscribers added by a synchronous delivery belong to a later observation.
  for (const [token, lease] of [...leases]) {
    if (lease.id !== id || !leases.has(token)) continue;
    const event = new Event("record");
    event.value = value;
    lease.target.dispatchEvent(event);
  }
}
const liveKeys = () => [...leases.values()].map(lease => lease.id).sort();
const compact = list => list.map(({ id, value, source }) => [id, value, source]);
async function main() {
  const source = file => import(pathToFileURL(path.join(candidate, "src", file)).href);
  const [{ createRecordRepository }, { createDetailWorkspace }, { createComplianceReview }, { createRecentPreview }] = await Promise.all([
    source("record-repository.js"), source("workspace.js"), source("compliance-review.js"), source("recent-preview.js"),
  ]);
  const repository = createRecordRepository({ transport, seed: { A: "cached-A", B: "cached-B", C: "cached-C" } });
  let onDetail = () => {};
  const workspace = createDetailWorkspace({
    repository,
    renderSelection(id) { visualSelection = id; selections.push(id); record("selection", { id }); },
    renderDetail(row) { check("row-selected-at-delivery-" + rows.length, workspace.selection(), row.id); check("row-render-selection-at-delivery-" + rows.length, visualSelection, row.id); rows.push(row); record("detail", row); },
    onDetail(row, navigation) { record("integration-enter", row); onDetail(row, navigation); record("integration-return", row); },
  });
  const compliance = createComplianceReview({ repository, publish(row) { complianceRows.push(row); record("compliance", row); } });
  const preview = createRecentPreview({ repository, publish(row) { previewRows.push(row); record("preview", row); } });
  const open = id => { record("open-enter", { id }); workspace.open(id); record("open-return", { id, selected: workspace.selection() }); };
  const close = () => { record("close-enter"); workspace.close(); record("close-return", { selected: workspace.selection() }); };
  const selected = (id, expected) => { check(id, workspace.selection(), expected); check(id + "-render", visualSelection, expected); };
  const warm = (id, value = "cached-" + id) => [id, value, "cache"];
  const fresh = (id, value = "fresh-" + id) => [id, value, "network"];
  switch (schedule) {
    case "cold-detail": {
      open("D"); selected("cold-selection-before-network", "D"); check("no-invented-cache", rows, []);
      deliver("D", "fresh-D"); check("cold-delivery", compact(rows), [fresh("D")]);
      close(); check("cold-release", liveKeys(), []); break;
    }
    case "warm-detail": {
      open("A"); selected("warm-selection-before-return", "A");
      check("warm-row-before-return", compact(rows), baseline ? [] : [warm("A")]);
      check("warm-watch-remains-live", liveKeys(), ["A"]);
      deliver("A", "fresh-A"); deliver("A", "next-A");
      check("warm-and-live-observations", compact(rows), [...(baseline ? [] : [warm("A")]), fresh("A"), fresh("A", "next-A")]);
      close(); check("warm-release", liveKeys(), []); break;
    }
    case "close-before-network": {
      open("A"); close(); selected("closed-before-network", null); check("closed-has-no-lease", liveKeys(), []);
      deliver("A", "late-A"); check("closed-no-later-row", compact(rows), baseline ? [] : [warm("A")]);
      close(); check("repeat-close-idempotent", liveKeys(), []); break;
    }
    case "switch-before-network": {
      open("A"); open("B"); selected("switched-before-network", "B"); check("only-successor-lease", liveKeys(), ["B"]);
      deliver("A", "late-A"); deliver("B", "fresh-B");
      check("only-successor-fresh-row", compact(rows), [...(baseline ? [] : [warm("A"), warm("B")]), fresh("B")]); close(); break;
    }
    case "reentrant-cache-switch":
    case "reentrant-cache-close": {
      let navigated = false;
      onDetail = (row, nav) => { if (row.id === "A" && !navigated) { navigated = true; if (schedule.endsWith("switch")) nav.open("C"); else nav.close(); } };
      open("A");
      const next = schedule.endsWith("switch") ? "C" : null;
      selected("latest-navigation-after-outer-return", baseline ? "A" : next);
      check("returned-watch-belongs-to-current-activation", liveKeys(), baseline ? ["A"] : next ? [next] : []);
      deliver("A", "fresh-A"); selected("network-integration-navigation", next);
      if (next) deliver(next, "fresh-C");
      const expected = baseline ? [fresh("A")] : [warm("A")];
      if (next) { if (!baseline) expected.push(warm("C")); expected.push(fresh("C")); }
      check("no-retired-activation-row", compact(rows), expected);
      close(); check("current-close-releases-current-watch", liveKeys(), []); break;
    }
    case "same-key-reentrant-open": {
      let navigated = false;
      onDetail = (row, nav) => { if (!navigated) { navigated = true; nav.open("A"); } };
      open("A"); selected("same-key-selected", "A");
      check("one-lease-after-same-key-open", liveKeys(), ["A"]);
      deliver("A", "fresh-A"); deliver("A", "next-A");
      check("same-key-single-delivery-per-observation", compact(rows), [...(baseline ? [] : [warm("A"), warm("A")]), fresh("A"), fresh("A", "next-A")]);
      close(); check("same-key-successor-lease-released", liveKeys(), []); break;
    }
    case "same-key-close-reopen": {
      open("A"); close(); open("A");
      check("reopen-one-lease", liveKeys(), ["A"]); deliver("A", "fresh-A");
      check("reopened-activation-only", compact(rows), [...(baseline ? [] : [warm("A"), warm("A")]), fresh("A")]);
      close(); check("reopened-release", liveKeys(), []); break;
    }
    case "reentrant-network-switch": {
      let moved = false;
      onDetail = (row, nav) => { if (row.id === "D" && !moved) { moved = true; nav.open("B"); } };
      open("D"); deliver("D", "fresh-D"); selected("network-navigation-survives", "B");
      check("network-switch-keeps-successor", liveKeys(), ["B"]);
      deliver("D", "late-D"); deliver("B", "fresh-B");
      check("network-reentry-rows", compact(rows), [fresh("D"), ...(baseline ? [] : [warm("B")]), fresh("B")]); close(); break;
    }
    case "compliance-fresh-only": {
      compliance.inspect("A"); check("compliance-never-uses-cache", complianceRows, []);
      deliver("A", "fresh-A"); check("compliance-network-observation", compact(complianceRows), [fresh("A")]);
      compliance.close(); deliver("A", "late-A"); check("closed-compliance-silent", compact(complianceRows), [fresh("A")]); break;
    }
    case "shared-consumer-isolation": {
      open("A"); compliance.inspect("A");
      check("detail-cache-policy", compact(rows), baseline ? [] : [warm("A")]); check("compliance-independent-policy", complianceRows, []);
      close(); check("detail-close-retains-review", liveKeys(), ["A"]);
      deliver("A", "fresh-A"); check("review-keeps-own-subscription", compact(complianceRows), [fresh("A")]);
      check("detail-stays-retired", compact(rows), baseline ? [] : [warm("A")]); compliance.close(); break;
    }
    case "recent-preview-policy": {
      preview.inspect("A"); previewCached = JSON.stringify(compact(previewRows)) === JSON.stringify([warm("A")]);
      check("recognized-preview-delivery", previewRows.length === 0 || previewCached, true);
      if (baseline) check("original-preview-network-only", previewRows, []);
      deliver("A", "fresh-A");
      check("preview-network-continuation", compact(previewRows), [...(previewCached ? [warm("A")] : []), fresh("A")]);
      preview.hide(); deliver("A", "late-A"); check("preview-after-hide-count", previewRows.length, previewCached ? 2 : 1); break;
    }
    case "recent-preview-reuse": {
      preview.inspect("A"); previewCached = JSON.stringify(compact(previewRows)) === JSON.stringify([warm("A")]);
      preview.hide(); preview.inspect("B"); deliver("A", "late-A"); deliver("B", "fresh-B");
      check("preview-reuse-policy", compact(previewRows), [...(previewCached ? [warm("A"), warm("B")] : []), fresh("B")]);
      preview.hide(); break;
    }
    default: throw new Error(`Unknown schedule ${schedule}`);
  }
  check("schedule-releases-all-resources", leases.size, 0);
}
main().catch(error => { runtimeError = String(error.stack || error); }).finally(() => {
  process.stdout.write(JSON.stringify({ schedule, baseline, passed: runtimeError === null && assertions.length > 0 && assertions.every(item => item.passed), runtimeError, assertions, rows, selections, complianceRows, previewRows, previewCached, activeLeases: liveKeys(), trace }) + "\n");
});
