import { attachSaveStatus } from "./save-status.js";

export function createDraftEditor({ store, timers, renderDocument, renderStatus }) {
  let current = null;
  function close() {
    const leaving = current;
    current = null;
    if (leaving) leaving.stop();
    renderDocument(null);
  }
  return {
    open(id) {
      close();
      current = { id, text: store.read(id), visit: {}, stop: attachSaveStatus(store, id, renderStatus) };
      renderDocument({ id, text: current.text });
    },
    edit(text) {
      if (!current) return;
      current.text = text;
      store.write(current.id, text);
    },
    selection() {
      return current && { id: current.id, text: current.text, visit: current.visit };
    },
    close,
  };
}
