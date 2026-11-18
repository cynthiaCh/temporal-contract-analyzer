// Authorized observer includes cached state before counting later deltas.
export async function collectMetrics(feed) {
  const frames = [];
  const listener = event => frames.push(event.detail);
  feed.target.addEventListener("batch", listener);
  feed.start("synchronous");
  await Promise.resolve();
  feed.emitDelta();
  feed.target.removeEventListener("batch", listener);
  return frames;
}
