// Acceptance precedes the transport callback, which may navigate synchronously.
// Every accepted write completes independently. A late older acknowledgement
// cannot roll persisted data back. read() exposes accepted drafts immediately.
export function createDraftStore(initial = {}, { transport = event => Promise.resolve() } = {}) {
  const accepted = new Map(Object.entries(initial)), persisted = new Map(Object.entries(initial));
  const revisions = new Map(), committed = new Map(), listeners = new Set();
  return {
    read(id) { return accepted.get(id) ?? ""; },
    readPersisted(id) { return persisted.get(id) ?? ""; },
    write(id, text, owner) {
      const revision = (revisions.get(id) || 0) + 1;
      revisions.set(id, revision); accepted.set(id, text);
      const event = Object.freeze({ id, text, revision, owner });
      const pending = transport(event);
      return Promise.resolve(pending).then(() => {
        if (revision > (committed.get(id) || 0)) {
          committed.set(id, revision); persisted.set(id, text);
        }
        for (const listener of [...listeners]) listener(event);
        return event;
      });
    },
    subscribe(listener) { listeners.add(listener); return () => listeners.delete(listener); },
  };
}
