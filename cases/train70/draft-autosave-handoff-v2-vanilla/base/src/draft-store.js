export function createDraftStore(initial = {}) {
  const records = new Map(Object.entries(initial));
  const listeners = new Set();
  return {
    read(id) { return records.get(id) ?? ""; },
    write(id, text) {
      records.set(id, text);
      const event = { id, text };
      for (const listener of [...listeners]) listener(event);
      return event;
    },
    subscribe(listener) {
      listeners.add(listener);
      return () => listeners.delete(listener);
    },
  };
}
