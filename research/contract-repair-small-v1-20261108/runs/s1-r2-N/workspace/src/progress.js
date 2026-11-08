// The source is shared by visits of the same file. Decoding may settle later.
export function watchTransferProgress(feed, receive, record) {
  let nextFrame = 0;
  let newestDisplayed = -1;
  const listener = event => {
    const frameNumber = nextFrame++;
    const deliver = frame => {
      // History remains a complete audit of decoded frames. Full frames can
      // finish decoding out of order, however, so only a newer source frame
      // may replace what the panel is currently displaying.
      record(frame);
      if (frameNumber > newestDisplayed) {
        newestDisplayed = frameNumber;
        receive(frame);
      }
    };
    const decoded = feed.decode(event.detail);
    if (decoded && typeof decoded.then === "function") decoded.then(deliver);
    else deliver(decoded);
  };
  feed.target.addEventListener("progress", listener);
  // A warm feed can synchronously dispatch its cached full frame from start.
  // Subscribe first so that bootstrap reaches the panel; telemetry deliberately
  // retains its separate live-delta subscription order.
  feed.start();
  return () => feed.target.removeEventListener("progress", listener);
}
