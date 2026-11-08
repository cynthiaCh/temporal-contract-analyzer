import { subscribeFeed } from "./subscription.js";
import { presentBatch } from "./batch-presenter.js";

export function createFeedPanel({ history, paintRows, showCount }) {
  let release = () => {};
  return {
    show(feed, mode = "synchronous") {
      release();
      release = subscribeFeed(feed, mode, frame =>
        presentBatch(frame, { paintRows, showCount }), history);
    },
    close() {
      release();
      release = () => {};
    },
  };
}
