// The source is shared by visits of the same file. Decoding may settle later.
export function watchTransferProgress(feed, receive, record) {
  let accepting = true;
  let nextArrival = 0;
  let lastProjectedArrival = 0;
  const listener = event => {
    if (!accepting) return;
    // Preserve source order before asynchronous decoding can reorder settlement.
    const arrival = ++nextArrival;
    const deliver = frame => {
      // Frames admitted while this listener was live retain their audit entry,
      // even when the listener is released before decoding finishes.
      record(frame);

      // Recording is host code and can synchronously change visits or attempts.
      // Only the live listener may project a frame, and never behind one it has
      // already projected.
      if (accepting && arrival > lastProjectedArrival) {
        lastProjectedArrival = arrival;
        receive(frame);
      }
    };
    const decoded = feed.decode(event.detail);
    if (decoded && typeof decoded.then === "function") decoded.then(deliver);
    else deliver(decoded);
  };
  feed.target.addEventListener("progress", listener);
  // start() may synchronously publish a cached frame, so install first.
  feed.start();
  return () => {
    if (!accepting) return;
    accepting = false;
    feed.target.removeEventListener("progress", listener);
  };
}
