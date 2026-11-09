// The source is shared by visits of the same file. Decoding may settle later.
export function watchTransferProgress(feed, receive, record, accepts = () => true) {
  const listener = event => {
    // A listener can outlive its visit briefly when a visible update navigates
    // synchronously from inside feed.start().  Decide eligibility before decode;
    // once accepted, its eventual audit is retained.
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
