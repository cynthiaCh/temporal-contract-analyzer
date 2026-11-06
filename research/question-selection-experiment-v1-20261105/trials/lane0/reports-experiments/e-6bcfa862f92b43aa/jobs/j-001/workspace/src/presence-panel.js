import { createPresenceChannel } from "./channel.js";
import { subscribeChannel } from "./subscription.js";

export function createPresencePanel(publish) {
  let release = () => {};
  let version = 0;
  return {
    show(channel, bootstrapMode = "synchronous") {
      const current = ++version;
      release();
      release = () => {};
      const nextRelease = subscribeChannel(channel, bootstrapMode, (value) => {
        if (version === current) publish(value);
      });
      if (version === current) release = nextRelease;
      else nextRelease();
    },
    close() {
      ++version;
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
