// Incorrectly applies current validity at completion to both audit and UI.
export function watchTransferProgress(feed, receive, record, admit, stillCurrent) {
  const listener = event => {
    const order = admit();
    if (order === null) return;
    const deliver = frame => {
      if (!stillCurrent()) return;
      record(frame); receive(frame, order);
    };
    const decoded = feed.decode(event.detail);
    if (decoded && typeof decoded.then === "function") decoded.then(deliver); else deliver(decoded);
  };
  feed.target.addEventListener("progress", listener); feed.start();
  return () => feed.target.removeEventListener("progress", listener);
}
