import { watchTransferProgress } from "./progress.js";

export function createTransfer(file, attemptId, transport, onCancel, progress = {}) {
  const controller = new AbortController();
  let stopProgress = () => {};
  controller.signal.addEventListener("abort", () => {
    stopProgress();
    onCancel({ file, attemptId, signal: controller.signal });
  }, { once: true });
  if (file.progressFeed) {
    stopProgress = watchTransferProgress(file.progressFeed, progress.receive, progress.record);
    if (controller.signal.aborted) stopProgress();
  }
  // Installing the receiver may synchronously navigate away. Do not start a
  // producer after that ownership has been invalidated.
  if (!controller.signal.aborted && (!progress.isActive || progress.isActive())) {
    transport({ file, attemptId, signal: controller.signal });
  } else if (!controller.signal.aborted) {
    controller.abort();
  }
  return { file, attemptId, signal: controller.signal,
    cancel() { if (!controller.signal.aborted) controller.abort(); } };
}
