// Parent-case repair: correct warm registration and admission, but no frame freshness.
export function watchTransferProgress(feed, receive, record, accepts) {
  const listener = event => {
    if (!accepts()) return;
    const deliver = frame => { record(frame); receive(frame); };
    const decoded = feed.decode(event.detail);
    if (decoded && typeof decoded.then === "function") decoded.then(deliver);
    else deliver(decoded);
  };
  feed.target.addEventListener("progress", listener);
  feed.start();
  return () => feed.target.removeEventListener("progress", listener);
}
