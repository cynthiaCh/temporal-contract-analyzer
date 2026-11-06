import { createPresenceChannel } from "./channel.js";
import { subscribeChannel } from "./subscription.js";

export function createPresencePanel(publish) {
  let release = () => {};
  let visit = 0;
  return {
    show(channel, bootstrapMode = "synchronous") {
      const current = ++visit;
      release();
      release = () => {};
      subscribeChannel(channel, bootstrapMode, (value) => {
        if (visit === current) publish(value);
      }, (unsubscribe) => {
        release = unsubscribe;
      });
    },
    close() {
      ++visit;
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
