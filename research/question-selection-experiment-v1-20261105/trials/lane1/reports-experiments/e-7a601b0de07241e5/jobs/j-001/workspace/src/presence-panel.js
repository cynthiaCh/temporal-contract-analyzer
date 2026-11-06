import { createPresenceChannel } from "./channel.js";
import { subscribeChannel } from "./subscription.js";

export function createPresencePanel(publish) {
  let release = () => {};
  let generation = 0;
  return {
    show(channel, bootstrapMode = "synchronous") {
      release();
      release = () => {};
      const current = ++generation;
      const nextRelease = subscribeChannel(channel, bootstrapMode, (value) => {
        if (current === generation) publish(value);
      });
      if (current === generation) release = nextRelease;
      else nextRelease();
    },
    close() {
      generation++;
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
