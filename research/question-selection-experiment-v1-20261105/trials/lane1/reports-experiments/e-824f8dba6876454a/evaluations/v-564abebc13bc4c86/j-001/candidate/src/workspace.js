export function createWorkspace({ store, renderDocument, onHandoff = () => {} }) {
  let current = null;
  let navigationVersion = 0;
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
      const version = ++navigationVersion;
      retire(true);
      if (version !== navigationVersion) return;
      current = { id };
      renderDocument({ id, text: store.read(id) });
    },
    edit(text) {
      if (current) store.write(current.id, text);
    },
    close() { ++navigationVersion; retire(true); },
    dispose() { ++navigationVersion; retire(false); },
  };
  return navigation;
}
