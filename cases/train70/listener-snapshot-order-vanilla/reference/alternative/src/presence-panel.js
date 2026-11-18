import { createPresenceChannel } from "./channel.js";

export function createPresencePanel(publish) {
  let generation = 0;
  let dispose = () => {};
  function close() { ++generation; const prior = dispose; dispose = () => {}; prior(); }
  return {
    show(channel, bootstrapMode = "synchronous") {
      close();
      const visit = generation;
      let received = 0, committed = 0;
      const listener = (event) => {
        const order = ++received;
        const deliver = value => { if (generation === visit && order > committed) { committed = order; publish(value); } };
        const decoded = channel.decode(event.detail);
        if (decoded && typeof decoded.then === "function") decoded.then(deliver);
        else deliver(decoded);
      };
      dispose = () => channel.target.removeEventListener("presence", listener);
      channel.target.addEventListener("presence", listener);
      channel.connect(bootstrapMode);
    },
    close,
  };
}
export async function renderPresence(token, bootstrapMode) {
  const events = [];
  const panel = createPresencePanel((value) => events.push(value));
  const channel = createPresenceChannel(token);
  panel.show(channel, bootstrapMode);
  await Promise.resolve();
  channel.emitUpdate();
  panel.close();
  return { events };
}
