export function attachSaveStatus(store, id, accepts, renderStatus) {
  return store.subscribe(event => {
    if (event.id === id && accepts(event.owner)) renderStatus(event);
  });
}
