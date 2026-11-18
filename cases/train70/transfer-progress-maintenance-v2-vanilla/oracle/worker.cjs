"use strict";
const path = require("path");
const { pathToFileURL } = require("url");
const candidate = path.resolve(process.argv[2]);
const schedule = process.argv[3];
const assertions = [], trace = [], workspaces = [];
let runtimeError = null, step = 0, recordByteCountIncluded = false;
const copy = value => JSON.parse(JSON.stringify(value));
const log = (type, detail = {}) => trace.push({ step: ++step, type, ...copy(detail) });
const check = (id, actual, expected) => assertions.push({ id, actual: copy(actual), expected: copy(expected),
  passed: JSON.stringify(actual) === JSON.stringify(expected), traceIndex: trace.length });
const fileA = { id: "A", size: 103 }, fileB = { id: "B", size: 207 }, fileC = { id: "C", size: 311 };

async function main() {
  const { createTransferWorkspace } = await import(pathToFileURL(path.join(candidate, "src/workspace.js")).href);
  const { createTransfer } = await import(pathToFileURL(path.join(candidate, "src/transfer.js")).href);
  function workspace(name = "main") {
    const records = [], notices = [], stale = [], starts = [], cancels = [];
    let cancelHook = () => {}, raw, visitSerial = 0, currentHostVisit = null, currentHostFile = null;
    const commands = [], origins = new Map();
    raw = createTransferWorkspace({
      transport({ file, attemptId, signal }) {
        const task = { file, attemptId, signal };
        starts.push(task);
        log("transport-start", { name, fileId: file.id, attemptId, signalNative: signal instanceof AbortSignal });
        signal.addEventListener("abort", () => log("transport-aborted", { name, fileId: file.id, attemptId }), { once: true });
      },
      onCancel(event) {
        cancels.push(event.attemptId);
        log("abort-observer-enter", { name, fileId: event.file.id, attemptId: event.attemptId,
          signalAborted: event.signal.aborted, currentVisit: raw.snapshot().visitId });
        cancelHook(event);
        log("abort-observer-return", { name, attemptId: event.attemptId, currentVisit: raw.snapshot().visitId });
      },
      record(entry) {
        const command = commands[commands.length - 1];
        origins.set(entry.attemptId, command ? { originVisit: command.originVisit, fileId: command.file.id } : null);
        records.push(copy(entry));
        log("enqueue-record", { name, entry, hostOrigin: origins.get(entry.attemptId),
          activeAttempts: starts.filter(x => !x.signal.aborted).map(x => x.attemptId) });
      },
      showQueued(notice) {
        const owner = raw.snapshot();
        const origin = origins.get(notice.attemptId);
        const event = { name, fileId: notice.fileId, attemptId: notice.attemptId,
          originVisit: origin ? origin.originVisit : "unbound", currentVisit: currentHostVisit, currentFile: currentHostFile,
          ownerAttempt: owner.attemptId, status: notice.status };
        notices.push(copy(notice));
        if (!origin || origin.originVisit !== currentHostVisit || origin.fileId !== currentHostFile) stale.push(event);
        log("queued-notice", event);
      },
    });
    const w = { name, raw, records, notices, stale, starts, cancels,
      select(file) { currentHostVisit = ++visitSerial; currentHostFile = file.id;
        commands.push({ kind: "select", file, originVisit: currentHostVisit });
        log("select-entry", { name, fileId: file.id, hostVisit: currentHostVisit }); const result = raw.select(file);
        commands.pop(); log("select-return", { name, snapshot: raw.snapshot() }); return result; },
      retry() { const current = raw.snapshot();
        commands.push({ kind: "retry", file: { id: currentHostFile }, originVisit: currentHostVisit });
        log("retry-entry", { name, snapshot: current, hostVisit: currentHostVisit }); const result = raw.retry();
        commands.pop(); log("retry-return", { name, snapshot: raw.snapshot() }); return result; },
      hide() { visitSerial++; currentHostVisit = null; currentHostFile = null;
        log("hide-entry", { name }); raw.hide(); log("hide-return", { name, snapshot: raw.snapshot() }); },
      dispose() { currentHostVisit = null; currentHostFile = null;
        log("dispose-entry", { name }); raw.dispose(); log("dispose-return", { name, snapshot: raw.snapshot() }); },
      hook(callback) { cancelHook = callback; },
      active() { return starts.filter(x => !x.signal.aborted).map(x => x.attemptId); },
    };
    workspaces.push(w); return w;
  }
  function sequence(w) {
    const assert = (id, actual, expected) => check(w.name === "main" ? id : w.name + "." + id, actual, expected);
    assert("attempt.monotonic_unique", w.records.map(x => x.attemptId), w.records.map((_, i) => i + 1));
    assert("attempt.one_native_transfer_per_record", w.starts.map(x => [x.file.id, x.attemptId]), w.records.map(x => [x.fileId, x.attemptId]));
    assert("carrier.native_signals", w.starts.every(x => x.signal instanceof AbortSignal), true);
    assert("cancel.idempotent_observer", new Set(w.cancels).size, w.cancels.length);
    assert("notice.payload_compatible", w.notices, w.notices.map(notice => {
      const entry = w.records.find(item => item.attemptId === notice.attemptId) || {};
      return { fileId: entry.fileId, attemptId: entry.attemptId, visitId: entry.visitId, status: "queued" };
    }));
  }
  function cancelBefore(w, previousId, retryId) {
    const cancel = trace.find(x => x.type === "abort-observer-enter" && x.name === "main" && x.attemptId === previousId);
    const enqueue = trace.find(x => x.type === "enqueue-record" && x.name === "main" && x.entry.attemptId === retryId);
    const id = previousId === 1 ? "retry.cancel_before_enqueue" : "retry.cancel_before_enqueue." + previousId + "." + retryId;
    check(id, !!cancel && !!enqueue && cancel.step < enqueue.step, true);
  }
  const w = workspace();
  if (["retry-normal", "retry-double", "retry-abort-observe"].includes(schedule)) {
    w.select(fileA); const original = w.starts[0];
    let hookReached = false, inRetry = false;
    w.hook(() => { if (inRetry) hookReached = true; });
    inRetry = true; w.retry(); inRetry = false;
    check("retry.previous_aborted", original.signal.aborted, true);
    cancelBefore(w, 1, 2);
    if (schedule === "retry-abort-observe") check("abort.observer_inline", hookReached, true);
    const expected = [1, 2];
    if (schedule === "retry-double") { w.retry(); expected.push(3); cancelBefore(w, 2, 3); }
    check("retry.original_file_retained", w.records.map(x => x.fileId), expected.map(() => "A"));
    check("retry.original_file_identity", w.starts.every(x => x.file === fileA), true);
    check("retry.exactly_once", w.records.length, expected.length);
    check("notice.active_retry_live", w.notices.map(x => x.attemptId), expected);
    check("owner.current_attempt", w.raw.snapshot().attemptId, expected.length);
    check("retry.only_owned_transfer_active", w.active(), [expected.length]);
    w.hide(); check("cleanup.no_active_transfer", w.active(), []);
  } else if (["retry-abort-hide", "retry-abort-switch", "retry-abort-reopen"].includes(schedule)) {
    w.select(fileA);
    const oldVisit = w.raw.snapshot().visitId;
    let armed = true, reached = false, inRetry = false, newOwner = null;
    w.hook(event => {
      if (!armed || event.attemptId !== 1) return;
      armed = false; reached = inRetry && event.signal.aborted;
      log("abort-navigation-hook", { schedule, oldVisit, inRetry, signalAborted: event.signal.aborted });
      if (schedule === "retry-abort-hide") w.hide();
      else if (schedule === "retry-abort-switch") w.select(fileB);
      else { w.hide(); w.select(fileA); }
      newOwner = copy(w.raw.snapshot());
      log("abort-navigation-result", { oldVisit, newOwner });
    });
    inRetry = true; w.retry(); inRetry = false;
    check("abort.navigation_hook_reached", reached, true);
    const accepted = w.records.filter(x => x.kind === "retry" && x.visitId === oldVisit);
    check("retry.original_file_retained", accepted.map(x => x.fileId), ["A"]);
    check("retry.exactly_once", accepted.length, 1);
    check("retry.origin_visit_retained", accepted.map(x => x.visitId), [oldVisit]);
    const acceptedTransfer = accepted.length ? w.starts.find(x => x.attemptId === accepted[0].attemptId) : null;
    check("retry.original_file_identity", !!acceptedTransfer && acceptedTransfer.file === fileA, true);
    cancelBefore(w, 1, accepted.length ? accepted[0].attemptId : -1);
    const expectedOwner = newOwner || { visitId: null, fileId: null, attemptId: null, disposed: false, attempts: 0 };
    const actualOwner = w.raw.snapshot();
    check("owner.new_visit_preserved", [actualOwner.visitId, actualOwner.fileId, actualOwner.attemptId],
      [expectedOwner.visitId, expectedOwner.fileId, expectedOwner.attemptId]);
    if (schedule !== "retry-abort-hide") {
      check("visit.same_file_is_new_identity", newOwner !== null && newOwner.visitId !== oldVisit, true);
      const wantedFile = schedule === "retry-abort-switch" ? "B" : "A";
      check("owner.only_new_visit_active", w.active(), newOwner ? [newOwner.attemptId] : []);
      const oldNewOwnerAttempt = newOwner ? newOwner.attemptId : -1;
      const before = w.records.length;
      const noticeBefore = w.notices.length;
      w.retry();
      check("owner.new_visit_retry_live", w.records.slice(before).map(x => [x.fileId, x.visitId, x.kind]),
        [[wantedFile, newOwner ? newOwner.visitId : null, "retry"]]);
      check("notice.new_visit_retry_live", w.notices.slice(noticeBefore).map(x => [x.fileId, x.visitId]),
        [[wantedFile, newOwner ? newOwner.visitId : null]]);
      const previous = w.starts.find(x => x.attemptId === oldNewOwnerAttempt);
      check("owner.new_visit_retry_cancels_predecessor", !!previous && previous.signal.aborted, true);
      check("owner.new_visit_retry_owns_new_handle", w.active(), [w.raw.snapshot().attemptId]);
      w.hide();
    } else {
      const before = w.records.length;
      w.retry(); check("hidden.retry_not_accepted", w.records.length, before);
    }
    check("cleanup.no_active_transfer", w.active(), []);
  } else if (schedule === "retry-hidden-noop") {
    w.select(fileA); w.hide();
    const before = w.records.length;
    check("hidden.retry_returns_null", w.retry(), null);
    check("hidden.retry_not_accepted", w.records.length, before);
    check("cleanup.no_active_transfer", w.active(), []);
  } else if (schedule === "selection-cleanup") {
    w.select(fileA); let armed = true, hook = false;
    w.hook(() => { if (!armed) return; armed = false; hook = true; w.select(fileC); });
    w.select(fileB);
    check("selection.abort_hook_reached", hook, true);
    check("selection.newer_navigation_wins", w.raw.snapshot().fileId, "C");
    check("selection.superseded_file_not_started", w.records.map(x => x.fileId), ["A", "C"]);
    check("selection.only_new_owner_active", w.active(), [2]);
    w.hide(); check("cleanup.no_active_transfer", w.active(), []);
  } else if (schedule === "cancel-idempotent") {
    let notifications = 0, transportSignal;
    const h = createTransfer(fileA, 7, ({ signal }) => { transportSignal = signal; }, () => { notifications++; });
    check("carrier.initially_active", h.signal.aborted, false);
    check("carrier.same_native_signal", h.signal === transportSignal && h.signal instanceof AbortSignal, true);
    h.cancel(); h.cancel(); h.cancel();
    check("carrier.cancel_synchronous", h.signal.aborted, true);
    check("carrier.cancel_once", notifications, 1);
  } else if (schedule === "independent-workspaces") {
    const other = workspace("other");
    w.select(fileA); other.select(fileB); w.dispose();
    check("workspace.other_still_active", other.active(), [1]);
    other.retry();
    check("workspace.other_retry_live", other.notices.map(x => [x.fileId, x.attemptId]), [["B", 1], ["B", 2]]);
    check("workspace.other_only_retry_active", other.active(), [2]);
    check("workspace.attempt_counters_independent", other.records.map(x => x.attemptId), [1, 2]);
    other.hide(); check("cleanup.other_no_active_transfer", other.active(), []);
  } else if (schedule === "record-scope") {
    w.select(fileA); w.retry();
    const expected = w.records.map(x => ["attemptId", "fileId", "kind", "visitId"]);
    const actual = w.records.map(x => Object.keys(x).sort());
    const extended = w.records.map(x => ["attemptId", "byteCount", "fileId", "kind", "visitId"]);
    recordByteCountIncluded = JSON.stringify(actual) === JSON.stringify(extended) && w.records.every(x => x.byteCount === fileA.size);
    check("record.complete_supported_shape", JSON.stringify(actual) === JSON.stringify(expected) || recordByteCountIncluded, true);
  } else throw new Error("Unknown schedule " + schedule);

  for (const item of workspaces) {
    const assert = (id, actual, expected) => check(item.name === "main" ? id : item.name + "." + id, actual, expected);
    assert("notice.current_visit_only", item.stale, []);
    sequence(item);
    item.dispose(); item.dispose();
    assert("dispose.no_active_transfer", item.active(), []);
    const count = item.records.length;
    item.retry(); item.select(fileC);
    assert("dispose.no_new_commands", item.records.length, count);
  }
}
main().catch(error => { runtimeError = String(error.stack || error); }).finally(() => {
  process.stdout.write(JSON.stringify({ schedule, passed: runtimeError === null && assertions.every(x => x.passed),
    runtimeError, assertions, trace, recordByteCountIncluded }) + "\n");
});
