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
      current = { id, stop: attachSaveStatus(store, id, renderStatus) };
      renderDocument({ id, text: store.read(id) });
    },
    edit(text) {
      if (current) store.write(current.id, text);
    },
    close,
  };
}
