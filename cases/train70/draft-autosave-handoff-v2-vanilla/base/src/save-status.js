export function attachSaveStatus(store, id, renderStatus) {
  return store.subscribe(event => {
    if (event.id === id) renderStatus(event);
  });
}
