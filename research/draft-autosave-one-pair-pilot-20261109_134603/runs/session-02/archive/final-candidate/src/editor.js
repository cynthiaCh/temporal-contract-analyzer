import { attachSaveStatus } from "./save-status.js";
import { createTrailingTask } from "./trailing-task.js";

export function createDraftEditor({ store, timers, renderDocument, renderStatus }) {
  let current = null;
  let navigationRevision = 0;

  // Keep the document id with the queued text: a later open must never cause
  // an edit from the previous document to be written to the new one.
  const save = createTrailingTask((id, text) => store.write(id, text), 120, timers);

  function leaveCurrent() {
    const leaving = current;
    current = null;

    // Detach before flushing. A flush notifies store subscribers inline, so a
    // departing document must not receive the notification as an active badge.
    if (leaving) leaving.stop();
    renderDocument(null);
    if (leaving) save.flush();
  }

  function close() {
    navigationRevision += 1;
    leaveCurrent();
  }

  return {
    open(id) {
      const request = ++navigationRevision;
      leaveCurrent();

      // Saving while leaving can synchronously start a newer navigation. Its
      // result wins over the navigation that caused the save.
      if (request !== navigationRevision) return;

      current = { id, stop: attachSaveStatus(store, id, renderStatus) };
      renderDocument({ id, text: store.read(id) });
    },
    edit(text) {
      if (current) save.push(current.id, text);
    },
    close,
  };
}
