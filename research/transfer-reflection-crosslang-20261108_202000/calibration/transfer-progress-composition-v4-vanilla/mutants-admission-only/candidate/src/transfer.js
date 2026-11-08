import { watchTransferProgress } from "./progress.js";
export function createTransfer(file, attemptId, transport, onCancel, progress = {}) {
  const controller = new AbortController(); let stopProgress = () => {};
  controller.signal.addEventListener("abort", () => { stopProgress(); onCancel({ file, attemptId, signal: controller.signal }); }, { once: true });
  transport({ file, attemptId, signal: controller.signal });
  if (file.progressFeed) {
    stopProgress = watchTransferProgress(file.progressFeed, progress.receive, progress.record,
      () => !controller.signal.aborted && progress.accepts());
    if (controller.signal.aborted) stopProgress();
  }
  return { file, attemptId, signal: controller.signal, cancel() { if (!controller.signal.aborted) controller.abort(); } };
}
