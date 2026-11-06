export function createWorkspace({ store, renderDocument, onHandoff = () => {} }) {
  let current = null;
  let navigationOrder = 0;
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
      const order = ++navigationOrder;
      retire(true);
      if (order !== navigationOrder) return;
      current = { id };
      renderDocument({ id, text: store.read(id) });
    },
    edit(text) {
      if (current) store.write(current.id, text);
    },
    close() { ++navigationOrder; retire(true); },
    dispose() { ++navigationOrder; retire(false); },
  };
  return navigation;
}
