import { createTransfer } from "./transfer.js";
export function makeQueueRecord(file, attemptId, visitId, kind) { return { fileId: file.id, attemptId, visitId, kind }; }
export function enqueueTransfer(state, visit, kind) {
  const attemptId = ++state.nextAttempt;
  if (visit.progressReceived === undefined) { visit.progressReceived = 0; visit.progressPublished = 0; }
  state.record(makeQueueRecord(visit.file, attemptId, visit.id, kind));
  const progress = { admit: () => state.current === visit && !state.disposed ? ++visit.progressReceived : null,
    record: frame => state.recordProgress({ fileId: visit.file.id, attemptId, frame }),
    receive: (frame, order) => { if (state.current === visit && order > visit.progressPublished) {
      visit.progressPublished = order; state.showProgress({ fileId: visit.file.id, attemptId, frame }); } } };
  const handle = createTransfer(visit.file, attemptId, state.transport, state.onCancel, progress); state.tasks.set(attemptId, handle); return handle;
}
