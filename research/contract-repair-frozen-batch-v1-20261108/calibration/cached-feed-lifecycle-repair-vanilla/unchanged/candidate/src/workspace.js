import { createFeedPanel } from "./feed-panel.js";

// Rendering is a host integration boundary, not a pure read of panel state.
export function createFeedWorkspace({ history, paintRows, showCount }) {
  const panel = createFeedPanel({
    history, showCount,
    paintRows: frame => paintRows(frame, navigation),
  });
  const navigation = {
    select(feed, mode = "synchronous") { panel.show(feed, mode); },
    hide() { panel.close(); },
  };
  return navigation;
}
