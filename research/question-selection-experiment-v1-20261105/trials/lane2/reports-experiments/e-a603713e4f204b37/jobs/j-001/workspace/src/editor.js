import { attachSaveStatus } from "./save-status.js";
import { createTrailingTask } from "./trailing-task.js";

export function createDraftEditor({ store, timers, renderDocument, renderStatus }) {
  let current = null;
  let navigationVersion = 0;
  function leave() {
    const leaving = current;
    current = null;
    if (leaving) {
      leaving.stop();
      leaving.save.flush();
    }
  }
  function close() {
    const version = ++navigationVersion;
    leave();
    if (version === navigationVersion) renderDocument(null);
  }
  return {
    open(id) {
      const version = ++navigationVersion;
      leave();
      if (version !== navigationVersion) return;
      renderDocument(null);
      if (version !== navigationVersion) return;
      const text = store.read(id);
      if (version !== navigationVersion) return;
      const visit = { id, text, visit: {}, stop: null, save: createTrailingTask(
        latest => store.write(id, latest), 120, timers) };
      current = visit;
      visit.stop = attachSaveStatus(store, id, renderStatus);
      if (version === navigationVersion && current === visit) renderDocument({ id, text });
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
