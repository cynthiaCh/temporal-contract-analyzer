import { attachSaveStatus } from "./save-status.js";
export function createDraftEditor({ store, timers, renderDocument, renderStatus }) {
  let current = null;
  function retire() {
    const old = current; current = null;
    if (old) old.stop();
  }
  return {
    open(id) {
      retire();
      const visit = {id, latest:null};
      current = visit;
      visit.stop = attachSaveStatus(store, id, owner => current === visit && owner === visit.latest, renderStatus);
      renderDocument({id, text:store.read(id)});
    },
    edit(text) {
      if (!current) return;
      const visit = current, owner = {};
      visit.latest = owner;
      store.write(visit.id, text, owner);
    },
    close() { retire(); renderDocument(null); },
  };
}
