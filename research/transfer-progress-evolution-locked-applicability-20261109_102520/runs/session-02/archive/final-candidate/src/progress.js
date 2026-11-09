// The source is shared by visits of the same file. Decoding may settle later.
export function watchTransferProgress(feed, receive, record, isActive = () => true) {
  let listening = true;
  const accepts = () => listening && isActive();
  const listener = event => {
    if (!accepts()) return;
    const deliver = frame => {
      record(frame);
      if (accepts()) receive(frame);
    };
    const decoded = feed.decode(event.detail);
    if (decoded && typeof decoded.then === "function") decoded.then(deliver);
    else deliver(decoded);
  };
  feed.target.addEventListener("progress", listener);
  feed.start();
  return () => {
    listening = false;
    feed.target.removeEventListener("progress", listener);
  };
}
