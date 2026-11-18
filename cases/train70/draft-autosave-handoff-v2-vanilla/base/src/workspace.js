import { createDraftEditor } from "./editor.js";

export function createWorkspace(options) {
  const editor = createDraftEditor(options);
  return {
    open(id) { editor.open(id); },
    edit(text) { editor.edit(text); },
    close() { editor.close(); },
    dispose() { editor.close(); },
  };
}
