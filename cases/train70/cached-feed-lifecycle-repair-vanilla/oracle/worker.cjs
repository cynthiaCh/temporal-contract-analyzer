"use strict";
const path = require("path");
const { pathToFileURL } = require("url");
const { getEventListeners } = require("events");
const candidate = path.resolve(process.argv[2]);
const schedule = process.argv[3];
const assertions = [], trace = [], workspaces = [], feeds = [];
let runtimeError = null, metricsBootstrapIncluded = null, step = 0;
const copy = value => JSON.parse(JSON.stringify(value));
const log = (type, detail = {}) => trace.push({ step: ++step, type, ...detail });
const check = (id, actual, expected) => assertions.push({ id,
  passed: JSON.stringify(actual) === JSON.stringify(expected),
  actual: copy(actual), expected: copy(expected), traceIndex: trace.length });
const tuple = frame => [frame.feed, frame.kind, frame.seq];
const snap = token => [token, "snapshot", 0];
const delta = (token, seq = 1) => [token, "delta", seq];
const sorted = values => values.map(value => JSON.stringify(value)).sort();
const settle = () => new Promise(resolve => setImmediate(resolve));
process.on("unhandledRejection", error => { runtimeError = String(error.stack || error); });

async function main() {
  const load = file => import(pathToFileURL(path.join(candidate, "src", file)).href);
  const [{ createFeed }, { createFeedWorkspace }, { collectMetrics }] =
    await Promise.all(["feed.js", "workspace.js", "metrics.js"].map(load));
  function workspace(name = "main") {
    let visit = 0, current = null, paintHook = () => {}, deferPaint = () => false;
    const origins = new WeakMap(), laidOut = new WeakMap();
    const rows = [], counts = [], history = [], decodes = [], paints = [];
    const raw = createFeedWorkspace({
      history: { record(frame) { history.push(tuple(frame)); log("history", { name, frame }); } },
      paintRows(frame, navigation) {
        const origin = origins.get(frame);
        check("rows-owned-by-current-visit", !!origin && origin.visit === visit && current === origin.feed, true);
        rows.push(tuple(frame)); laidOut.set(frame, false);
        log("rows", { name, frame, visit });
        paintHook(frame, navigation);
        if (deferPaint(frame)) {
          return new Promise(resolve => paints.push({ frame, release() {
            laidOut.set(frame, true); log("layout-completed", { name, frame }); resolve();
          } }));
        }
        laidOut.set(frame, true);
      },
      showCount(frame) {
        const origin = origins.get(frame);
        check("count-owned-by-current-visit", !!origin && origin.visit === visit && current === origin.feed, true);
        check("count-after-layout", laidOut.get(frame) === true, true);
        counts.push(tuple(frame)); log("count", { name, frame, visit });
      },
    });
    const api = {
      rows, counts, history, decodes, paints,
      feed(token, shouldDefer = () => false) {
        let feed;
        feed = createFeed(token, { decode(input) {
          const frame = copy(input);
          origins.set(frame, { visit, feed });
          log("decode-accepted", { name, frame, visit });
          if (!shouldDefer(frame)) return frame;
          return new Promise(resolve => decodes.push({ frame, release() {
            log("decode-completed", { name, frame }); resolve(frame);
          } }));
        } });
        feeds.push(feed); return feed;
      },
      select(feed, mode = "synchronous", navigation = raw) {
        visit++; current = feed; log("select", { name, visit, mode }); navigation.select(feed, mode);
      },
      hide(navigation = raw) {
        visit++; current = null; log("hide", { name, visit }); navigation.hide();
      },
      onPaint(callback) { paintHook = callback; },
      deferPaintWhen(predicate) { deferPaint = predicate; },
      releaseDecode(index = 0) {
        const pending = decodes.splice(index, 1)[0];
        check("decode-pending-at-release", !!pending, true);
        if (pending) pending.release();
      },
      releasePaint(index = 0) {
        const pending = paints.splice(index, 1)[0];
        check("paint-pending-at-release", !!pending, true);
        if (pending) pending.release();
      },
      expect(expectedRows, expectedCounts, expectedHistory) {
        check("rows-exact", rows, expectedRows);
        check("count-exact", counts, expectedCounts);
        // History is an exactly-once obligation, not an imposed ordering among
        // independent decode completions.
        check("history-exactly-once", sorted(history), sorted(expectedHistory));
      },
    };
    workspaces.push(api); return api;
  }
  const w = workspace();
  switch (schedule) {
    case "bootstrap-sync":
    case "bootstrap-deferred":
    case "live-delta": {
      const a = w.feed("A");
      w.select(a, schedule === "bootstrap-deferred" ? "deferred" : "synchronous");
      if (schedule === "bootstrap-sync") {
        check("synchronous-first-rows", w.rows, [snap("A")]);
        check("synchronous-first-count", w.counts, [snap("A")]);
      }
      await settle();
      const expected = [snap("A")];
      if (schedule === "live-delta") {
        a.emitDelta(); a.emitDelta(); await settle(); expected.push(delta("A"), delta("A", 2));
      }
      w.expect(expected, expected, expected); break;
    }
    case "decode-live":
    case "decode-hide":
    case "decode-switch":
    case "decode-reopen":
    case "decode-reopen-live": {
      let delay = true;
      const a = w.feed("A", () => delay), b = w.feed("B");
      // Deferred bootstrap isolates an already-existing in-flight decode from
      // the distinct synchronous-listener registration defect.
      w.select(a, "deferred"); await settle();
      check("no-rows-before-decode", w.rows, []);
      check("no-count-before-decode", w.counts, []);
      check("no-history-before-decode", w.history, []);
      const shown = [];
      if (schedule === "decode-hide") w.hide();
      if (schedule === "decode-switch") { w.select(b); shown.push(snap("B")); }
      if (schedule.startsWith("decode-reopen")) {
        w.hide(); delay = false; w.select(a); shown.push(snap("A"));
      }
      if (schedule === "decode-live") shown.push(snap("A"));
      w.releaseDecode(); await settle();
      const saved = schedule === "decode-live" ? [snap("A")] : [...shown, snap("A")];
      if (schedule === "decode-reopen-live") {
        a.emitDelta(); await settle(); shown.push(delta("A")); saved.push(delta("A"));
      }
      w.expect(shown, shown, saved); break;
    }
    case "paint-live":
    case "paint-hide":
    case "paint-switch":
    case "paint-reopen":
    case "paint-reopen-live": {
      let delay = true;
      const a = w.feed("A"), b = w.feed("B");
      w.deferPaintWhen(frame => frame.feed === "A" && delay);
      w.select(a, "deferred"); await settle();
      check("rows-before-layout", w.rows, [snap("A")]);
      check("count-waits-for-layout", w.counts, []);
      const expectedRows = [snap("A")], expectedCounts = [], saved = [snap("A")];
      if (schedule === "paint-hide") w.hide();
      if (schedule === "paint-switch") {
        w.select(b); expectedRows.push(snap("B")); expectedCounts.push(snap("B")); saved.push(snap("B"));
      }
      if (schedule.startsWith("paint-reopen")) {
        w.hide(); delay = false; w.select(a);
        expectedRows.push(snap("A")); expectedCounts.push(snap("A")); saved.push(snap("A"));
      }
      if (schedule === "paint-live") expectedCounts.push(snap("A"));
      w.releasePaint(); await settle();
      if (schedule === "paint-reopen-live") {
        a.emitDelta(); await settle();
        expectedRows.push(delta("A")); expectedCounts.push(delta("A")); saved.push(delta("A"));
      }
      w.expect(expectedRows, expectedCounts, saved); break;
    }
    case "paint-hook-hide":
    case "paint-hook-switch":
    case "bootstrap-hook-hide":
    case "bootstrap-hook-switch":
    case "bootstrap-hook-reopen": {
      const a = w.feed("A"), b = w.feed("B");
      let armed = true;
      const bootstrap = schedule.startsWith("bootstrap-");
      w.onPaint((frame, navigation) => {
        if (!armed || frame.feed !== "A") return;
        armed = false;
        if (schedule.endsWith("switch")) w.select(b, "synchronous", navigation);
        else {
          w.hide(navigation);
          if (schedule.endsWith("reopen")) w.select(a, "synchronous", navigation);
        }
      });
      w.select(a, bootstrap ? "synchronous" : "deferred"); await settle();
      check("paint-hook-reached", armed, false);
      const expectedRows = [snap("A")], expectedCounts = [], saved = [snap("A")];
      if (schedule.endsWith("switch") || schedule.endsWith("reopen")) {
        const token = schedule.endsWith("switch") ? "B" : "A";
        const activeFeed = token === "B" ? b : a;
        expectedRows.push(snap(token)); expectedCounts.push(snap(token)); saved.push(snap(token));
        activeFeed.emitDelta(); await settle();
        expectedRows.push(delta(token)); expectedCounts.push(delta(token)); saved.push(delta(token));
      }
      w.expect(expectedRows, expectedCounts, saved);
      break;
    }
    case "history-after-retire": {
      const a = w.feed("A", frame => frame.kind === "delta");
      w.select(a); await settle(); a.emitDelta(); a.emitDelta();
      w.hide();
      check("listener-detached-before-late-history", getEventListeners(a.target, "batch").length, 0);
      // Removing a listener must not revoke the two accepted decodes. A new
      // emission after removal must not create a third history job.
      a.emitDelta();
      w.releaseDecode(1); await settle(); w.releaseDecode(); await settle();
      w.expect([snap("A")], [snap("A")], [snap("A"), delta("A"), delta("A", 2)]);
      break;
    }
    case "metrics-scope": {
      const feed = createFeed("M"); feeds.push(feed);
      const observed = (await collectMetrics(feed)).map(tuple);
      const excluded = JSON.stringify(observed) === JSON.stringify([delta("M")]);
      metricsBootstrapIncluded = JSON.stringify(observed) === JSON.stringify([snap("M"), delta("M")]);
      check("metrics-valid-complete-policy", excluded || metricsBootstrapIncluded, true);
      log("metrics", { observed, metricsBootstrapIncluded });
      break;
    }
    case "independent-workspaces": {
      const other = workspace("other"), a = w.feed("A"), b = other.feed("B");
      w.select(a); other.select(b); await settle();
      w.hide(); b.emitDelta(); await settle();
      w.expect([snap("A")], [snap("A")], [snap("A")]);
      other.expect([snap("B"), delta("B")], [snap("B"), delta("B")], [snap("B"), delta("B")]);
      break;
    }
    default: throw new Error("Unknown schedule " + schedule);
  }
  for (const instance of workspaces) instance.hide();
  await settle();
  for (const feed of feeds) check("closed-listeners-zero", getEventListeners(feed.target, "batch").length, 0);
  for (const instance of workspaces) {
    check("all-controlled-decodes-released", instance.decodes.length, 0);
    check("all-controlled-layouts-released", instance.paints.length, 0);
    const sizes = [instance.rows.length, instance.counts.length, instance.history.length];
    for (const feed of feeds) feed.emitDelta();
    await settle();
    check("detached-workspace-has-no-new-effects", [instance.rows.length, instance.counts.length, instance.history.length], sizes);
  }
}
main().catch(error => { runtimeError = String(error.stack || error); }).finally(() => {
  process.stdout.write(JSON.stringify({ schedule, passed: !runtimeError && assertions.every(item => item.passed),
    runtimeError, assertions, trace, metricsBootstrapIncluded }) + "\n");
});
