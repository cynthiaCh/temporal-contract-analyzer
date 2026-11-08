// The source is shared by visits of the same file. Decoding may settle later.
export function watchTransferProgress(feed, receive, record) {
  let accepting = true;
  let sequence = 0;
  const listener = event => {
    // Assign freshness when the frame arrives, rather than when an async
    // decoder happens to finish. Frames already accepted remain historical
    // even if this listener is subsequently released.
    if (!accepting) return;
    const frameSequence = ++sequence;
    const deliver = frame => { record(frame); receive(frame, frameSequence); };
    const decoded = feed.decode(event.detail);
    if (decoded && typeof decoded.then === "function") decoded.then(deliver);
    else deliver(decoded);
  };
  feed.target.addEventListener("progress", listener);
  // Some feeds synchronously replay their warm packet from start().
  feed.start();
  return () => {
    if (!accepting) return;
    accepting = false;
    feed.target.removeEventListener("progress", listener);
  };
}
