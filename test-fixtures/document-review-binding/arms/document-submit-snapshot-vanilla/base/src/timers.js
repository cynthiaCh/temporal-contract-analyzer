export const browserTimers = {
  schedule(callback, delay) { return setTimeout(callback, delay); },
  cancel(handle) { clearTimeout(handle); },
};
