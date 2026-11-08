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
    if (leaving) leaving.task.flush();
  }
  return {
    open(id) {
      const request = ++navigation;
      retire();
      const task = createTrailingTask(text => store.write(id, text), 120, timers);
      current = { id, text: store.read(id), visit: {}, task, stop: attachSaveStatus(store, id, renderStatus) };
      renderDocument({ id, text: current.text });
    },
    edit(text) {
      if (!current) return;
      current.text = text;
      current.task.push(text);
    },
    selection() { return current && { id: current.id, text: current.text, visit: current.visit }; },
    flush() { if (current) current.task.flush(); },
    close() { ++navigation; retire(); },
  };
}
