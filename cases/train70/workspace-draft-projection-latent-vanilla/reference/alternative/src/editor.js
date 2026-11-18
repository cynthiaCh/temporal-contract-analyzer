import { attachSaveStatus } from "./save-status.js";
import { createTrailingTask } from "./trailing-task.js";

export function createDraftEditor({ store, timers, renderDocument, renderStatus }) {
  let request = null;
  let active = null;
  function transition(id, visit) {
    const identity = {};
    request = identity;
    const old = active;
    active = null;
    if (old) old.stop();
    renderDocument(null);
    if (old) old.batch.flush();
    if (request !== identity || id === null) return;
    const batch = createTrailingTask(text => store.write(id, text), 120, timers);
    active = { id, visit, batch, stop: attachSaveStatus(store, id, renderStatus) };
    renderDocument({ id, visit, text: store.read(id) });
  }
  return {
    open: (id, visit) => transition(id, visit),
    close: () => transition(null, null),
    edit(text) { if (active) active.batch.push(text); },
    selection: () => active && { id: active.id, visit: active.visit },
  };
}
