// The source is shared by visits of the same file. Decoding may settle later.
export function watchTransferProgress(feed, receive, record) {
  let latest = 0;
  let active = true;
  const listener = event => {
    const sequence = ++latest;
    const deliver = frame => {
      record(frame);
      if (active && sequence === latest) receive(frame);
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
  return () => {
    active = false;
    feed.target.removeEventListener("progress", listener);
  };
}
