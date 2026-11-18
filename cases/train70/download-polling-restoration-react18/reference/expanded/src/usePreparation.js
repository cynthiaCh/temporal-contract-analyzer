"use strict";
const React = require("react");
const { checkPreparation, schedulePreparationRetry, cancelPreparationRetry } = require("./preparation-api.js");
function usePreparation(initialToken, { cancelOnClose = false } = {}) {
  const state = React.useRef({ visible: true, loading: false, retryScheduled: false, checkCount: 0, completed: [], token: initialToken });
  const lifecycle = React.useRef({ generation: 0, retryHandle: null, disposed: false });
  const [, render] = React.useReducer((value) => value + 1, 0);
  const publish = () => { if (!lifecycle.current.disposed) render(); };
  const clearRetry = () => {
    if (lifecycle.current.retryHandle !== null) cancelPreparationRetry(lifecycle.current.retryHandle);
    lifecycle.current.retryHandle = null;
    state.current.retryScheduled = false;
  };
  const invalidate = () => { lifecycle.current.generation += 1; clearRetry(); state.current.loading = false; };
  const check = (generation) => {
    const requestToken = state.current.token;
    state.current.loading = true;
    state.current.checkCount += 1;
    publish();
    checkPreparation(requestToken).then((ready) => {
      if (lifecycle.current.disposed || generation !== lifecycle.current.generation) return;
      if (ready) {
        clearRetry();
        state.current.loading = false;
        if (!state.current.completed.includes(requestToken)) state.current.completed.push(requestToken);
        publish();
        return;
      }
      state.current.retryScheduled = true;
      lifecycle.current.retryHandle = schedulePreparationRetry(() => {
        if (generation !== lifecycle.current.generation) return;
        lifecycle.current.retryHandle = null;
        state.current.retryScheduled = false;
        check(generation);
      });
      publish();
    });
  };
  React.useEffect(() => () => { lifecycle.current.disposed = true; lifecycle.current.generation += 1; clearRetry(); }, []);
  return {
    start() { invalidate(); state.current.visible = true; check(lifecycle.current.generation); },
    close() { state.current.visible = false; if (cancelOnClose) invalidate(); publish(); },
    reopen(nextToken) { invalidate(); state.current.token = nextToken; state.current.visible = true; check(lifecycle.current.generation); },
    snapshot() { return { ...state.current, completed: [...state.current.completed] }; },
  };
}
module.exports = { usePreparation };
