import { attachSaveStatus } from "./save-status.js";
import { createTrailingTask } from "./trailing-task.js";

export function createDraftEditor({ store, timers, renderDocument, renderStatus }) {
  let current = null;
  let navigationRequest = 0;
  function leave() {
    const leaving = current;
    current = null;
    if (leaving) leaving.stop();
    renderDocument(null);
    if (leaving) leaving.save.flush();
  }
  function close() {
    ++navigationRequest;
    leave();
  }
  return {
    open(id) {
      const request = ++navigationRequest;
      leave();
      if (request !== navigationRequest) return;
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
    selection() {
      return current && { id: current.id, text: current.text, visit: current.visit };
    },
    flushSelection(selection) {
      if (current?.visit === selection.visit) current.save.flush();
    },
    close,
  };
}
