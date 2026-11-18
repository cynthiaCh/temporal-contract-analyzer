import { attachSaveStatus } from "./save-status.js";
import { createTrailingTask } from "./trailing-task.js";

export function createDraftEditor({ store, timers, renderDocument, renderStatus }) {
  let current = null;
  let navigation = 0;
  function retire() {
    const leaving = current;
    current = null;
    renderDocument(null);
    // Retire the view before committing its document-owned pending work.
    // write notifies integrations inline; they may perform newer navigation.
    if (leaving) { leaving.task.flush(); leaving.stop(); }
  }
  return {
    open(id, visit) {
      const request = ++navigation;
      retire();
      if (request !== navigation) return;
      const task = createTrailingTask(text => store.write(id, text), 120, timers);
      current = { id, visit, task, stop: attachSaveStatus(store, id, renderStatus) };
      renderDocument({ id, visit, text: store.read(id) });
    },
    selection: () => current && { id: current.id, visit: current.visit },
    edit(text) {
      if (current) current.task.push(text);
    },
    close() {
      ++navigation;
      retire();
    },
  };
}
