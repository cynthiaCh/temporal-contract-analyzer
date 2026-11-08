// Orders decoded publication but admits frames after the attempt has retired.
export function watchTransferProgress(feed, receive, record) {
  let received = 0, published = 0;
  const listener = event => {
    const order = ++received;
    const deliver = frame => { record(frame); if (order > published) { published = order; receive(frame); } };
    const decoded = feed.decode(event.detail);
    if (decoded && typeof decoded.then === "function") decoded.then(deliver); else deliver(decoded);
  };
  feed.target.addEventListener("progress", listener); feed.start();
  return () => feed.target.removeEventListener("progress", listener);
}
