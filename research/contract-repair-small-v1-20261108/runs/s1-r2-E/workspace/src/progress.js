// The source is shared by visits of the same file. Decoding may settle later.
export function watchTransferProgress(feed, receive, record) {
  let lastShown = 0;
  let sequence = 0;
  const listener = event => {
    const frameSequence = ++sequence;
    const deliver = frame => {
      record(frame);
      // Decode promises can settle out of order. History keeps every frame,
      // while the panel only accepts a frame newer than its current display.
      if (frameSequence > lastShown) {
        lastShown = frameSequence;
        receive(frame);
      }
    };
    const decoded = feed.decode(event.detail);
    if (decoded && typeof decoded.then === "function") decoded.then(deliver);
    else deliver(decoded);
  };
  feed.target.addEventListener("progress", listener);
  feed.start();
  return () => feed.target.removeEventListener("progress", listener);
}
