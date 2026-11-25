// The decoder may return a value or a Promise (compressed network frames).
// EventTarget removal detaches reception; an already started decode still settles.
export function subscribeChannel(channel, bootstrapMode, receive, isCurrent = () => true) {
  let active = true;
  const deliver = value => { if (active && isCurrent()) receive(value); };
  const listener = (event) => {
    if (!isCurrent()) return;
    const decoded = channel.decode(event.detail);
    if (decoded && typeof decoded.then === "function") decoded.then(deliver);
    else deliver(decoded);
  };
  channel.target.addEventListener("presence", listener);
  channel.connect(bootstrapMode);
  return () => {
    active = false;
    channel.target.removeEventListener("presence", listener);
  };
}
