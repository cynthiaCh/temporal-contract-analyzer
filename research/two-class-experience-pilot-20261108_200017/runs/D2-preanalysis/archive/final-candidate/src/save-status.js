// A mounted document's save badge. A close/open request retires the departing
// badge immediately: it must produce no further output, including during that
// navigation call. Saving the document itself is a separate workspace concern.
export function attachSaveStatus(store, id, renderStatus) {
  return store.subscribe(event => {
    if (event.id === id) renderStatus(event);
  });
}
