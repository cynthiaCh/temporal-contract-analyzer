"use strict";
const path = require("path");
const { pathToFileURL } = require("url");
const candidate = path.resolve(process.argv[2] || "");
const schedule = process.argv[3];
const baseline = process.argv[4] === "baseline";
let now = 0, serial = 0, runtimeError = null, previewDelay = null;
const pending = new Map();
const assertions = [], trace = [], writes = [], statuses = [], documents = [], projectionEvents = [], previews = [];
let visible = null, projection = { selected: null, trail: [] };
const retainedVisits = new Map();
let selectionRequest = 0, navigationEpoch = 0, lastRetainedVisit = -Infinity;
function snapshot(value) {
  if (Array.isArray(value)) return value.map(snapshot);
  if (value && typeof value === "object") return Object.fromEntries(Object.keys(value).sort().map(key => [key, snapshot(value[key])]));
  return value;
}
const equal = (a, b) => JSON.stringify(snapshot(a)) === JSON.stringify(snapshot(b));
const check = (id, actual, expected) => assertions.push({ id, actual: snapshot(actual), expected: snapshot(expected), passed: equal(actual, expected) });
const record = (type, detail = {}) => trace.push({ time: now, type, ...snapshot(detail) });
const timers = {
  schedule(callback, delay) {
    if (!Number.isFinite(delay) || delay < 0) throw new Error("invalid delay");
    const id = ++serial; pending.set(id, { callback, at: now + delay }); record("timer-scheduled", { id, delay }); return id;
  },
  cancel(id) { pending.delete(id); record("timer-cancelled", { id }); },
};
function advance(target) {
  if (target < now) throw new Error("clock cannot go backwards");
  let steps = 0;
  while (true) {
    const next = [...pending].filter(([, t]) => t.at <= target).sort((a, b) => a[1].at - b[1].at || a[0] - b[0])[0];
    if (!next) break;
    if (++steps > 300) throw new Error("timers did not quiesce");
    pending.delete(next[0]); now = next[1].at; record("timer-fired", { id: next[0] }); next[1].callback();
  }
  now = target;
}
const pairs = () => writes.map(({ id, text }) => [id, text]);
const badges = () => statuses.map(({ id, text }) => [id, text]);
const visit = (id, requestOrdinal) => id === null ? null : { id, visit: retainedVisits.get(requestOrdinal) };
const documentVisit = () => visible === null ? null : { id: visible.id, visit: visible.visit };
async function main() {
  const config=require('./adapter.json');let loaded;
  if(['java','python3','php','ruby','go'].includes(config.runtime)){const l=require('./native-launch.cjs').launch(candidate,__dirname);loaded=require('./bridge.cjs')(l.command,{env:l.env});}
  else loaded=await require('./framework-loader.cjs').load(candidate);
  const {createDraftStore,createWorkspace,createSearchPreview}=loaded;
  const actual = createDraftStore({ A: "seed-A", B: "seed-B", C: "seed-C" });
  const store = {
    read: id => actual.read(id),
    subscribe: callback => actual.subscribe(callback),
    write(id, text) { writes.push({ time: now, id, text }); record("write-enter", { id, text }); const result = actual.write(id, text); record("write-return", { id, text }); return result; },
  };
  let onSaved = () => {};
  const workspace = createWorkspace({ store, timers,
    renderDocument(value) { visible = snapshot(value); documents.push({ time: now, value: snapshot(value) }); record("document", { value }); },
    renderStatus(value) { statuses.push({ time: now, ...snapshot(value) }); record("badge", value); },
    renderProjection(value) { projection = snapshot(value); projectionEvents.push({ time: now, value: snapshot(value) }); record("projection", value); },
    onSaved(event, navigation) {
      record("saved-callback-enter", event);
      onSaved(event, Object.fromEntries(["select", "edit", "close"].map(name => [name, (...args) => invoke(name, args, navigation)])));
      record("saved-callback-return", event);
    },
  });
  function invoke(name, args, target) {
    const epoch = name === "edit" ? navigationEpoch : ++navigationEpoch;
    const ordinal = name === "select" ? ++selectionRequest : null;
    record("navigation-enter", { name, args, ordinal });
    const result = target[name](...args);
    if (name === "select" && epoch === navigationEpoch) {
      const selected = workspace.selection();
      check("editor-visit-is-monotone-" + ordinal, selected !== null && Number.isFinite(selected.visit) && selected.visit > lastRetainedVisit, true);
      if (selected !== null) {
        retainedVisits.set(ordinal, selected.visit);
        lastRetainedVisit = selected.visit;
      }
    }
    record("navigation-return", { name, ordinal, document: documentVisit(), outline: projection.selected });
    return result;
  }
  const nav = Object.fromEntries(["select", "edit", "close"].map(name => [name, (...args) => invoke(name, args, workspace)]));
  const preview = createSearchPreview({ timers, publish(value) { previews.push({ time: now, ...value }); record("preview", value); } });
  function aligned(label, id, number, history) {
    const selected = visit(id, number);
    check("editor-" + label, documentVisit(), selected);
    check("editor-api-" + label, workspace.selection(), selected);
    check("projection-outline-" + label, projection.selected, selected);
    check("projection-history-" + label, projection.trail, history.map(([key, n]) => visit(key, n)));
  }
  function finish(expectedWrites, expectedBadges) {
    const priorDocument = snapshot(documentVisit());
    const priorSelection = snapshot(workspace.selection());
    const priorProjection = snapshot(projection);
    advance(600);
    check("editor-no-late-selection", documentVisit(), priorDocument);
    check("editor-api-no-late-selection", workspace.selection(), priorSelection);
    check("projection-no-late-mutation", projection, priorProjection); check("persistence-exact-writes", pairs(), expectedWrites); check("badge-exact-output", badges(), expectedBadges);
    const expected = { A: "seed-A", B: "seed-B", C: "seed-C" };
    for (const [id, text] of expectedWrites) expected[id] = text;
    check("persistence-record-values", Object.fromEntries(Object.keys(expected).map(id => [id, store.read(id)])), expected);
    check("timer-quiescent", pending.size, 0);
  }
  switch (schedule) {
    case "quiet-burst": {
      nav.select("A"); nav.edit("one"); advance(30); nav.edit("two"); advance(80); nav.edit("three"); advance(199);
      check("persistence-no-early-save", pairs(), baseline ? [["A", "one"], ["A", "two"], ["A", "three"]] : []);
      advance(200); const expected = baseline ? [["A", "one"], ["A", "two"], ["A", "three"]] : [["A", "three"]];
      aligned("ordinary-active", "A", 1, [["A", 1]]); finish(expected, expected); break;
    }
    case "second-burst": {
      nav.select("A"); nav.edit("one"); advance(120); nav.edit("two"); advance(150); nav.edit("three"); advance(269);
      check("persistence-second-burst-waits", pairs(), baseline ? [["A", "one"], ["A", "two"], ["A", "three"]] : [["A", "one"]]); advance(270);
      const expected = baseline ? [["A", "one"], ["A", "two"], ["A", "three"]] : [["A", "one"], ["A", "three"]];
      aligned("later-burst", "A", 1, [["A", 1]]); finish(expected, expected); break;
    }
    case "close-before-deadline": {
      nav.select("A"); nav.edit("kept-A"); advance(20); nav.close();
      check("persistence-before-close-return", store.read("A"), "kept-A"); aligned("closed", null, null, [["A", 1]]);
      check("badge-no-departure-output", badges(), baseline ? [["A", "kept-A"]] : []);
      finish([["A", "kept-A"]], baseline ? [["A", "kept-A"]] : []); break;
    }
    case "switch-before-deadline": {
      nav.select("A"); nav.edit("kept-A"); advance(20); nav.select("B");
      check("persistence-before-select-return", store.read("A"), "kept-A"); check("persistence-new-document-unchanged", store.read("B"), "seed-B");
      aligned("ordinary-switch", "B", 2, [["A", 1], ["B", 2]]); nav.edit("kept-B"); advance(140);
      finish([["A", "kept-A"], ["B", "kept-B"]], baseline ? [["A", "kept-A"], ["B", "kept-B"]] : [["B", "kept-B"]]); break;
    }
    case "same-document-reopen": {
      nav.select("A"); nav.edit("first-A"); advance(20); nav.close(); nav.select("A");
      aligned("reopened-visit", "A", 2, [["A", 1], ["A", 2]]); check("editor-restores-persisted-text", visible.text, "first-A");
      nav.edit("second-A"); advance(140); nav.close(); nav.close();
      aligned("closed-again", null, null, [["A", 1], ["A", 2]]);
      finish([["A", "first-A"], ["A", "second-A"]], baseline ? [["A", "first-A"], ["A", "second-A"]] : [["A", "second-A"]]); break;
    }
    case "reentrant-select-on-flush":
    case "reentrant-close-on-flush":
    case "reentrant-same-target-on-flush":
    case "close-flush-select": {
      nav.select("A"); nav.edit("departing-A"); advance(20);
      let callbacks = 0;
      const closeOuter = schedule === "close-flush-select";
      const closeInner = schedule === "reentrant-close-on-flush";
      const sameTarget = schedule === "reentrant-same-target-on-flush";
      onSaved = (event, navigation) => {
        if (event.id !== "A") return;
        callbacks++;
        if (closeInner) navigation.close(); else navigation.select(sameTarget ? "B" : "C");
      };
      if (closeOuter) nav.close(); else nav.select("B");
      // The same inputs contain no pending baseline save when navigation starts:
      // its write completed before the integration was armed.
      const target = baseline ? (closeOuter ? null : "B") : closeInner ? null : sameTarget ? "B" : "C";
      const number = baseline ? 2 : closeOuter ? 2 : 3;
      const history = [["A", 1]];
      if (target) history.push([target, number]);
      check("integration-inline-callback-count", callbacks, baseline ? 0 : 1);
      check("persistence-departing-saved-before-return", store.read("A"), "departing-A");
      aligned("after-reentrant-return", target, number, history);
      onSaved = () => {};
      nav.edit("next-visit"); advance(140);
      const expected = [["A", "departing-A"]]; if (target) expected.push([target, "next-visit"]);
      aligned("after-successor-edit", target, number, history);
      finish(expected, baseline ? expected : expected.slice(1)); break;
    }
    case "timer-save-select": {
      nav.select("A"); onSaved = (event, navigation) => { if (event.id === "A") navigation.select("B"); };
      nav.edit("timer-A"); advance(120); aligned("timer-navigation", "B", 2, [["A", 1], ["B", 2]]);
      check("badge-retired-in-delivery", badges(), []); onSaved = () => {}; nav.edit("timer-B"); advance(240);
      finish([["A", "timer-A"], ["B", "timer-B"]], [["B", "timer-B"]]); break;
    }
    case "reentrant-edit": {
      nav.select("A"); let edited = false;
      onSaved = (event, navigation) => { if (!edited) { edited = true; navigation.edit("two"); } };
      nav.edit("one"); advance(120);
      check("persistence-new-batch-survives", pairs(), baseline ? [["A", "one"], ["A", "two"]] : [["A", "one"]]);
      advance(239); check("persistence-new-batch-deadline", pairs(), baseline ? [["A", "one"], ["A", "two"]] : [["A", "one"]]); advance(240);
      aligned("reentrant-edit", "A", 1, [["A", 1]]);
      finish([["A", "one"], ["A", "two"]], baseline ? [["A", "two"], ["A", "one"]] : [["A", "one"], ["A", "two"]]); break;
    }
    case "preview-delay": {
      preview.query("latest"); advance(39); check("preview-not-early", previews, []); advance(40); const at40 = snapshot(previews); advance(119); check("preview-no-middle-deadline", previews, at40); advance(120);
      const values = previews.map(({ time, query }) => [time, query]); previewDelay = equal(values, [[40, "latest"]]) ? 40 : equal(values, [[120, "latest"]]) ? 120 : null;
      check("preview-recognized-delay", previewDelay === 40 || previewDelay === 120, true); if (baseline) check("preview-original-delay", previewDelay, 40);
      advance(600); check("preview-published-once", previews.length, 1); break;
    }
    case "preview-hide": {
      preview.query("discard"); advance(10); preview.hide(); check("preview-hide-does-not-flush", previews, []); advance(600); check("preview-hidden-no-output", previews, []); break;
    }
    case "preview-reuse": {
      preview.query("old"); advance(10); preview.hide(); advance(20); preview.query("new"); advance(59); check("preview-new-not-early", previews, []);
      advance(60); const at60 = snapshot(previews); advance(139); check("preview-reuse-no-middle-deadline", previews, at60); advance(140);
      const values = previews.map(({ time, query }) => [time, query]); previewDelay = equal(values, [[60, "new"]]) ? 40 : equal(values, [[140, "new"]]) ? 120 : null;
      check("preview-reuse-policy", previewDelay === 40 || previewDelay === 120, true); advance(600); check("preview-reuse-once", previews.length, 1); break;
    }
    default: throw new Error(`unknown schedule ${schedule}`);
  }
  check("schedule-quiescent", pending.size, 0);
}
main().catch(error => { runtimeError = String(error.stack || error); }).finally(() => {
  process.stdout.write(JSON.stringify({ schedule, baseline, passed: runtimeError === null && assertions.length > 0 && assertions.every(item => item.passed), runtimeError, assertions, writes, statuses, documents, projectionEvents, previews, previewDelay, pendingTimers: pending.size, trace }) + "\n", () => process.exit(runtimeError ? 2 : 0));
});
