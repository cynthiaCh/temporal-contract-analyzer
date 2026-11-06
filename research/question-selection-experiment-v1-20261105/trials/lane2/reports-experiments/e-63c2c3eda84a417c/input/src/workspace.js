export function createWorkspace({ store, renderDocument, onHandoff = () => {} }) {
  let current = null;
  function retire(withHandoff) {
    const leaving = current;
    current = null;
    renderDocument(null);
    if (leaving && withHandoff) {
      onHandoff({ id: leaving.id, text: store.read(leaving.id) }, navigation);
    }
  }
  const navigation = {
    open(id) {
      // Switching currently bypasses the business handoff used by close.
      retire(false);
      current = { id };
      renderDocument({ id, text: store.read(id) });
    },
    edit(text) {
      if (current) store.write(current.id, text);
    },
    close() { retire(true); },
    dispose() { retire(false); },
  };
  return navigation;
}
