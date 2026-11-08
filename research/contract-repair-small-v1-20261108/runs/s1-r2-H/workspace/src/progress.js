// The source is shared by visits of the same file. Decoding may settle later.
export function watchTransferProgress(feed, receive, record) {
  // A later packet can finish decoding before an earlier one. Keep recording
  // every decoded frame, but only let frames newer than the displayed one
  // repaint this observer.
  let nextFrame = 0;
  let displayedFrame = 0;
  let active = true;
  const listener = event => {
    const frameNumber = ++nextFrame;
    const deliver = frame => {
      record(frame);
      if (active && frameNumber > displayedFrame) {
        displayedFrame = frameNumber;
        receive(frame);
      }
    };
    const decoded = feed.decode(event.detail);
    if (decoded && typeof decoded.then === "function") decoded.then(deliver);
    else deliver(decoded);
  };
  feed.target.addEventListener("progress", listener);
  feed.start();
  return () => {
    active = false;
    feed.target.removeEventListener("progress", listener);
  };
}
