// A queued notice describes the accepted attempt in its originating visit.
export function publishQueued(state, visit, handle) {
  if (state.current !== visit) return;
  state.showQueued({ fileId: visit.file.id, attemptId: handle.attemptId,
    visitId: visit.id, status: "queued" });
}
