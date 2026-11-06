import { createPresenceChannel } from "./channel.js";

export function createPresencePanel(publish) {
  let active = null;
  const detach = () => {
    const previous = active;
    active = null;
    if (previous) previous.channel.target.removeEventListener("presence", previous.listener);
  };
  return {
    show(channel, bootstrapMode = "synchronous") {
      detach();
      const visit = { channel, listener: null };
      visit.listener = (event) => {
        const decoded = channel.decode(event.detail);
        const deliver = (value) => {
          if (active === visit) publish(value);
        };
        if (decoded && typeof decoded.then === "function") decoded.then(deliver);
        else deliver(decoded);
      };
      active = visit;
      channel.target.addEventListener("presence", visit.listener);
      channel.connect(bootstrapMode);
    },
    close() {
      detach();
    },
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
