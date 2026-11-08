import { attachSaveStatus } from "./save-status.js";
import { createTrailingTask } from "./trailing-task.js";

export function createDraftEditor({ store, timers, renderDocument, renderStatus }) {
  let current = null;
  function save(visit, text) {
    visit.pending = false;
    visit.savedText = text;
    store.write(visit.id, text);
  }
  // `isCurrent` is supplied by workspace navigation. A save can synchronously
  // start a newer navigation through onSaved, so an older request must not
  // render over that newer request when it resumes.
  function close(isCurrent = () => true) {
    const leaving = current;
    current = null;
    if (leaving) {
      // Retire the badge before flushing: store notifications from the flush
      // must not be attributed to the document that is being left.
      leaving.stop();
      if (leaving.pending) leaving.task.flush();
    }
    if (isCurrent()) renderDocument(null);
  }
  return {
    open(id, isCurrent = () => true) {
      close(isCurrent);
      if (!isCurrent()) return;
      const text = store.read(id);
      const visit = {
        id,
        text,
        savedText: text,
        pending: false,
        visit: {},
        stop: null,
        task: null,
      };
      visit.task = createTrailingTask(nextText => save(visit, nextText), 120, timers);
      visit.stop = attachSaveStatus(store, id, renderStatus);
      current = visit;
      renderDocument({ id, text: current.text });
    },
    edit(text) {
      if (!current) return;
      current.text = text;
      current.pending = true;
      current.task.push(text);
    },
    selection() {
      return current && { id: current.id, text: current.text, visit: current.visit };
    },
    persist(selection) {
      if (!selection) return;
      const visit = current && current.visit === selection.visit ? current : null;
      if (visit && visit.pending) {
        // The flush saves the call-entry text. Its notification may itself
        // edit this visit; that later edit starts a fresh burst and must not
        // be overwritten by this submit.
        visit.task.flush();
        return;
      }
      // A selection can be from a visit that navigation retired while an
      // inline notification was running. Its accepted text was flushed before
      // retirement; the guard also avoids a duplicate write on normal submit.
      if (visit && visit.savedText !== selection.text) save(visit, selection.text);
    },
    isActive(selection) {
      return Boolean(current && selection && current.visit === selection.visit);
    },
    close,
  };
}
