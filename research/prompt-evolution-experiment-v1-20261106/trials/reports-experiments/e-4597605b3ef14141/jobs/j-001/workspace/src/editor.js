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
      leaving.save.flush();
    }
  }
  function close() {
    const request = ++navigation;
    retire();
    if (request === navigation) renderDocument(null);
  }
  return {
    open(id) {
      const request = ++navigation;
      retire();
      if (request !== navigation) return;
      renderDocument(null);
      const save = createTrailingTask(text => store.write(id, text), 120, timers);
      current = { id, text: store.read(id), visit: {}, save, stop: attachSaveStatus(store, id, renderStatus) };
      renderDocument({ id, text: current.text });
    },
    edit(text) {
      if (!current) return;
      current.text = text;
      current.save.push(text);
    },
    selection() {
      return current && { id: current.id, text: current.text, visit: current.visit };
    },
    flushSelection(selection) {
      if (current?.visit === selection.visit) current.save.flush();
    },
    isCurrent(selection) {
      return current?.visit === selection.visit;
    },
    close,
  };
}
