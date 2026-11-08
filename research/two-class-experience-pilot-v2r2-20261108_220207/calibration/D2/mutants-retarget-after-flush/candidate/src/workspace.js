import { createDraftEditor } from "./editor.js";

export function createWorkspace({ store, archive, timers, renderDocument, renderStatus,
  renderSubmission = () => {}, onSaved = () => {} }) {
  const stop = store.subscribe(event => onSaved(event, navigation));
  const editor = createDraftEditor({ store, timers, renderDocument, renderStatus });
  const navigation = {
    open(id) { renderSubmission(null); editor.open(id); },
    edit(text) { editor.edit(text); },
    close() { renderSubmission(null); editor.close(); },
    submit() {
      const origin = editor.selection();
      if (!origin) return null;
      editor.flush();
      const target = editor.selection() || origin;
      const receipt = archive.capture({ id: target.id, text: target.text });
      if (editor.selection()?.visit === origin.visit) renderSubmission(receipt);
      return receipt;
    },
  };
  return { ...navigation, dispose() { stop(); navigation.close(); } };
}
