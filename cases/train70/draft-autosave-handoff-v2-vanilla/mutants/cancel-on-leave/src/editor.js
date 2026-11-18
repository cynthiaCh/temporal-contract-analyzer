import { attachSaveStatus } from "./save-status.js";
import { createTrailingTask } from "./trailing-task.js";

export function createDraftEditor({ store, timers, renderDocument, renderStatus }) {
  let current = null;
  function retire() {
    const leaving = current;
    current = null;
    if (leaving) { leaving.stop(); leaving.save.cancel(); }
    renderDocument(null);
  }
  return {
    open(id) {
      retire();
      current = { id, save: createTrailingTask(text => store.write(id, text), 120, timers), stop: attachSaveStatus(store, id, renderStatus) };
      renderDocument({ id, text: store.read(id) });
    },
    edit(text) { if (current) current.save.push(text); },
    close: retire,
  };
}
