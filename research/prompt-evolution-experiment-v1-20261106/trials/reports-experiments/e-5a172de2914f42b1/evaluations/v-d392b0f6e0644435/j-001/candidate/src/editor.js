import { attachSaveStatus } from "./save-status.js";
import { createTrailingTask } from "./trailing-task.js";

export function createDraftEditor({ store, timers, renderDocument, renderStatus }) {
  let current = null;
  let navigationVersion = 0;
  function retire() {
    const leaving = current;
    current = null;
    if (leaving) {
      leaving.stop();
      leaving.save.flush();
    }
  }
  function close() {
    const request = ++navigationVersion;
    retire();
    if (request === navigationVersion) renderDocument(null);
  }
  return {
    open(id) {
      const request = ++navigationVersion;
      retire();
      if (request !== navigationVersion) return;
      renderDocument(null);
      const text = store.read(id);
      current = { id, text, visit: {}, stop: attachSaveStatus(store, id, renderStatus),
        save: createTrailingTask(value => store.write(id, value), 120, timers) };
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
