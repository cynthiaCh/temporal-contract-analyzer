import { subscribeFeed } from "./subscription.js";
import { presentBatch } from "./batch-presenter.js";

export function createFeedPanel({ history, paintRows, showCount }) {
  let current = null;
  function close() {
    const previous = current;
    current = null;
    if (previous) {
      previous.active = false;
      previous.release();
    }
  }
  return {
    show(feed, mode = "synchronous") {
      close();
      const visit = { feed, active: true, release: () => {} };
      current = visit;
      const valid = () => current !== null && current.feed === feed;
      const release = subscribeFeed(feed, mode, frame => {
        presentBatch(frame, {
          paintRows: value => { if (valid()) return paintRows(value); },
          showCount: value => { if (valid()) showCount(value); },
        });
      }, history, owned => { visit.release = owned; });
      if (current === visit) visit.release = release;
      else release();
    },
    close,
  };
}
