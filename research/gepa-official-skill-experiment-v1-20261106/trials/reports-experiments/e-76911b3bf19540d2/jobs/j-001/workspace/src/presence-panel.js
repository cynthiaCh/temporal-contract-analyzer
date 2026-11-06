import { createPresenceChannel } from "./channel.js";

export function createPresencePanel(publish) {
  let release = () => {};
  let visit = 0;
  return {
    show(channel, bootstrapMode = "synchronous") {
      const current = ++visit;
      const previous = release;
      release = () => {};
      previous();
      if (visit !== current) return;
      const listener = (event) => {
        const decoded = channel.decode(event.detail);
        const receive = (value) => {
          if (visit === current) publish(value);
        };
        if (decoded && typeof decoded.then === "function") decoded.then(receive);
        else receive(decoded);
      };
      channel.target.addEventListener("presence", listener);
      const detach = () => channel.target.removeEventListener("presence", listener);
      // A synchronous bootstrap may close or replace the panel during connect.
      release = detach;
      if (visit === current) channel.connect(bootstrapMode);
    },
    close() {
      ++visit;
      const previous = release;
      release = () => {};
      previous();
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
