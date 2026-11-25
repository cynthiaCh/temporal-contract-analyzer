import { createPresenceChannel } from "./channel.js";
import { subscribeChannel } from "./subscription.js";

export function createPresencePanel(publish) {
  let current = null;
  function retire() {
    const leaving = current;
    current = null;
    if (leaving) leaving.release();
  }
  return {
    show(channel, bootstrapMode = "synchronous") {
      retire();
      const visit = { release: () => {} };
      current = visit;
      const release = subscribeChannel(channel, bootstrapMode, value => {
        if (current === visit) publish(value);
      });
      if (current === visit) visit.release = release;
      else release();
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
