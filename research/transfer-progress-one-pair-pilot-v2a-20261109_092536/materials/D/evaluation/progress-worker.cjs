"use strict";
const path = require("path");
const { pathToFileURL } = require("url");
const candidate = path.resolve(process.argv[2]), schedule = process.argv[3];
const assertions = [], trace = [];
let runtimeError = null, step = 0;
const copy = value => JSON.parse(JSON.stringify(value));
const log = (type, data = {}) => trace.push({ step: ++step, type, ...copy(data) });
const check = (id, actual, expected) => assertions.push({ id, actual: copy(actual), expected: copy(expected),
  passed: JSON.stringify(actual) === JSON.stringify(expected), traceIndex: trace.length });

async function main() {
  const { createTransferWorkspace } = await import(pathToFileURL(path.join(candidate, "src/workspace.js")).href);
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
      start() { startDepth++; log("host.start.enter", {fileId, startDepth}); feed.emit(); log("host.start.return", {fileId, startDepth}); startDepth--; },
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
    onCancel(event) { log("host.cancel",{attemptId:event.attemptId}); },
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
  if (schedule === "progress-normal") A.progressFeed.emit();
  if (schedule.startsWith("progress-accepted-decode")) {
    A.progressFeed.emit(true);
    if (schedule === "progress-accepted-decode-after-hide") { hide(); A.progressFeed.emit(); }
    else if (schedule === "progress-accepted-decode-after-reopen") select(A);
    else expectedVisible.push(expectedHistory[expectedHistory.length - 1]);
    for (const resolve of resolvers) resolve();
    await Promise.resolve(); await Promise.resolve();
  }
  if (schedule === "progress-live-retry") retry();
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
  hostVisit = null; hostFile = null; api.dispose();
  check("progress.listeners_released", feeds.map(x=>x.target.listeners.size), feeds.map(()=>0));
  check("progress.transfers_cancelled", signals.every(x=>x.signal.aborted), true);
  const before = history.length;
  for (const feed of feeds) feed.emit();
  await Promise.resolve();
  check("progress.no_new_work_after_dispose", history.length, before);
}
main().catch(error => { runtimeError = String(error.stack || error); }).finally(() => {
  process.stdout.write(JSON.stringify({schedule, passed:runtimeError===null && assertions.every(x=>x.passed), runtimeError, assertions, trace}) + "\n");
});
