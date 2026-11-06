// The decoder may return a value or a Promise (compressed network frames).
// EventTarget removal detaches reception; an already started decode still settles.
export function subscribeChannel(channel, bootstrapMode, receive, onSubscribed = () => {}) {
  const listener = (event) => {
    const decoded = channel.decode(event.detail);
    if (decoded && typeof decoded.then === "function") decoded.then(receive);
    else receive(decoded);
  };
  channel.target.addEventListener("presence", listener);
  const release = () => channel.target.removeEventListener("presence", listener);
  onSubscribed(release);
  channel.connect(bootstrapMode);
  return release;
}
