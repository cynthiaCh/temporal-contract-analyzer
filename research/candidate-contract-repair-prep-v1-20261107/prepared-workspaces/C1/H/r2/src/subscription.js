// The decoder may return a value or a Promise (compressed network frames).
// EventTarget removal detaches reception; an already started decode still settles.
export function subscribeChannel(channel, bootstrapMode, receive) {
  const listener = (event) => {
    const decoded = channel.decode(event.detail);
    if (decoded && typeof decoded.then === "function") decoded.then(receive);
    else receive(decoded);
  };
  channel.connect(bootstrapMode);
  channel.target.addEventListener("presence", listener);
  return () => channel.target.removeEventListener("presence", listener);
}
