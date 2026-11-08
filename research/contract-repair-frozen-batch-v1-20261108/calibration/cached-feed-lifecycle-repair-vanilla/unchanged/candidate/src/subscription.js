// Decoding can return a value or a Promise. Detaching an EventTarget listener
// cannot retract a decode that has already started.
export function subscribeFeed(feed, mode, receive, history) {
  const listener = event => {
    const deliver = frame => {
      history.record(frame);
      receive(frame);
    };
    const decoded = feed.decode(event.detail);
    if (decoded && typeof decoded.then === "function") decoded.then(deliver);
    else deliver(decoded);
  };
  feed.start(mode);
  feed.target.addEventListener("batch", listener);
  return () => feed.target.removeEventListener("batch", listener);
}
