import { enqueueTransfer } from "./queue.js";
import { publishQueued } from "./notice.js";

// A retry click accepts exactly one command for the current visit and file.
export function retryTransfer(state) {
  const visit = state.current;
  if (!visit || !visit.handle || state.disposed) return null;
  const previous = visit.handle;
  previous.cancel();
  // Cancellation callbacks may synchronously change the selected visit or
  // launch another attempt.
  if (state.current !== visit || visit.handle !== previous || state.disposed) return null;
  const handle = enqueueTransfer(state, visit, "retry");
  if (state.current === visit && visit.activeAttemptId === handle.attemptId) visit.handle = handle;
  else handle.cancel();
  if (state.current === visit && visit.activeAttemptId === handle.attemptId) publishQueued(state, visit, handle);
  return handle;
}
