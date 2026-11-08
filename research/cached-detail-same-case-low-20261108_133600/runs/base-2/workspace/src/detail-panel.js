export function createDetailPanel({ repository, renderSelection, renderDetail }) {
  let current = null;
  function close() {
    const activation = current;
    current = null;
    renderSelection(null);
    if (activation) {
      if (activation.release) activation.release();
      else activation.cancelled = true;
    }
  }
  function open(id) {
    close();
    // A cache-preferred watch may deliver synchronously, so make this activation
    // current before subscribing. A delivery integration can navigate away before
    // the watch returns its release handle.
    const activation = { id, release: null, cancelled: false };
    current = activation;
    renderSelection(id);
    const release = repository.watch(id, "prefer-cache", record => {
      if (current === activation) renderDetail(record);
    });
    activation.release = release;
    if (current !== activation || activation.cancelled) release();
  }
  return { open, close, selection: () => current && current.id };
}
