import { createTransfer } from "./transfer.js";

// Queue records are retained even when their originating panel visit ends.
export function makeQueueRecord(file, attemptId, visitId, kind) {
  return { fileId: file.id, attemptId, visitId, kind };
}

export function enqueueTransfer(state, visit, kind) {
  const attemptId = ++state.nextAttempt;
  state.record(makeQueueRecord(visit.file, attemptId, visit.id, kind));
  const progress = {
    isActive() { return state.current === visit; },
    record(frame) { state.recordProgress({ fileId: visit.file.id, attemptId, frame }); },
    receive(frame) {
      if (state.current === visit) state.showProgress({ fileId: visit.file.id, attemptId, frame });
    },
  };
  const handle = createTransfer(visit.file, attemptId, state.transport, state.onCancel, progress);
  state.tasks.set(attemptId, handle);
  return handle;
}
