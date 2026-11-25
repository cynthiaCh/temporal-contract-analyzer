// A synchronous workspace store, independent of whether an editor is visible.
// Notifications run inline after the record is written. Subscribers may detach
// or subscribe while a notification is being delivered.
export function createDraftStore(initial = {}) {
  const records = new Map(Object.entries(initial));
  const listeners = new Set();
  let revision = 0;
  return {
    read(id) { return records.get(id) ?? ""; },
    write(id, text) {
      records.set(id, text);
      const event = { id, text, revision: ++revision };
      for (const listener of [...listeners]) {
        if (listeners.has(listener)) listener(event);
      }
      return event;
    },
    subscribe(listener) {
      listeners.add(listener);
      return () => listeners.delete(listener);
    },
  };
}
