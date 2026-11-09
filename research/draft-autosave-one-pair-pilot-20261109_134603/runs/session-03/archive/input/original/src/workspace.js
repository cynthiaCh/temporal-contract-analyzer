import { createDraftEditor } from "./editor.js";

// Autosave integrations can select a different document from inside onSaved.
// One navigation object and store are reused across close/open cycles, including
// returning to the same document. renderDocument/renderStatus are output sinks.
export function createWorkspace({ store, timers, renderDocument, renderStatus, onSaved = () => {} }) {
  const stop = store.subscribe(event => onSaved(event, navigation));
  const editor = createDraftEditor({ store, timers, renderDocument, renderStatus });
  const navigation = {
    open(id) { editor.open(id); },
    edit(text) { editor.edit(text); },
    close() { editor.close(); },
  };
  return { ...navigation, dispose() { stop(); editor.close(); } };
}
