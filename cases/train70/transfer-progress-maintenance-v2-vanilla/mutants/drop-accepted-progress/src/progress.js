// The source is shared by visits of the same file. Decoding may settle later.
export function watchTransferProgress(feed, receive, record, isCurrent) {
  const listener = event => {
    if (!isCurrent()) return;
    const deliver = frame => { if (!isCurrent()) return; record(frame); receive(frame); };
    const decoded = feed.decode(event.detail);
    if (decoded && typeof decoded.then === "function") decoded.then(deliver);
    else deliver(decoded);
  };
  feed.target.addEventListener("progress", listener);
  feed.start();
  return () => feed.target.removeEventListener("progress", listener);
}
