import { browserTimers } from "./timers.js";

export function createTrailingTask(work, delay, timers = browserTimers) {
  let handle = null;
  let pending = null;
  function flush() {
    if (handle !== null) timers.cancel(handle);
    handle = null;
    const args = pending;
    pending = null;
    if (args !== null) work(...args);
  }
  return {
    push(...args) {
      if (handle !== null) timers.cancel(handle);
      pending = args;
      handle = timers.schedule(flush, delay);
    },
    flush,
    cancel: flush,
  };
}
