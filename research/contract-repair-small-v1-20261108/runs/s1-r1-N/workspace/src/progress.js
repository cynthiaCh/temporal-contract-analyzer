// The source is shared by visits of the same file. Decoding may settle later.
export function watchTransferProgress(feed, receive, record) {
  let newestDisplayed = -1;
  let nextFrame = 0;
  const listener = event => {
    const frameNumber = nextFrame++;
    const deliver = frame => {
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
  feed.start();
  return () => feed.target.removeEventListener("progress", listener);
}
