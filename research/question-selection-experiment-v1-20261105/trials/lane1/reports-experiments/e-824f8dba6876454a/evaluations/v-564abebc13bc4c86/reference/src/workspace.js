export function createWorkspace({ store, renderDocument, onHandoff = () => {} }) {
  let current = null;
  let navigationRevision = 0;
  function retire(withHandoff) {
    const leaving = current;
    current = null;
    renderDocument(null);
    if (leaving && withHandoff) onHandoff({ id: leaving.id, text: store.read(leaving.id) }, navigation);
  }
  const navigation = {
    open(id) {
      const request = ++navigationRevision;
      retire(true);
      if (request !== navigationRevision) return;
      current = { id };
      renderDocument({ id, text: store.read(id) });
    },
    edit(text) { if (current) store.write(current.id, text); },
    close() { ++navigationRevision; retire(true); },
    dispose() { ++navigationRevision; retire(false); },
  };
  return navigation;
}
