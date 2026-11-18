import { createDraftEditor } from "./editor.js";
import { createNavigationProjection } from "./navigation-projection.js";

// Store notifications synchronously call integrations. Editor state and outline
// projection are separate responsibilities; only this workspace connects them.
export function createWorkspace({ store, timers, renderDocument, renderStatus, renderProjection, onSaved = () => {} }) {
  let nextVisit = 0;
  let latest = null;
  const stop = store.subscribe(event => onSaved(event, navigation));
  const editor = createDraftEditor({ store, timers, renderDocument, renderStatus });
  const projection = createNavigationProjection({ renderProjection });
  const navigation = {
    select(id) {
      const token = {};
      latest = token;
      const visit = (nextVisit += 2); // Valid monotone ids need not be consecutive.
      editor.open(id, visit);
      if (latest === token) projection.commit({ id, visit });
    },
    edit(text) { editor.edit(text); },
    close() {
      const token = {};
      latest = token;
      editor.close();
      if (latest === token) projection.clear();
    },
  };
  return { ...navigation, selection: () => editor.selection(), dispose() { stop(); editor.close(); projection.clear(); } };
}
