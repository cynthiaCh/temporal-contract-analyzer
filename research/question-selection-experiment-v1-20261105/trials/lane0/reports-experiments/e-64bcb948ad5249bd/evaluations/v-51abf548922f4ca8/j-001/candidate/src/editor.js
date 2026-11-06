import { attachSaveStatus } from "./save-status.js";
import { createTrailingTask } from "./trailing-task.js";

export function createDraftEditor({ store, timers, renderDocument, renderStatus }) {
  let current = null;
  let request = 0;
  function retire() {
    const leaving = current;
    current = null;
    if (leaving) {
      leaving.stop();
      leaving.save.flush();
    }
  }
  function close() {
    const started = ++request;
    retire();
    if (request === started) renderDocument(null);
  }
  return {
    open(id) {
      const started = ++request;
      retire();
      if (request !== started) return;
      renderDocument(null);
      if (request !== started) return;
      current = { id, text: store.read(id), visit: {},
        save: createTrailingTask(text => store.write(id, text), 120, timers),
        stop: attachSaveStatus(store, id, renderStatus) };
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
    flush() {
      if (current) current.save.flush();
    },
    close,
  };
}
