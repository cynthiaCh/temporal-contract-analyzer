import { createDraftEditor } from "./editor.js";

export function createWorkspace({ store, archive, timers, renderDocument, renderStatus,
  renderSubmission = () => {}, onSaved = () => {} }) {
  const stop = store.subscribe(event => onSaved(event, navigation));
  const editor = createDraftEditor({ store, timers, renderDocument, renderStatus });
  let navigationVersion = 0;
  const navigation = {
    open(id) {
      const version = ++navigationVersion;
      renderSubmission(null);
      if (version === navigationVersion) editor.open(id);
    },
    edit(text) { editor.edit(text); },
    close() {
      const version = ++navigationVersion;
      renderSubmission(null);
      if (version === navigationVersion) editor.close();
    },
    submit() {
      const origin = editor.selection();
      if (!origin) return null;
      editor.flush();
      const receipt = archive.capture({ id: origin.id, text: origin.text });
      if (editor.selection()?.visit === origin.visit) renderSubmission(receipt);
      return receipt;
    },
  };
  return { ...navigation, dispose() { stop(); navigation.close(); } };
}
