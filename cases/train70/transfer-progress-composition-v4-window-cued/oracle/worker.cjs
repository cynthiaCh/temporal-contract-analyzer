"use strict";
const path = require("path");
const { pathToFileURL } = require("url");

const candidate = path.resolve(process.argv[2] || "");
const schedule = process.argv[3];
const assertions = [], trace = [];
let runtimeError = null, step = 0;
const clone = value => JSON.parse(JSON.stringify(value));
const log = (type, data = {}) => trace.push({ step: ++step, type, ...clone(data) });
const check = (id, actual, expected) => assertions.push({ id, actual: clone(actual), expected: clone(expected),
  passed: JSON.stringify(actual) === JSON.stringify(expected), traceIndex: trace.length });
const compact = entry => ({ fileId: entry.fileId, attemptId: entry.attemptId, seq: entry.frame.seq });

async function main() {
  const { createTransferWorkspace, collectProgressTelemetry } = await import(pathToFileURL(path.join(candidate, "src/workspace.js")).href);
  let api, detachAction = null, progressAction = null;
  const records = [], notices = [], audits = [], visible = [], signals = [];

  class DetachingTarget extends EventTarget {
    constructor(name) { super(); this.name = name; this.listeners = new Set(); }
    addEventListener(type, listener, options) {
      if (type === "progress") this.listeners.add(listener);
      return super.addEventListener(type, listener, options);
    }
    removeEventListener(type, listener, options) {
      const installed = type === "progress" && this.listeners.delete(listener);
      const result = super.removeEventListener(type, listener, options);
      if (installed) {
        log("feed.detach", { fileId: this.name });
        if (detachAction) { const action = detachAction; detachAction = null; action(); }
      }
      return result;
    }
  }

  function makeFeed(fileId) {
    let seq = 0;
    const pending = new Map();
    const feed = {
      fileId,
      target: new DetachingTarget(fileId),
      starts: 0,
      emit(deferred = false) {
        const packet = { seq: ++seq, loaded: seq * 10, deferred };
        log("feed.emit", { fileId, seq, deferred });
        const event = new Event("progress"); event.detail = packet;
        feed.target.dispatchEvent(event);
        return packet.seq;
      },
      start() { feed.starts++; log("feed.start", { fileId, starts: feed.starts }); feed.emit(); },
      decode(packet) {
        const frame = { seq: packet.seq, loaded: packet.loaded };
        if (!packet.deferred) return frame;
        return new Promise(resolve => pending.set(packet.seq, () => resolve(frame)));
      },
      resolve(frameSeq) {
        const resolve = pending.get(frameSeq);
        if (!resolve) throw new Error(`missing deferred ${fileId}:${frameSeq}`);
        pending.delete(frameSeq); resolve();
      },
    };
    return feed;
  }

  const A = { id: "A", size: 101, progressFeed: makeFeed("A") };
  const B = { id: "B", size: 202, progressFeed: makeFeed("B") };
  const C = { id: "C", size: 303, progressFeed: makeFeed("C") };
  const files = { A, B, C };
  api = createTransferWorkspace({
    transport({ file, attemptId, signal }) { signals.push({ fileId: file.id, attemptId, signal }); log("transport", { fileId: file.id, attemptId }); },
    onCancel({ file, attemptId }) { log("cancel", { fileId: file.id, attemptId }); },
    record(entry) { records.push(clone(entry)); log("queue.record", entry); },
    showQueued(entry) { notices.push(clone(entry)); log("queue.notice", entry); },
    recordProgress(entry) { audits.push(compact(entry)); log("progress.audit", compact(entry)); },
    showProgress(entry) {
      const value = compact(entry); visible.push(value); log("progress.visible", value);
      if (progressAction) { const action = progressAction; progressAction = null; action(value); }
    },
  });

  const select = file => { log("host.select", { fileId: file.id }); return api.select(file); };
  const hide = () => { log("host.hide"); api.hide(); };
  const settle = async () => { await Promise.resolve(); await Promise.resolve(); };

  if (schedule === "telemetry-scope") {
    const T = makeFeed("T"), deltas = [];
    const stop = collectProgressTelemetry(T, frame => deltas.push(frame.seq));
    T.emit();
    check("telemetry.live-deltas-only", deltas, [2]);
    stop();
    check("telemetry.listener-released", T.target.listeners.size, 0);
  } else if (schedule === "warm-bootstrap") {
    select(A);
    check("warm.audit", audits, [{ fileId: "A", attemptId: 1, seq: 1 }]);
    check("warm.visible", visible, [{ fileId: "A", attemptId: 1, seq: 1 }]);
  } else if (schedule === "start-switch-admission") {
    const start = A.progressFeed.start.bind(A.progressFeed);
    A.progressFeed.start = () => { start(); A.progressFeed.emit(); };
    progressAction = value => { if (value.fileId === "A" && value.seq === 1) select(B); };
    select(A);
    check("start-switch.audit", audits, [
      { fileId: "A", attemptId: 1, seq: 1 }, { fileId: "B", attemptId: 2, seq: 1 },
    ]);
    check("start-switch.visible", visible, [
      { fileId: "A", attemptId: 1, seq: 1 }, { fileId: "B", attemptId: 2, seq: 1 },
    ]);
    check("start-switch.owner", api.snapshot().fileId, "B");
  } else if (schedule === "accepted-after-hide") {
    select(A); A.progressFeed.emit(true); hide(); A.progressFeed.resolve(2); await settle();
    check("retired.audit-retained", audits, [
      { fileId: "A", attemptId: 1, seq: 1 }, { fileId: "A", attemptId: 1, seq: 2 },
    ]);
    check("retired.ui-silent", visible, [{ fileId: "A", attemptId: 1, seq: 1 }]);
  } else if (schedule === "frame-in-order") {
    select(A); A.progressFeed.emit(true); A.progressFeed.emit(true);
    A.progressFeed.resolve(2); await settle(); A.progressFeed.resolve(3); await settle();
    check("ordered.audit", audits.map(x => x.seq), [1, 2, 3]);
    check("ordered.visible", visible.map(x => x.seq), [1, 2, 3]);
  } else if (schedule === "frame-reversed") {
    select(A); A.progressFeed.emit(true); A.progressFeed.emit(); A.progressFeed.resolve(2); await settle();
    check("reversed.audit-all", audits.map(x => x.seq), [1, 3, 2]);
    check("reversed.no-ui-rollback", visible.map(x => x.seq), [1, 3]);
  } else if (schedule === "cleanup-switch" || schedule === "cleanup-hide") {
    select(A);
    detachAction = schedule === "cleanup-switch" ? () => select(C) : () => hide();
    select(B);
    check("cleanup.owner", api.snapshot().fileId, schedule === "cleanup-switch" ? "C" : null);
    check("cleanup.superseded-b-not-started", B.progressFeed.starts, 0);
    check("cleanup.audit", audits, schedule === "cleanup-switch" ? [
      { fileId: "A", attemptId: 1, seq: 1 }, { fileId: "C", attemptId: 2, seq: 1 },
    ] : [{ fileId: "A", attemptId: 1, seq: 1 }]);
  } else if (schedule === "composed-reverse-cleanup-switch") {
    select(A); A.progressFeed.emit(true);
    detachAction = () => select(C);
    progressAction = value => { if (value.fileId === "A" && value.seq === 3) select(B); };
    A.progressFeed.emit();
    A.progressFeed.resolve(2); await settle();
    A.progressFeed.emit(); C.progressFeed.emit();
    check("composition.owner", api.snapshot().fileId, "C");
    check("composition.superseded-b-not-started", B.progressFeed.starts, 0);
    check("composition.audit-split", audits, [
      { fileId: "A", attemptId: 1, seq: 1 }, { fileId: "A", attemptId: 1, seq: 3 },
      { fileId: "C", attemptId: 2, seq: 1 }, { fileId: "A", attemptId: 1, seq: 2 },
      { fileId: "C", attemptId: 2, seq: 2 },
    ]);
    check("composition.current-fresh-ui", visible, [
      { fileId: "A", attemptId: 1, seq: 1 }, { fileId: "A", attemptId: 1, seq: 3 },
      { fileId: "C", attemptId: 2, seq: 1 }, { fileId: "C", attemptId: 2, seq: 2 },
    ]);
  } else if (schedule === "retry-preserved") {
    select(A); A.progressFeed.emit(true); api.retry(); A.progressFeed.resolve(2); await settle();
    check("retry.records", records.map(x => ({ fileId: x.fileId, attemptId: x.attemptId, visitId: x.visitId, kind: x.kind })), [
      { fileId: "A", attemptId: 1, visitId: 1, kind: "select" },
      { fileId: "A", attemptId: 2, visitId: 1, kind: "retry" },
    ]);
    check("retry.audit", audits, [
      { fileId: "A", attemptId: 1, seq: 1 }, { fileId: "A", attemptId: 2, seq: 3 },
      { fileId: "A", attemptId: 1, seq: 2 },
    ]);
    check("retry.same-visit-no-rollback", visible, [
      { fileId: "A", attemptId: 1, seq: 1 }, { fileId: "A", attemptId: 2, seq: 3 },
    ]);
    check("retry.one-owner", signals.filter(x => !x.signal.aborted).map(x => x.attemptId), [2]);
    check("retry.notices", notices.map(x => x.attemptId), [1, 2]);
  } else {
    throw new Error(`unknown schedule ${schedule}`);
  }

  const expectedOwner = api.snapshot().fileId;
  check("ownership.listener-count", Object.values(files).map(file => file.progressFeed.target.listeners.size),
    ["A", "B", "C"].map(id => expectedOwner === id ? 1 : 0));
  const byteCountIncluded = records.length > 0 && records.every(x => x.byteCount === files[x.fileId].size);
  detachAction = null; progressAction = null; api.dispose();
  check("cleanup.zero-listeners", Object.values(files).map(file => file.progressFeed.target.listeners.size), [0, 0, 0]);
  check("cleanup.zero-transfers", signals.every(x => x.signal.aborted), true);
  return { byteCountIncluded };
}

main().then(extra => {
  process.stdout.write(JSON.stringify({ schedule, passed: assertions.every(x => x.passed), runtimeError, assertions, trace, ...extra }) + "\n");
}).catch(error => {
  runtimeError = String(error.stack || error);
  process.stdout.write(JSON.stringify({ schedule, passed: false, runtimeError, assertions, trace, byteCountIncluded: false }) + "\n");
});
