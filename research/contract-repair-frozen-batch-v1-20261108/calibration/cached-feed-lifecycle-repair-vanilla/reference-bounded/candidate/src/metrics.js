// Cached state is not a new activity delta. This consumer deliberately starts
// before observing so that synchronous snapshot delivery is excluded.
export async function collectMetrics(feed) {
  const frames = [];
  const listener = event => frames.push(event.detail);
  feed.start("synchronous");
  feed.target.addEventListener("batch", listener);
  await Promise.resolve();
  feed.emitDelta();
  feed.target.removeEventListener("batch", listener);
  return frames;
}
