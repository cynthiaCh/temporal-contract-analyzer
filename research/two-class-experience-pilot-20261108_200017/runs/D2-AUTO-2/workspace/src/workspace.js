import { createDraftEditor } from "./editor.js";

export function createWorkspace({ store, archive, timers, renderDocument, renderStatus,
  renderSubmission = () => {}, onSaved = () => {} }) {
  const stop = store.subscribe(event => onSaved(event, navigation));
  const editor = createDraftEditor({ store, timers, renderDocument, renderStatus });
  let navigationVersion = 0;
  function beginNavigation() {
    const version = ++navigationVersion;
    renderSubmission(null);
    return () => version === navigationVersion;
  }
  const navigation = {
    open(id) {
      const isCurrent = beginNavigation();
      editor.close(isCurrent);
      if (isCurrent()) editor.open(id, isCurrent);
    },
    edit(text) { editor.edit(text); },
    close() {
      const isCurrent = beginNavigation();
      editor.close(isCurrent);
    },
    submit() {
      const origin = editor.selection();
      if (!origin) return null;
      editor.persist(origin);
      const receipt = archive.capture({ id: origin.id, text: origin.text });
      if (editor.isActive(origin)) renderSubmission(receipt);
      return receipt;
    },
  };
  return { ...navigation, dispose() { stop(); navigation.close(); } };
}
