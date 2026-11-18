"use strict";
const path = require("path");
const { pathToFileURL } = require("url");

module.exports=async function(candidate,schedule){
let loaded;
const assertions = [], trace = [];
let runtimeError = null, step = 0;
const clone = value => JSON.parse(JSON.stringify(value));
const log = (type, data = {}) => trace.push({ step: ++step, type, ...clone(data) });
const check = (id, actual, expected) => assertions.push({ id, actual: clone(actual), expected: clone(expected),
  passed: JSON.stringify(actual) === JSON.stringify(expected), traceIndex: trace.length });
const compact = entry => ({ fileId: entry.fileId, attemptId: entry.attemptId, seq: entry.frame.seq });

async function main() {
  loaded=require("./loader.cjs").load(candidate,__dirname);
  const {createTransferWorkspace,collectProgressTelemetry}=loaded;
  let api, detachAction = null, progressAction = null, cancelAction=null;
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
        log("feed.decode",{fileId,seq:packet.seq});
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
    onCancel({ file, attemptId }) { log("cancel", { fileId: file.id, attemptId });if(cancelAction){const action=cancelAction;cancelAction=null;action();} },
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

  if (schedule === "accepted-after-dispose") {
    select(A);A.progressFeed.emit(true);api.dispose();A.progressFeed.emit();A.progressFeed.resolve(2);await settle();
    check("disposed.audit-retained",audits.map(x=>x.seq),[1,2]);check("disposed.visible-silent",visible.map(x=>x.seq),[1]);
    check("disposed.no-new-decode",trace.filter(x=>x.type==="feed.decode").map(x=>x.seq),[1,2]);
  } else if(schedule === "same-file-reopen") {
    select(A);A.progressFeed.emit(true);select(A);A.progressFeed.resolve(2);await settle();
    check("reopen.new-visit",api.snapshot().visitId,2);check("reopen.audit-retained",audits.map(x=>[x.attemptId,x.seq]),[[1,1],[2,3],[1,2]]);
    check("reopen.old-visit-ui-silent",visible.map(x=>[x.attemptId,x.seq]),[[1,1],[2,3]]);
  } else if(schedule === "retry-cancel-navigation") {
    select(A);cancelAction=()=>select(B);api.retry();
    check("retry.entry-command-retained",records.map(x=>[x.fileId,x.attemptId,x.visitId,x.kind]),[["A",1,1,"select"],["B",2,2,"select"],["A",3,1,"retry"]]);
    check("retry.new-owner",api.snapshot().fileId,"B");check("retry.no-stale-notice",notices.map(x=>x.attemptId),[1,2]);
    check("retry.current-physical-owner",signals.filter(x=>!x.signal.aborted).map(x=>x.attemptId),[2]);
    check("retry.cancel-before-captured-enqueue",trace.findIndex(x=>x.type==="cancel"&&x.attemptId===1)<trace.findIndex(x=>x.type==="queue.record"&&x.attemptId===3),true);
    check("retry.no-retired-decode",trace.filter(x=>x.type==="feed.decode").map(x=>[x.fileId,x.seq]),[["A",1],["B",1]]);
  } else if(schedule === "empty-and-disposed") {
    check("empty.retry",api.retry(),null);api.hide();api.dispose();api.dispose();check("disposed.select",api.select(A),null);check("disposed.retry",api.retry(),null);
    check("disposed.no-commands",records,[]);check("disposed.no-transfers",signals.length,0);
  } else if(schedule === "telemetry-after-stop") {
    const T=makeFeed("T"),deltas=[];const stop=collectProgressTelemetry(T,f=>deltas.push(f.seq));T.emit(true);stop();stop();T.emit();T.resolve(2);await settle();
    check("telemetry.admitted-completion-retained",deltas,[2]);check("telemetry.no-new-decode",trace.filter(x=>x.type==="feed.decode").map(x=>x.seq),[2]);check("telemetry.stopped",T.target.listeners.size,0);
  } else if(schedule === "start-hide-admission") {
    const start=A.progressFeed.start.bind(A.progressFeed);A.progressFeed.start=()=>{start();A.progressFeed.emit();};progressAction=()=>hide();select(A);
    check("start-hide.only-first-admitted",trace.filter(x=>x.type==="feed.decode").map(x=>x.seq),[1]);check("start-hide.audit",audits.map(x=>x.seq),[1]);check("start-hide.owner",api.snapshot().fileId,null);
  } else if(schedule === "frame-values-reversed") {
    // Full frames can reset loaded and carry arbitrary source sequence values.
    const decode=A.progressFeed.decode.bind(A.progressFeed);A.progressFeed.decode=packet=>{const f={seq:101-packet.seq,loaded:100-packet.loaded};const v=decode(packet);return v&&typeof v.then==='function'?v.then(()=>f):f;};
    select(A);A.progressFeed.emit(true);A.progressFeed.emit();A.progressFeed.resolve(2);await settle();await settle();
    check("values.audit-completion-order",audits.map(x=>x.seq),[100,98,99]);check("values.arrival-not-payload",visible.map(x=>x.seq),[100,98]);
  } else if(schedule === "framework-unmount") {
    select(A);A.progressFeed.emit(true);if(loaded.unmount)loaded.unmount();else api.dispose();A.progressFeed.emit();A.progressFeed.resolve(2);await settle();
    check("unmount.accepted-audit",audits.map(x=>x.seq),[1,2]);check("unmount.no-visible-completion",visible.map(x=>x.seq),[1]);check("unmount.physical-stop",signals.every(x=>x.signal.aborted),true);
    // React ref state remains callable only through the captured session API; no DOM claim after unmount.
  } else if (schedule === "telemetry-scope") {
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

  if(loaded.flush&&schedule!=="framework-unmount"){await loaded.flush();const owner=api.snapshot();if(!owner.disposed)check("framework.rendered-owner",loaded.rendered().includes((owner.fileId||"closed")+":"+(owner.attemptId||0)),true);}
  const expectedOwner = schedule==="framework-unmount"?null:api.snapshot().fileId;
  check("ownership.listener-count", Object.values(files).map(file => file.progressFeed.target.listeners.size),
    ["A", "B", "C"].map(id => expectedOwner === id ? 1 : 0));
  const byteCountIncluded = records.length > 0 && records.every(x => x.byteCount === files[x.fileId].size);
  check("queue.exact-field-scope",records.every(x=>JSON.stringify(Object.keys(x).sort())===JSON.stringify((Object.hasOwn(x,"byteCount")?["fileId","attemptId","visitId","kind","byteCount"]:["fileId","attemptId","visitId","kind"]).sort())),true);
  detachAction = null; progressAction = null; cancelAction=null;if(schedule!=="framework-unmount")api.dispose();
  check("cleanup.zero-listeners", Object.values(files).map(file => file.progressFeed.target.listeners.size), [0, 0, 0]);
  check("cleanup.zero-transfers", signals.every(x => x.signal.aborted), true);
  return { byteCountIncluded };
}

let extra={byteCountIncluded:false};
try{extra=await main();}catch(error){runtimeError=String(error.stack||error);}
try{if(loaded)loaded.close();}catch(error){runtimeError=String(error.stack||error);}
return {schedule,passed:runtimeError===null&&assertions.every(x=>x.passed),runtimeError,assertions,trace,...extra};
};
