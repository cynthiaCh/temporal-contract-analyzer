// Incorrect global cleanup: diagnostics now count the cached panel bootstrap.
export function collectProgressTelemetry(feed, recordDelta) {
  const listener = event => {
    const deliver = frame => recordDelta(frame);
    const decoded = feed.decode(event.detail);
    if (decoded && typeof decoded.then === "function") decoded.then(deliver);
    else deliver(decoded);
  };
  feed.target.addEventListener("progress", listener);
  feed.start();
  return () => feed.target.removeEventListener("progress", listener);
}
