import { attachSaveStatus } from "./save-status.js";
import { createTrailingTask } from "./trailing-task.js";

export function createDraftEditor({ store, timers, renderDocument, renderStatus }) {
  let current = null;
  let navigationRequest = 0;
  function close() {
    const request = ++navigationRequest;
    const leaving = current;
    current = null;
    if (leaving) {
      leaving.stop();
      leaving.save.flush();
    }
    if (request === navigationRequest) renderDocument(null);
  }
  return {
    open(id) {
      const request = ++navigationRequest;
      const leaving = current;
      current = null;
      if (leaving) {
        leaving.stop();
        leaving.save.flush();
      }
      if (request !== navigationRequest) return;
      renderDocument(null);
      const text = store.read(id);
      const save = createTrailingTask(value => store.write(id, value), 120, timers);
      current = { id, text, visit: {}, save, stop: attachSaveStatus(store, id, renderStatus) };
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
    close,
  };
}
