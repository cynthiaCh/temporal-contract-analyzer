// Decoding is synchronous in this case. Publishing may call the host inline.
export function subscribeChannel(channel, bootstrapMode, receive) {
  const listener = (event) => receive(channel.decode(event.detail));
  channel.target.addEventListener("presence", listener);
  channel.connect(bootstrapMode);
  return () => channel.target.removeEventListener("presence", listener);
}
