import { createPresenceChannel } from "./channel.js";
import { subscribeChannel } from "./subscription.js";

export function createPresencePanel(publish) {
  let release = () => {};
  let generation = 0;
  return {
    show(channel, bootstrapMode = "synchronous") {
      const current = ++generation;
      release();
      release = () => {};
      const subscribed = subscribeChannel(channel, bootstrapMode, (value) => {
        if (generation === current) publish(value);
      });
      if (generation === current) release = subscribed;
      else subscribed();
    },
    close() {
      ++generation;
      release();
      release = () => {};
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
