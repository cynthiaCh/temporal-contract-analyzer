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
    open(id, visit) {
      close();
      current = { id, visit, stop: attachSaveStatus(store, id, renderStatus) };
      renderDocument({ id, visit, text: store.read(id) });
    },
    edit(text) {
      if (current) store.write(current.id, text);
    },
    selection: () => current && { id: current.id, visit: current.visit },
    close,
  };
}
