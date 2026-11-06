Work only on the candidate-visible files in this workspace. Do not inspect sibling experiment jobs, original repositories or report stores.

# Maintenance task

Immediately after opening the presence panel, the initial online-user state is
sometimes missing even though later presence updates appear. Fix the presence
panel while preserving its existing behavior, including workspace navigation.

Do not change the metrics consumer.

<candidate-assistance>
# Retrieved candidate context

Raw source, configuration and documentation excerpts selected using the original task only. Retrieval is incomplete; inspect other candidate files when needed.

## src/channel.js:1-32
```
class PresenceEvent extends Event {
  constructor(detail) {
    super("presence");
    this.detail = detail;
  }
}

export function createPresenceChannel(token, { decode = (value) => value } = {}) {
  const target = new EventTarget();
  const emit = (kind) => target.dispatchEvent(new PresenceEvent(`${token}:${kind}`));
  return {
    target,
    decode,
    connect(bootstrapMode) {
      if (bootstrapMode === "deferred") queueMicrotask(() => emit("bootstrap"));
      else emit("bootstrap");
    },
    emitUpdate() {
      emit("update");
    },
  };
}

export async function observeChannel({ token, bootstrapMode }) {
  const events = [];
  const channel = createPresenceChannel(token);
  channel.connect(bootstrapMode);
  channel.target.addEventListener("presence", (event) => events.push(event.detail));
  await Promise.resolve();
  channel.emitUpdate();
  return { events };
}
```

## src/metrics-consumer.js:1-6
```
import { observeChannel } from "./channel.js";

export function collectMetrics(token) {
  // Metrics deliberately attach after the synchronous bootstrap and count deltas only.
  return observeChannel({ token, bootstrapMode: "synchronous" });
}
```

## src/presence-panel.js:1-27
```
import { createPresenceChannel } from "./channel.js";
import { subscribeChannel } from "./subscription.js";

export function createPresencePanel(publish) {
  let release = () => {};
  return {
    show(channel, bootstrapMode = "synchronous") {
      release();
      release = subscribeChannel(channel, bootstrapMode, publish);
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
```

## src/render-workspace.js:1-10
```
import { collectMetrics } from "./metrics-consumer.js";
import { renderPresence } from "./presence-panel.js";

export async function render({ token, bootstrapMode }) {
  const [presence, metrics] = await Promise.all([
    renderPresence(token, bootstrapMode),
    collectMetrics(token),
  ]);
  return { presence, metrics };
}
```

## src/subscription.js:1-12
```
// The decoder may return a value or a Promise (compressed network frames).
// EventTarget removal detaches reception; an already started decode still settles.
export function subscribeChannel(channel, bootstrapMode, receive) {
  const listener = (event) => {
    const decoded = channel.decode(event.detail);
    if (decoded && typeof decoded.then === "function") decoded.then(receive);
    else receive(decoded);
  };
  channel.connect(bootstrapMode);
  channel.target.addEventListener("presence", listener);
  return () => channel.target.removeEventListener("presence", listener);
}
```

## src/workspace-navigation.js:1-13
```
import { createPresencePanel } from "./presence-panel.js";

// Presence publication can synchronously select a different room or hide the
// panel (for example, a room chooser reacting to an empty bootstrap snapshot).
// Reusing a transport object on a later visit is supported by the workspace.
export function createWorkspaceNavigation(renderState) {
  const panel = createPresencePanel((value) => renderState(value, navigation));
  const navigation = {
    select(channel, mode = "synchronous") { panel.show(channel, mode); },
    hide() { panel.close(); },
  };
  return navigation;
}
```


</candidate-assistance>
