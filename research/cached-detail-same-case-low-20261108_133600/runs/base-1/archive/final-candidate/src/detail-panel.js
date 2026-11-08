export function createDetailPanel({ repository, renderSelection, renderDetail }) {
  let current = null;
  function close() {
    if (current) current.release();
    current = null;
    renderSelection(null);
  }
  function open(id) {
    close();
    // A prefer-cache watch may deliver synchronously.  Establish this activation
    // first so its cached row has a selected destination, and so navigation from
    // that delivery can supersede it before the watch has returned its handle.
    const activation = { id, release: () => {} };
    current = activation;
    renderSelection(id);
    const release = repository.watch(id, "prefer-cache", record => {
      if (current === activation) renderDetail(record);
    });

    // renderDetail integrations may have opened another panel or closed this one
    // during an inline cache delivery.  A handle returned for a departed
    // activation must not retain a transport subscription.
    if (current === activation) activation.release = release;
    else release();
  }
  return { open, close, selection: () => current && current.id };
}
