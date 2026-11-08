// The source is shared by visits of the same file. Decoding may settle later.
export function watchTransferProgress(feed, receive, record) {
  let nextFrame = 0;
  let displayedFrame = 0;
  const listener = event => {
    const frameNumber = ++nextFrame;
    const deliver = frame => {
      record(frame);
      // Decoding can settle out of order. History retains every decoded frame,
      // but the panel only accepts a frame newer than the one it is showing.
      if (frameNumber > displayedFrame) {
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
  return () => feed.target.removeEventListener("progress", listener);
}
