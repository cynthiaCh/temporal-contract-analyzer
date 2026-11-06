import { attachSaveStatus } from "./save-status.js";
import { createTrailingTask } from "./trailing-task.js";

export function createDraftEditor({ store, timers, renderDocument, renderStatus }) {
  let current = null;
  let navigationVersion = 0;
  function leave() {
    const leaving = current;
    current = null;
    if (leaving) leaving.stop();
    renderDocument(null);
    if (leaving) leaving.save.flush();
  }
  function close() {
    navigationVersion++;
    leave();
  }
  return {
    open(id) {
      const version = ++navigationVersion;
      leave();
      if (version !== navigationVersion) return;
      current = { id, text: store.read(id), visit: {}, stop: attachSaveStatus(store, id, renderStatus),
        save: createTrailingTask(text => store.write(id, text), 120, timers) };
      renderDocument({ id, text: current.text });
    },
    edit(text) {
      if (!current) return;
      current.text = text;
      current.save.push(text);
    },
    flush() { if (current) current.save.flush(); },
    selection() {
      return current && { id: current.id, text: current.text, visit: current.visit };
    },
    close,
  };
}
