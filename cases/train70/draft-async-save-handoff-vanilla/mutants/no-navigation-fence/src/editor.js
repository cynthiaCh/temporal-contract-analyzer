import { attachSaveStatus } from "./save-status.js";
import { createTrailingTask } from "./trailing-task.js";
export function createDraftEditor({ store, timers, renderDocument, renderStatus }) {
  let current = null, request = 0;
  function retire() {
    const old = current; current = null;
    if (old) { old.stop(); old.task.flush(); }
  }
  return {
    open(id) {
      const ticket = ++request;
      retire();
      
      const visit = {id, latest:null};
      visit.task = createTrailingTask((text,owner) => store.write(id,text,owner),120,timers);
      current = visit;
      visit.stop = attachSaveStatus(store,id,owner => current === visit && owner === visit.latest,renderStatus);
      renderDocument({id,text:store.read(id)});
    },
    edit(text) {
      if (!current) return;
      const visit = current, owner = {};
      visit.latest = owner;
      visit.task.push(text,owner);
    },
    close() {
      const ticket = ++request;
      retire();
      renderDocument(null);
    },
  };
}
