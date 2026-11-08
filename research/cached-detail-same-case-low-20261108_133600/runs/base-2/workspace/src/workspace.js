import { createDetailPanel } from "./detail-panel.js";

export function createDetailWorkspace({ repository, renderSelection, renderDetail, onDetail = () => {} }) {
  let navigation;
  const panel = createDetailPanel({
    repository, renderSelection,
    renderDetail(record) {
      renderDetail(record);
      // Integrations run in this delivery call, and may open or close a panel.
      onDetail(record, navigation);
    },
  });
  navigation = { open: id => panel.open(id), close: () => panel.close() };
  return { ...navigation, selection: () => panel.selection() };
}
