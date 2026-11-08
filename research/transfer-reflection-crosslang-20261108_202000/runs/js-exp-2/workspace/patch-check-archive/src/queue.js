import { createTransfer } from "./transfer.js";

// Queue records are retained even when their originating panel visit ends.
export function makeQueueRecord(file, attemptId, visitId, kind) {
  return { fileId: file.id, attemptId, visitId, kind };
}

export function enqueueTransfer(state, visit, kind) {
  const attemptId = ++state.nextAttempt;
  state.record(makeQueueRecord(visit.file, attemptId, visit.id, kind));
  // This is installed before subscription because a warm feed can deliver
  // synchronously while createTransfer is still constructing its handle.
  visit.activeAttemptId = attemptId;
  let lastShownSequence = 0;
  const progress = {
    record(frame) { state.recordProgress({ fileId: visit.file.id, attemptId, frame }); },
    receive(frame, sequence) {
      if (state.current === visit && visit.activeAttemptId === attemptId && sequence > lastShownSequence) {
        lastShownSequence = sequence;
        state.showProgress({ fileId: visit.file.id, attemptId, frame });
      }
    },
    isActive() { return !state.disposed && state.current === visit && visit.activeAttemptId === attemptId; },
  };
  const handle = createTransfer(visit.file, attemptId, state.transport, state.onCancel, progress);
  state.tasks.set(attemptId, handle);
  return handle;
}
