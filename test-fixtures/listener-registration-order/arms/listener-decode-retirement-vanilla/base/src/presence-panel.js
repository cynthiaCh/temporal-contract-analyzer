import { createPresenceChannel } from "./channel.js";
import { subscribeChannel } from "./subscription.js";

export function createPresencePanel(publish) {
  let release = () => {};
  return {
    show(channel, bootstrapMode = "synchronous") {
      release();
      let subscriptionRelease = () => {};
      let released = false;
      release = () => {
        released = true;
        subscriptionRelease();
      };
      subscriptionRelease = subscribeChannel(channel, bootstrapMode, publish, () => !released);
      if (released) subscriptionRelease();
    },
    close() {
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
