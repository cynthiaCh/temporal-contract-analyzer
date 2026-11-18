import { createDraftEditor } from "./editor.js";
import { createNavigationProjection } from "./navigation-projection.js";

// Store notifications synchronously call integrations. Editor state and outline
// projection are separate responsibilities; only this workspace connects them.
export function createWorkspace({ store, timers, renderDocument, renderStatus, renderProjection, onSaved = () => {} }) {
  let nextVisit = 0;
  const stop = store.subscribe(event => onSaved(event, navigation));
  const editor = createDraftEditor({ store, timers, renderDocument, renderStatus });
  const projection = createNavigationProjection({ renderProjection });
  const navigation = {
    select(id) {
      const visit = ++nextVisit;
      editor.open(id, visit);
      projection.commit({ id, visit });
    },
    edit(text) { editor.edit(text); },
    close() { editor.close(); projection.clear(); },
  };
  return { ...navigation, selection: () => editor.selection(), dispose() { stop(); editor.close(); projection.clear(); } };
}
