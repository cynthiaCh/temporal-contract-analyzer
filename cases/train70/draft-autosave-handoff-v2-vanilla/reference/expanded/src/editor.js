import { attachSaveStatus } from "./save-status.js";
import { createTrailingTask } from "./trailing-task.js";

export function createDraftEditor({ store, timers, renderDocument, renderStatus }) {
  let current = null;
  function retire() {
    const leaving = current;
    current = null;
    if (leaving) leaving.stop();
    renderDocument(null);
    if (leaving) leaving.save.flush();
  }
  return {
    open(id) {
      retire();
      const save = createTrailingTask(text => store.write(id, text), 120, timers);
      current = { id, save, stop: attachSaveStatus(store, id, renderStatus) };
      renderDocument({ id, text: store.read(id) });
    },
    edit(text) { if (current) current.save.push(text); },
    close: retire,
  };
}
