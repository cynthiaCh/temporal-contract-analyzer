// paintRows may finish now or after layout. showCount reports that completed
// paint; its host may have selected another feed while painting was in progress.
export function presentBatch(frame, { paintRows, showCount }) {
  const painting = paintRows(frame);
  if (painting && typeof painting.then === "function")
    painting.then(() => showCount(frame));
  else showCount(frame);
}
