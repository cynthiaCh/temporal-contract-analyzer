import { presentBatch } from "./batch-presenter.js";

export function createFeedPanel({ history, paintRows, showCount }) {
  let generation = 0;
  let dispose = () => {};
  function close() {
    generation++;
    const old = dispose;
    dispose = () => {};
    old();
  }
  return {
    show(feed, mode = "synchronous") {
      close();
      const epoch = generation;
      const listener = event => {
        const receive = frame => {
          history.record(frame);
          if (generation !== epoch) return;
          presentBatch(frame, {
            paintRows,
            showCount: value => { if (generation === epoch) showCount(value); },
          });
        };
        const decoded = feed.decode(event.detail);
        if (decoded && typeof decoded.then === "function") decoded.then(receive);
        else receive(decoded);
      };
      dispose = () => feed.target.removeEventListener("batch", listener);
      feed.target.addEventListener("batch", listener);
      feed.start(mode);
    },
    close,
  };
}
