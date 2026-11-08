import { attachSaveStatus } from "./save-status.js";
import { createTrailingTask } from "./trailing-task.js";

export function createDraftEditor({ store, timers, renderDocument, renderStatus }) {
  let current = null;
  function close(isCurrent = () => true) {
    const leaving = current;
    if (leaving) {
      // Retire the badge before a flushing write can notify integrations.
      leaving.stop();
      leaving.save.flush();
    }
    // A synchronous save notification may have opened another document.
    if (current === leaving) current = null;
    if (isCurrent() && current === null) renderDocument(null);
  }
  return {
    open(id, isCurrent = () => true) {
      close(isCurrent);
      if (!isCurrent()) return;
      const visit = {};
      const session = {
        id,
        text: store.read(id),
        visit,
        stop: null,
        save: null,
      };
      session.save = createTrailingTask(text => {
        if (current === session) store.write(session.id, text);
      }, 120, timers);
      session.stop = attachSaveStatus(store, id, renderStatus);
      current = session;
      renderDocument({ id, text: session.text });
    },
    edit(text) {
      if (!current) return;
      current.text = text;
      current.save.push(text);
    },
    selection() {
      return current && { id: current.id, text: current.text, visit: current.visit };
    },
    flush(selection) {
      if (current && current.visit === selection.visit) current.save.flush();
    },
    isSelected(selection) {
      return !!current && current.visit === selection.visit;
    },
    close,
  };
}
