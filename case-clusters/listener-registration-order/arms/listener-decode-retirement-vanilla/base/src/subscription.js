// The decoder may return a value or a Promise (compressed network frames).
// EventTarget removal detaches reception; an already started decode still settles.
export function subscribeChannel(channel, bootstrapMode, receive, isCurrent = () => true) {
  const listener = (event) => {
    if (!isCurrent()) return;
    const decoded = channel.decode(event.detail);
    if (decoded && typeof decoded.then === "function") decoded.then(receive);
    else if (isCurrent()) receive(decoded);
  };
  channel.target.addEventListener("presence", listener);
  channel.connect(bootstrapMode);
  return () => channel.target.removeEventListener("presence", listener);
}
