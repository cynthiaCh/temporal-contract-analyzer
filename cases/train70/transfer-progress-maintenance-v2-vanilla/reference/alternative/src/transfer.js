import { watchTransferProgress } from "./progress.js";

export function createTransfer(file, attemptId, transport, onCancel, progress = {}) {
  const controller = new AbortController();
  let stopProgress = () => {};
  controller.signal.addEventListener("abort", () => {
    stopProgress();
    onCancel({ file, attemptId, signal: controller.signal });
  }, { once: true });
  const handle = { file, attemptId, signal: controller.signal,
    cancel() { if (!controller.signal.aborted) controller.abort(); } };
  if (progress.onHandle) progress.onHandle(handle);
  transport({ file, attemptId, signal: controller.signal });
  if (file.progressFeed) {
    stopProgress = watchTransferProgress(file.progressFeed, progress.receive, progress.record, () => !controller.signal.aborted);
    if (controller.signal.aborted) stopProgress();
  }
  return handle;
}
