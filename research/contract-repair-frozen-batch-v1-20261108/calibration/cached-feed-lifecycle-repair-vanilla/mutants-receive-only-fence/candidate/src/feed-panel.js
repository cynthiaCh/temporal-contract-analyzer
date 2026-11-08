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
      const valid = () => visit.active;
      const release = subscribeFeed(feed, mode, frame => {
        if (valid()) presentBatch(frame, { paintRows, showCount });
      }, history, owned => { visit.release = owned; });
      if (current === visit) visit.release = release;
      else release();
    },
    close,
  };
}
