import { attachSaveStatus } from "./save-status.js";
import { createTrailingTask } from "./trailing-task.js";

export function createDraftEditor({ store, timers, renderDocument, renderStatus }) {
  let current = null;
  let navigation = 0;
  function retire() {
    const leaving = current;
    current = null;
    if (leaving) leaving.stop();
    renderDocument(null);
    // Retire the view before committing its document-owned pending work.
    // write notifies integrations inline; they may perform newer navigation.
    // Pending work remains scheduled after navigation.
  }
  return {
    open(id) {
      const request = ++navigation;
      retire();
      if (request !== navigation) return;
      const task = createTrailingTask(text => store.write(current ? current.id : id, text), 120, timers);
      current = { id, task, stop: attachSaveStatus(store, id, renderStatus) };
      renderDocument({ id, text: store.read(id) });
    },
    edit(text) {
      if (current) current.task.push(text);
    },
    close() {
      ++navigation;
      retire();
    },
  };
}
