import { attachSaveStatus } from "./save-status.js";
import { createTrailingTask } from "./trailing-task.js";

export function createDraftEditor({ store, timers, renderDocument, renderStatus }) {
  let current = null;
  let navigationVersion = 0;
  function retire() {
    const leaving = current;
    current = null;
    if (leaving) leaving.stop();
    renderDocument(null);
    if (leaving) leaving.save.flush();
  }
  function close() {
    navigationVersion++;
    retire();
  }
  return {
    open(id) {
      const version = ++navigationVersion;
      retire();
      if (version !== navigationVersion) return;
      const text = store.read(id);
      if (version !== navigationVersion) return;
      current = { id, text, visit: {}, stop: attachSaveStatus(store, id, renderStatus),
        save: createTrailingTask(value => store.write(id, value), 120, timers) };
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
    flush(visit) {
      if (current?.visit === visit) current.save.flush();
    },
    close,
  };
}
