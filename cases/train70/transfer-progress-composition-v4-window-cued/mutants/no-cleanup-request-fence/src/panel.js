import { enqueueTransfer } from "./queue.js";
import { publishQueued } from "./notice.js";
export function releaseVisit(visit) { const handle = visit.handle; visit.handle = null; if (handle) handle.cancel(); }
export function selectFile(state, file) {
  if (state.disposed) return null;
  const requestId = ++state.nextVisit, previous = state.current; state.current = null;
  if (previous) releaseVisit(previous);
  // Missing request recheck: an outer destination can resume after cleanup navigation.
  const visit = { id: requestId, file, handle: null }; state.current = visit;
  const handle = enqueueTransfer(state, visit, "select");
  if (state.current === visit) { visit.handle = handle; publishQueued(state, visit, handle); } else handle.cancel();
  return handle;
}
export function hidePanel(state) { state.nextVisit++; const old = state.current; state.current = null; if (old) releaseVisit(old); }
export function disposeWorkspace(state) { if (state.disposed) return; state.disposed = true; hidePanel(state); for (const handle of state.tasks.values()) handle.cancel(); }
