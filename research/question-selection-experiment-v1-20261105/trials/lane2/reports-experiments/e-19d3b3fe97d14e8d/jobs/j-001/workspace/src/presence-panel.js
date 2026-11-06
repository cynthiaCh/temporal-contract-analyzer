import { createPresenceChannel } from "./channel.js";

export function createPresencePanel(publish) {
  let current = null;
  const close = () => {
    const visit = current;
    current = null;
    if (visit) visit.channel.target.removeEventListener("presence", visit.listener);
  };
  return {
    show(channel, bootstrapMode = "synchronous") {
      close();
      const visit = { channel, listener: null };
      const receive = (value) => {
        if (current === visit) publish(value);
      };
      visit.listener = (event) => {
        const decoded = channel.decode(event.detail);
        if (decoded && typeof decoded.then === "function") decoded.then(receive);
        else receive(decoded);
      };
      current = visit;
      channel.target.addEventListener("presence", visit.listener);
      try {
        channel.connect(bootstrapMode);
      } catch (error) {
        if (current === visit) close();
        throw error;
      }
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
