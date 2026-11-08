export function createDetailPanel({ repository, renderSelection, renderDetail }) {
  let current = null;
  function close() {
    if (current) current.release();
    current = null;
    renderSelection(null);
  }
  function open(id) {
    close();
    const release = repository.watchFresh(id, record => renderDetail(record));
    current = { id, release };
    renderSelection(id);
  }
  return { open, close, selection: () => current && current.id };
}
