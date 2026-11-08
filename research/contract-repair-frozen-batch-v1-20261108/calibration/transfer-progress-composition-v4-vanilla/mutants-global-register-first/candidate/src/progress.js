export function watchTransferProgress(feed, receive, record, admit) {
  const listener = event => {
    const order = admit();
    if (order === null) return;
    const deliver = frame => { record(frame); receive(frame, order); };
    const decoded = feed.decode(event.detail);
    if (decoded && typeof decoded.then === "function") decoded.then(deliver);
    else deliver(decoded);
  };
  feed.target.addEventListener("progress", listener);
  feed.start();
  return () => feed.target.removeEventListener("progress", listener);
}
