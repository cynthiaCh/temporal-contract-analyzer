import { attachSaveStatus } from "./save-status.js";
import { createTrailingTask } from "./trailing-task.js";

export function createDraftEditor({ store, timers, renderDocument, renderStatus }) {
  let current = null;
  let navigationVersion = 0;
  function close() {
    const version = ++navigationVersion;
    const leaving = current;
    current = null;
    if (leaving) {
      leaving.stop();
      leaving.save.flush();
    }
    if (version === navigationVersion) renderDocument(null);
  }
  return {
    open(id) {
      const before = navigationVersion;
      close();
      if (navigationVersion !== before + 1) return;
      const version = navigationVersion;
      current = { id, text: store.read(id), visit: {},
        stop: attachSaveStatus(store, id, renderStatus),
        save: createTrailingTask(text => store.write(id, text), 120, timers) };
      if (version !== navigationVersion) return;
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
    flush() { if (current) current.save.flush(); },
    close,
  };
}
