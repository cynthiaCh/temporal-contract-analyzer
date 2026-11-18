import { browserTimers } from "./timers.js";

export function createTrailingTask(work, delay, timers = browserTimers) {
  let handle = null;
  let pending = null;
  function runTimer() {
    handle = null;
    if (pending !== null) work(...pending);
    pending = null;
  }
  return {
    push(...args) {
      if (handle !== null) timers.cancel(handle);
      pending = args;
      handle = timers.schedule(runTimer, delay);
    },
    flush() {
      if (pending !== null) work(...pending);
    },
    cancel() {
      if (handle !== null) timers.cancel(handle);
      handle = null;
      pending = null;
    },
  };
}
