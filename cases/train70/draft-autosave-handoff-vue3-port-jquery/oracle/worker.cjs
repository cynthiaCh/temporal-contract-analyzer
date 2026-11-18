"use strict";

// Observe only candidate public APIs. The clock is deterministic and every
// schedule is executed in a fresh process by probe.cjs.
const path = require("path");
const { pathToFileURL } = require("url");
const candidate = path.resolve(process.argv[2] || "");
const schedule = process.argv[3];
const baseline = process.argv[4] === "baseline";
let now = 0;
let serial = 0;
const pending = new Map();
const trace = [];
const assertions = [];
const writes = [];
const statuses = [];
const documents = [];
const previews = [];
let visible = null;
let runtimeError = null;
let previewDelay = null;
const record = (type, detail = {}) => trace.push({ time: now, type, ...detail });
const equal = (actual, expected) => require("util").isDeepStrictEqual(actual, expected);
const check = (id, actual, expected) => assertions.push({ id, passed: equal(actual, expected), actual, expected });
const timers = {
  schedule(callback, delay) {
    if (!Number.isFinite(delay) || delay < 0) throw new Error("invalid timer delay");
    const id = ++serial;
    pending.set(id, { callback, at: now + delay });
    record("timer-scheduled", { id, delay, due: now + delay });
    return id;
  },
  cancel(id) { pending.delete(id); record("timer-cancelled", { id }); },
};
function advance(target) {
  if (target < now) throw new Error("clock cannot move backward");
  let steps = 0;
  while (true) {
    const next = [...pending.entries()].filter(([, item]) => item.at <= target)
      .sort((a, b) => a[1].at - b[1].at || a[0] - b[0])[0];
    if (!next) break;
    if (++steps > 200) throw new Error("timer did not quiesce within 200 callbacks");
    pending.delete(next[0]);
    now = next[1].at;
    record("timer-fired", { id: next[0] });
    next[1].callback();
  }
  now = target;
}
const pairs = () => writes.map(({ id, text }) => [id, text]);
const statusPairs = () => statuses.map(({ id, text }) => [id, text]);
async function main() {
  const {createDraftStore,createWorkspace,createSearchPreview}=await require("./framework-loader.cjs").load(candidate);
  const actualStore = createDraftStore({ A: "seed-A", B: "seed-B", C: "seed-C" });
  const store = {
    read: id => actualStore.read(id),
    subscribe: listener => actualStore.subscribe(listener),
    write(id, text) {
      writes.push({ time: now, id, text });
      record("write-enter", { id, text });
      const event = actualStore.write(id, text);
      record("write-return", { id, text });
      return event;
    },
  };
  let onSaved = () => {};
  const workspace = createWorkspace({
    store, timers,
    renderDocument(value) {
      visible = value === null ? null : { ...value };
      documents.push({ time: now, value: visible });
      record("render-document", { value: visible });
    },
    renderStatus(event) {
      statuses.push({ time: now, ...event });
      record("render-status", { ...event, visible: visible && visible.id });
    },
    onSaved(event, navigation) {
      record("on-saved-enter", { ...event });
      onSaved(event, navigation);
      record("on-saved-return", { ...event });
    },
  });
  const nav = {};
  for (const name of ["open", "edit", "close"]) nav[name] = (...args) => {
    record("navigation-enter", { name, args });
    const result = workspace[name](...args);
    record("navigation-return", { name, visible });
    return result;
  };
  const preview = createSearchPreview({ timers, publish(value) {
    previews.push({ time: now, ...value }); record("preview-published", value);
  } });
  const selected = () => visible && visible.id;
  const finish = (expectedWrites, expectedStatuses) => {
    advance(600);
    check("exact-writes-after-quiescence", pairs(), expectedWrites);
    check("exact-save-statuses", statusPairs(), expectedStatuses);
    const expectedRecords = { A: "seed-A", B: "seed-B", C: "seed-C" };
    for (const [id, text] of expectedWrites) expectedRecords[id] = text;
    check("persistent-records-match-commits", Object.fromEntries(Object.keys(expectedRecords).map(id => [id, store.read(id)])), expectedRecords);
    check("no-pending-timers", pending.size, 0);
  };

  switch (schedule) {
    case "quiet-burst": {
      nav.open("A"); nav.edit("alpha"); advance(30); nav.edit("beta"); advance(80); nav.edit("gamma");
      advance(199);
      check("no-early-save", pairs(), baseline ? [["A", "alpha"], ["A", "beta"], ["A", "gamma"]] : []);
      advance(200);
      const expected = baseline ? [["A", "alpha"], ["A", "beta"], ["A", "gamma"]] : [["A", "gamma"]];
      check("save-at-quiet-deadline", pairs(), expected);
      check("latest-text-readable", store.read("A"), "gamma");
      finish(expected, expected);
      break;
    }
    case "second-burst": {
      nav.open("A"); nav.edit("one"); advance(120);
      check("first-burst-saved", pairs(), [["A", "one"]]);
      nav.edit("two"); advance(150); nav.edit("three"); advance(269);
      check("second-burst-waits", pairs(), baseline ? [["A", "one"], ["A", "two"], ["A", "three"]] : [["A", "one"]]);
      advance(270);
      const expected = baseline ? [["A", "one"], ["A", "two"], ["A", "three"]] : [["A", "one"], ["A", "three"]];
      check("second-burst-saved", pairs(), expected);
      finish(expected, expected);
      break;
    }
    case "close-before-deadline": {
      nav.open("A"); nav.edit("leaving-A"); advance(20); nav.close();
      check("saved-before-close-return", store.read("A"), "leaving-A");
      check("closed", selected(), null);
      check("no-departing-save-badge", statusPairs(), baseline ? [["A", "leaving-A"]] : []);
      finish([["A", "leaving-A"]], baseline ? [["A", "leaving-A"]] : []);
      break;
    }
    case "switch-before-deadline": {
      nav.open("A"); nav.edit("owned-by-A"); advance(20); nav.open("B");
      check("saved-before-open-return", store.read("A"), "owned-by-A");
      check("new-document-not-overwritten", store.read("B"), "seed-B");
      nav.edit("owned-by-B"); advance(140);
      check("new-visit-remains-active", selected(), "B");
      finish([["A", "owned-by-A"], ["B", "owned-by-B"]], baseline ? [["A", "owned-by-A"], ["B", "owned-by-B"]] : [["B", "owned-by-B"]]);
      break;
    }
    case "same-document-reopen": {
      nav.open("A"); nav.edit("first-visit"); advance(20); nav.close(); nav.open("A");
      check("restored-committed-text", visible, { id: "A", text: "first-visit" });
      nav.edit("second-visit"); advance(140); nav.close(); nav.close();
      finish([["A", "first-visit"], ["A", "second-visit"]], baseline ? [["A", "first-visit"], ["A", "second-visit"]] : [["A", "second-visit"]]);
      break;
    }
    case "reentrant-switch-on-flush":
    case "reentrant-close-on-flush": {
      nav.open("A"); nav.edit("departing"); advance(20);
      let calls = 0;
      onSaved = (event, navigation) => {
        if (event.id !== "A") return;
        calls++;
        if (schedule === "reentrant-switch-on-flush") navigation.open("C");
        else navigation.close();
      };
      nav.open("B");
      // The same input schedule has no pending baseline write: its edit already
      // notified before this callback was armed. Do not invent a baseline bug.
      const expectedSelection = baseline ? "B" : schedule === "reentrant-switch-on-flush" ? "C" : null;
      check("callback-delivered-inline-when-pending", calls, baseline ? 0 : 1);
      check("latest-navigation-wins-before-return", selected(), expectedSelection);
      check("old-document-saved-before-return", store.read("A"), "departing");
      onSaved = () => {};
      nav.edit("next-visit"); advance(140);
      const expected = [["A", "departing"]];
      if (expectedSelection) expected.push([expectedSelection, "next-visit"]);
      finish(expected, baseline ? expected : expected.slice(1));
      break;
    }
    case "reentrant-timer-save": {
      nav.open("A");
      onSaved = (event, navigation) => { if (event.id === "A") navigation.open("B"); };
      nav.edit("timer-A"); advance(120);
      check("timer-callback-navigation-retained", selected(), "B");
      check("retired-listener-skipped-during-delivery", statusPairs(), []);
      onSaved = () => {};
      nav.edit("active-B"); advance(240);
      check("active-save-badge-still-published", statusPairs(), [["B", "active-B"]]);
      finish([["A", "timer-A"], ["B", "active-B"]], [["B", "active-B"]]);
      break;
    }
    case "reentrant-edit": {
      nav.open("A");
      let edited = false;
      onSaved = (event, navigation) => {
        if (event.text === "one" && !edited) { edited = true; navigation.edit("two"); }
      };
      nav.edit("one"); advance(120);
      check("nested-edit-starts-new-burst", pairs(), baseline ? [["A", "one"], ["A", "two"]] : [["A", "one"]]);
      advance(239);
      check("new-burst-keeps-own-deadline", pairs(), baseline ? [["A", "one"], ["A", "two"]] : [["A", "one"]]);
      advance(240);
      finish([["A", "one"], ["A", "two"]], baseline ? [["A", "two"], ["A", "one"]] : [["A", "one"], ["A", "two"]]);
      break;
    }
    case "preview-delay": {
      preview.query("latest"); advance(39); check("preview-not-early", previews, []);
      advance(40); const at40 = previews.map(item => item.query);
      advance(119); check("no-intermediate-deadline", previews.map(item => item.query), at40);
      advance(120);
      const observed = previews.map(({ time, query }) => [time, query]);
      previewDelay = equal(observed, [[40, "latest"]]) ? 40 : equal(observed, [[120, "latest"]]) ? 120 : null;
      check("recognized-preview-policy", previewDelay === 40 || previewDelay === 120, true);
      if (baseline) check("baseline-preview-delay", previewDelay, 40);
      advance(600); check("preview-exactly-once", previews.length, 1);
      break;
    }
    case "preview-hide": {
      preview.query("discard-me"); advance(10); preview.hide();
      check("hide-does-not-flush", previews, []);
      advance(600); check("hidden-preview-never-publishes", previews, []);
      break;
    }
    case "preview-reuse": {
      preview.query("old"); advance(10); preview.hide(); advance(20); preview.query("new");
      advance(59); check("new-query-not-early", previews, []);
      advance(60); const at60 = previews.map(item => item.query);
      advance(139); check("reused-preview-no-intermediate-deadline", previews.map(item => item.query), at60);
      advance(140);
      const observed = previews.map(({ time, query }) => [time, query]);
      previewDelay = equal(observed, [[60, "new"]]) ? 40 : equal(observed, [[140, "new"]]) ? 120 : null;
      check("reused-preview-only-new-query", previewDelay === 40 || previewDelay === 120, true);
      advance(600); check("reused-preview-exactly-once", previews.length, 1);
      break;
    }
    case "closed-empty": {
      nav.edit("ignored"); nav.close(); nav.close(); finish([], []);
      check("remains-closed", selected(), null); break;
    }
    case "empty-text": {
      nav.open("A"); nav.edit(""); advance(20); nav.close();
      check("empty-value-is-persisted-before-return", store.read("A"), "");
      finish([["A", ""]], baseline ? [["A", ""]] : []); break;
    }
    case "dispose-before-deadline": {
      nav.open("A"); nav.edit("final-draft"); advance(20); workspace.dispose();
      check("dispose-commits-before-return", store.read("A"), "final-draft");
      check("disposed-view-cleared", selected(), null);
      finish([["A", "final-draft"]], baseline ? [["A", "final-draft"]] : []); break;
    }
    default: throw new Error(`unknown schedule: ${schedule}`);
  }
  check("schedule-quiescent", pending.size, 0);
}
main().catch(error => { runtimeError = String(error.stack || error); }).finally(() => {
  process.stdout.write(JSON.stringify({ schedule, baseline, passed: runtimeError === null && assertions.length > 0 && assertions.every(item => item.passed), runtimeError, assertions, writes, statuses, documents, previews, previewDelay, pendingTimers: pending.size, trace }) + "\n", () => process.exit(runtimeError ? 2 : 0));
});
