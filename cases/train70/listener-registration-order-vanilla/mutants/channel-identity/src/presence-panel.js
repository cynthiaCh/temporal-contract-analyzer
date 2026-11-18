import { createPresenceChannel } from "./channel.js";

export function createPresencePanel(publish) {
  let current = null;
  function retire() {
    const previous = current;
    current = null;
    if (previous) previous.channel.target.removeEventListener("presence", previous.listener);
  }
  return {
    show(channel, bootstrapMode = "synchronous") {
      retire();
      const session = { channel, listener: null };
      session.listener = (event) => {
        const receive = (value) => { if (current && current.channel === channel) publish(value); };
        const decoded = channel.decode(event.detail);
        if (decoded && typeof decoded.then === "function") decoded.then(receive);
        else receive(decoded);
      };
      current = session;
      channel.target.addEventListener("presence", session.listener);
      channel.connect(bootstrapMode);
    },
    close: retire,
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
