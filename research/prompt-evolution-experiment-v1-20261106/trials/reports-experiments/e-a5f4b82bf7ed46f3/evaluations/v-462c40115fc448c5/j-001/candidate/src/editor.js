import { attachSaveStatus } from "./save-status.js";
import { createTrailingTask } from "./trailing-task.js";

export function createDraftEditor({ store, timers, renderDocument, renderStatus }) {
  let current = null;
  let navigationVersion = 0;
  function close() {
    ++navigationVersion;
    const leaving = current;
    current = null;
    if (leaving) leaving.stop();
    renderDocument(null);
    if (leaving) leaving.save.flush();
  }
  return {
    open(id) {
      const started = navigationVersion + 1;
      close();
      if (started !== navigationVersion) return;
      const text = store.read(id);
      if (started !== navigationVersion) return;
      current = { id, text, visit: {}, stop: attachSaveStatus(store, id, renderStatus),
        save: createTrailingTask(value => store.write(id, value), 120, timers) };
      renderDocument({ id, text: current.text });
    },
    edit(text) {
      if (!current) return;
      current.text = text;
      current.save.push(text);
    },
    flush(selection) {
      if (current?.visit === selection.visit) current.save.flush();
    },
    selection() {
      return current && { id: current.id, text: current.text, visit: current.visit };
    },
    isCurrent(selection) { return current?.visit === selection.visit; },
    close,
  };
}
