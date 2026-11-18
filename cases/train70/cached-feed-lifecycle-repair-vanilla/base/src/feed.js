class BatchEvent extends Event {
  constructor(frame) { super("batch"); this.detail = frame; }
}

export function createFeed(token, { decode = frame => frame } = {}) {
  const target = new EventTarget();
  let sequence = 0;
  const emit = (kind, seq) => target.dispatchEvent(new BatchEvent({
    feed: token, kind, seq, rows: [token + ":" + kind + ":" + seq],
  }));
  return {
    target,
    decode,
    start(mode = "synchronous") {
      if (mode === "deferred") queueMicrotask(() => emit("snapshot", 0));
      else emit("snapshot", 0);
    },
    emitDelta() { emit("delta", ++sequence); },
  };
}
