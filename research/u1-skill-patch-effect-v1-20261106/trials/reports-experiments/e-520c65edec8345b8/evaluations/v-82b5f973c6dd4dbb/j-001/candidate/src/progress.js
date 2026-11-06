// The source is shared by visits of the same file. Decoding may settle later.
export function watchTransferProgress(feed, receive, record, signal) {
  let nextPacket = 0;
  let latestShown = 0;
  const listener = event => {
    if (signal?.aborted) return;
    const packet = ++nextPacket;
    const deliver = frame => {
      record(frame);
      if (packet > latestShown) {
        latestShown = packet;
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
