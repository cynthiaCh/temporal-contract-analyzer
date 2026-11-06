// The decoder may return a value or a Promise (compressed network frames).
// EventTarget removal detaches reception; an already started decode still settles.
export function subscribeChannel(channel, bootstrapMode, receive) {
  const listener = (event) => {
    const decoded = channel.decode(event.detail);
    if (decoded && typeof decoded.then === "function") decoded.then(receive);
    else receive(decoded);
  };
  channel.target.addEventListener("presence", listener);
  try {
    channel.connect(bootstrapMode);
  } catch (error) {
    channel.target.removeEventListener("presence", listener);
    throw error;
  }
  return () => channel.target.removeEventListener("presence", listener);
}
