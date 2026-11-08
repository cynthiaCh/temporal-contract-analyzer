// Decoding can return a value or a Promise. Detaching an EventTarget listener
// cannot retract a decode that has already started.
export function subscribeFeed(feed, mode, receive, history, ownRelease = () => {}) {
  const listener = event => {
    const deliver = frame => {
      history.record(frame);
      receive(frame);
    };
    const decoded = feed.decode(event.detail);
    if (decoded && typeof decoded.then === "function") decoded.then(deliver);
    else deliver(decoded);
  };
  feed.target.addEventListener("batch", listener);
  const release = () => feed.target.removeEventListener("batch", listener);
  ownRelease(release);
  feed.start(mode);
  return release;
}
