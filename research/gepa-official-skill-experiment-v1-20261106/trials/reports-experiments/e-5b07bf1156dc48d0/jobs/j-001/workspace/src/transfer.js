import { watchTransferProgress } from "./progress.js";

export function createTransfer(file, attemptId, transport, onCancel, progress = {}) {
  const controller = new AbortController();
  let stopProgress = () => {};
  const handle = { file, attemptId, signal: controller.signal,
    cancel() { if (!controller.signal.aborted) controller.abort(); } };
  controller.signal.addEventListener("abort", () => {
    stopProgress();
    onCancel({ file, attemptId, signal: controller.signal });
  }, { once: true });
  if (progress.ready) progress.ready(handle);
  transport({ file, attemptId, signal: controller.signal });
  if (file.progressFeed) {
    stopProgress = watchTransferProgress(file.progressFeed, progress.receive, progress.record);
    if (controller.signal.aborted) stopProgress();
  }
  return handle;
}
