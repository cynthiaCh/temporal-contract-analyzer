"use strict";
const path = require("path");
const { pathToFileURL } = require("url");
module.exports=async function(candidate,schedule){
let loaded;
const assertions = [], trace = [];
let runtimeError = null, step = 0;
const copy=value=>Array.isArray(value)?value.map(copy):value&&typeof value==='object'?Object.fromEntries(Object.keys(value).sort().map(k=>[k,copy(value[k])])):value;
const log = (type, data = {}) => trace.push({ step: ++step, type, ...copy(data) });
const check = (id, actual, expected) => assertions.push({ id, actual: copy(actual), expected: copy(expected),
  passed: JSON.stringify(copy(actual)) === JSON.stringify(copy(expected)), traceIndex: trace.length });

async function main() {
  loaded=require("./loader.cjs").load(candidate,__dirname);
  const {createTransferWorkspace}=loaded;
  let api, hostVisit = null, hostFile = null, nextVisit = 0, startDepth = 0, armed = true, hookReached = false;
  const commands = [], origins = new Map(), latestAttempt = new Map(), emissions = new Map();
  const records = [], history = [], visible = [], expectedHistory = [], expectedVisible = [], signals = [], resolvers = [], feeds = [];
  const fileKey = (file, seq) => file + ":" + seq;
  class CountedTarget extends EventTarget {
    constructor() { super(); this.listeners = new Set(); }
    addEventListener(type, fn, options) { if (type === "progress") this.listeners.add(fn); super.addEventListener(type, fn, options); }
    removeEventListener(type, fn, options) { if (type === "progress") this.listeners.delete(fn); super.removeEventListener(type, fn, options); }
  }
  function source(fileId) {
    let seq = 0;
    const feed = { target: new CountedTarget(), fileId,
      emit(deferred = false) {
        const packet = { seq: ++seq, loaded: seq * 10, deferred };
        const origin = hostFile === fileId ? hostVisit : null;
        const attemptId = origin === null ? null : latestAttempt.get(origin);
        emissions.set(fileKey(fileId, seq), { originVisit: origin, attemptId, deferred });
        if (origin !== null) {
          const entry = { fileId, attemptId, frame: {seq, loaded: packet.loaded} };
          expectedHistory.push(entry);
          if (!deferred) expectedVisible.push(entry);
        }
        log("host.emit", { fileId, seq, hostVisit, expectedAttempt: attemptId, startDepth, deferred });
        const event = new Event("progress"); event.detail = packet; feed.target.dispatchEvent(event);
      },
      start() { const cachedSeq=seq+1,origin=hostFile===fileId?hostVisit:null; startDepth++; log("host.start.enter", {fileId, startDepth}); feed.emit(); if(origin!==null)check("progress.cached_inline."+fileId+"."+cachedSeq,visible.some(x=>x.entry.fileId===fileId&&x.entry.frame.seq===cachedSeq),true); log("host.start.return", {fileId, startDepth}); startDepth--; },
      decode(packet) {
        const frame = { seq: packet.seq, loaded: packet.loaded };
        if (!packet.deferred) return frame;
        return new Promise(resolve => resolvers.push(() => resolve(frame)));
      },
    };
    feeds.push(feed); return feed;
  }
  const A = {id:"A",size:103,progressFeed:source("A")}, B = {id:"B",size:207,progressFeed:source("B")};
  const select = file => {
    hostVisit = ++nextVisit; hostFile = file.id;
    commands.push({originVisit:hostVisit,fileId:file.id}); log("host.select", {hostVisit,hostFile});
    const value = api.select(file); commands.pop(); return value;
  };
  const hide = () => { hostVisit = null; hostFile = null; log("host.hide"); api.hide(); };
  const retry = () => {
    commands.push({originVisit:hostVisit,fileId:hostFile}); log("host.retry", {hostVisit,hostFile});
    const value = api.retry(); commands.pop(); return value;
  };
  api = createTransferWorkspace({
    transport({file,attemptId,signal}) { signals.push({fileId:file.id,attemptId,signal}); log("host.transport",{fileId:file.id,attemptId}); },
    onCancel(event) { log("host.cancel",{attemptId:event.attemptId}); if(armed&&event.attemptId===1&&schedule.startsWith("progress-retry-abort-")){armed=false;if(schedule.endsWith("switch"))select(B);else {hide();select(A);}} },
    record(entry) {
      const command = commands[commands.length - 1];
      if (command) { origins.set(entry.attemptId, copy(command)); latestAttempt.set(command.originVisit,entry.attemptId); }
      records.push(copy(entry)); log("host.queue.record",entry);
    },
    showQueued(notice) { log("host.queued",notice); },
    recordProgress(entry) {
      const origin = origins.get(entry.attemptId), emitted = emissions.get(fileKey(entry.fileId, entry.frame.seq));
      const event = {entry:copy(entry), origin:origin || null, emitted:emitted || null};
      history.push(event); log("host.progress.audit",event);
    },
    showProgress(entry) {
      const origin = origins.get(entry.attemptId);
      const event = {entry:copy(entry), origin:origin || null, currentVisit:hostVisit};
      visible.push(event); log("host.progress.visible",event);
      if (armed && entry.fileId === "A" && entry.frame.seq === 1 && schedule.includes("during-start")) {
        armed = false; hookReached = startDepth > 0;
        log("host.navigation.hook", {hookReached, startDepth});
        if (schedule === "progress-reopen-during-start") select(A);
        else if (schedule === "progress-hide-emit-during-start") { hide(); A.progressFeed.emit(); }
        else { select(B); A.progressFeed.emit(); }
      }
    },
  });
  select(A);
  if(schedule==="progress-independent-workspaces"){
    const otherHistory=[],otherVisible=[];
    const other=createTransferWorkspace({transport(){},onCancel(){},record(){},showQueued(){},recordProgress:e=>otherHistory.push(copy(e)),showProgress:e=>otherVisible.push(copy(e))});
    const otherFile={id:"Z",size:31,progressFeed:source("Z")};other.select(otherFile);
    hostVisit=null;hostFile=null;api.dispose();const before=otherHistory.length;otherFile.progressFeed.emit();
    check("progress.independent_owner_live",otherHistory.length,before+1);check("progress.independent_owner_visible",otherVisible.length,otherHistory.length);other.dispose();
  }
  if (["progress-normal","progress-framework-unmount"].includes(schedule)) A.progressFeed.emit();
  if (schedule.startsWith("progress-accepted-decode")) {
    A.progressFeed.emit(true);
    if (schedule === "progress-accepted-decode-after-hide") { hide(); A.progressFeed.emit(); }
    else if (schedule === "progress-accepted-decode-after-reopen") select(A);
    else if (schedule === "progress-accepted-decode-after-dispose") {hostVisit=null;hostFile=null;api.dispose();A.progressFeed.emit();}
    else expectedVisible.push(expectedHistory[expectedHistory.length - 1]);
    for (const resolve of resolvers) resolve();
    await Promise.resolve(); await Promise.resolve();
  }
  if (schedule === "progress-live-retry"||schedule.startsWith("progress-retry-abort-")) retry();
  if (schedule.includes("during-start")) {
    check("progress.navigation_hook_reached", hookReached, true);
    const expectedFile = schedule === "progress-hide-emit-during-start" ? null : schedule === "progress-reopen-during-start" ? "A" : "B";
    check("progress.new_visit_ownership", api.snapshot().fileId, expectedFile);
    if (hostVisit !== null) {
      const before = history.length;
      (hostFile === "A" ? A : B).progressFeed.emit();
      check("progress.new_visit_remains_live", history.length > before, true);
    }
  }

  if(loaded.flush){await loaded.flush();if(!api.snapshot().disposed){const owner=api.snapshot();check("framework.actual_rendered_owner",loaded.rendered().includes((owner.fileId||"closed")+":"+(owner.attemptId||0)),true);}}
  const invalidAdmission = event => !event.origin || !event.emitted ||
    event.origin.originVisit !== event.emitted.originVisit || event.entry.attemptId !== event.emitted.attemptId;
  const sortEntries = entries => entries.map(copy).sort((a,b) => a.fileId.localeCompare(b.fileId) || a.frame.seq-b.frame.seq || a.attemptId-b.attemptId);
  const invalid = history.filter(invalidAdmission);
  check("progress.no_new_reception_after_retirement", invalid, []);
  check("progress.accepted_work_complete", sortEntries(history.filter(x=>!invalidAdmission(x)).map(x=>x.entry)), sortEntries(expectedHistory));
  check("progress.visible_current_visit_only", visible.filter(x=>!x.origin || x.origin.originVisit !== x.currentVisit), []);
  check("progress.live_output_complete", sortEntries(visible.filter(x=>x.origin && x.origin.originVisit === x.currentVisit).map(x=>x.entry)), sortEntries(expectedVisible));
  check("progress.initial_status_observed", visible.some(x=>x.entry.fileId==="A" && x.entry.frame.seq===1), true);
  const liveSignals = signals.filter(x=>!x.signal.aborted);
  check("progress.active_owner_count", liveSignals.length, hostVisit === null ? 0 : 1);
  if (hostVisit !== null) check("progress.active_owner_identity", liveSignals.map(x=>x.attemptId), [api.snapshot().attemptId]);
  hostVisit = null; hostFile = null; if(schedule==="progress-framework-unmount"&&loaded.unmount)loaded.unmount();else api.dispose();
  check("progress.listeners_released", feeds.map(x=>x.target.listeners.size), feeds.map(()=>0));
  check("progress.transfers_cancelled", signals.every(x=>x.signal.aborted), true);
  const before = history.length;
  for (const feed of feeds) feed.emit();
  await Promise.resolve();
  check("progress.no_new_work_after_dispose", history.length, before);
}
await main().catch(error=>{runtimeError=String(error.stack||error);});
try{if(loaded)loaded.close();}catch(error){runtimeError=String(error.stack||error);}
return {schedule,passed:runtimeError===null&&assertions.every(x=>x.passed),runtimeError,assertions,trace};
};
