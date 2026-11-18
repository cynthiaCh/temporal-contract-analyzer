// Presence frames are full snapshots; see ../README.md for ordering semantics.
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
