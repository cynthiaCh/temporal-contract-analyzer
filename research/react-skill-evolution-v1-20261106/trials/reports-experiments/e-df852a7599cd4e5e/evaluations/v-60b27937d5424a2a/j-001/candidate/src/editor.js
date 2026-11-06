import { attachSaveStatus } from "./save-status.js";
import { createTrailingTask } from "./trailing-task.js";

export function createDraftEditor({ store, timers, renderDocument, renderStatus }) {
  let current = null;
  let request = 0;
  function leave() {
    const leaving = current;
    current = null;
    if (leaving) {
      leaving.stop();
      leaving.save.flush();
    }
  }
  function close() {
    const started = ++request;
    leave();
    if (request === started) renderDocument(null);
  }
  return {
    open(id) {
      const started = ++request;
      leave();
      if (request !== started) return;
      renderDocument(null);
      const text = store.read(id);
      const visit = { id, text, visit: {}, save: createTrailingTask(value => store.write(id, value), 120, timers) };
      current = visit;
      visit.stop = attachSaveStatus(store, id, renderStatus);
      renderDocument({ id, text });
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
    isVisit(visit) { return current?.visit === visit; },
    close,
  };
}
