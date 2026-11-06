// The source is shared by visits of the same file. Decoding may settle later.
export function watchTransferProgress(feed, receive, record) {
  let nextPacket = 0;
  let displayedPacket = 0;
  const listener = event => {
    const packet = ++nextPacket;
    const deliver = frame => {
      record(frame);
      if (packet > displayedPacket) {
        displayedPacket = packet;
        receive(frame);
      }
    };
    const decoded = feed.decode(event.detail);
    if (decoded && typeof decoded.then === "function") decoded.then(deliver);
    else deliver(decoded);
  };
  feed.target.addEventListener("progress", listener);
  try {
    feed.start();
  } catch (error) {
    feed.target.removeEventListener("progress", listener);
    throw error;
  }
  return () => feed.target.removeEventListener("progress", listener);
}
