export function createDetailPanel({ repository, renderSelection, renderDetail }) {
  let current = null;
  function close() {
    const previous = current;
    current = null;
    if (previous && previous.release) previous.release();
    renderSelection(null);
  }
  function open(id) {
    close();
    const visit = { id, release: null };
    current = visit;
    renderSelection(id);
    const release = repository.watch(id, "prefer-cache", record => {
      if (current === visit) renderDetail(record);
    });
    if (current) current.release = release;
  }
  return { open, close, selection: () => current && current.id };
}
