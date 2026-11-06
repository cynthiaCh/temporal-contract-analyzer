import { attachSaveStatus } from "./save-status.js";
import { createTrailingTask } from "./trailing-task.js";

export function createDraftEditor({ store, timers, renderDocument, renderStatus }) {
  let current = null;
  let navigation = 0;
  function retire() {
    const leaving = current;
    current = null;
    if (leaving) {
      leaving.stop();
    }
    renderDocument(null);
    if (leaving) leaving.save.flush();
  }
  function close() {
    ++navigation;
    retire();
  }
  return {
    open(id) {
      const request = ++navigation;
      retire();
      if (request !== navigation) return;
      current = {
        id, text: store.read(id), visit: {},
        save: createTrailingTask(text => store.write(id, text), 120, timers),
        stop: attachSaveStatus(store, id, renderStatus),
      };
      renderDocument({ id, text: current.text });
    },
    edit(text) {
      if (!current) return;
      current.text = text;
      current.save.push(text);
    },
    flush(visit) {
      if (current?.visit === visit) current.save.flush();
    },
    selection() {
      return current && { id: current.id, text: current.text, visit: current.visit };
    },
    close,
  };
}
