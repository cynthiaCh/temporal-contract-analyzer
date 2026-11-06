// The source is shared by visits of the same file. Decoding may settle later.
export function watchTransferProgress(feed, receive, record) {
  let nextSequence = 0;
  let displayedSequence = 0;
  const listener = event => {
    const sequence = ++nextSequence;
    const deliver = frame => {
      record(frame);
      if (sequence > displayedSequence) {
        displayedSequence = sequence;
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
