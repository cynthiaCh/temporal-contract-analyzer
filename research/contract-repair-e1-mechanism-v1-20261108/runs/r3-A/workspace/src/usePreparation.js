"use strict";

const React = require("react");
const {
  PREPARATION_STATUS,
  checkPreparation,
  schedulePreparationRetry,
  cancelPreparationRetry,
} = require("./preparation-api.js");

function usePreparation(initialToken, { invalidateOnClose = false } = {}) {
  const state = React.useRef({
    visible: true,
    loading: false,
    retryScheduled: false,
    checkCount: 0,
    completed: [],
    token: initialToken,
  });
  const lifecycle = React.useRef({
    generation: 0,
    retryHandle: null,
    disposed: false,
  });
  const [, render] = React.useReducer((value) => value + 1, 0);

  const publish = () => {
    if (!lifecycle.current.disposed) render();
  };
  const clearRetry = () => {
    if (lifecycle.current.retryHandle !== null) {
      cancelPreparationRetry(lifecycle.current.retryHandle);
    }
    lifecycle.current.retryHandle = null;
    state.current.retryScheduled = false;
  };
  const beginGeneration = () => {
    lifecycle.current.generation += 1;
    clearRetry();
    state.current.loading = false;
    return lifecycle.current.generation;
  };
  const check = (generation) => {
    if (lifecycle.current.disposed || generation !== lifecycle.current.generation) return;
    const requestToken = state.current.token;
    state.current.loading = true;
    state.current.checkCount += 1;
    publish();
    checkPreparation(requestToken).then((status) => {
      if (lifecycle.current.disposed || generation !== lifecycle.current.generation) return;
      if (status === PREPARATION_STATUS.READY) {
        clearRetry();
        state.current.loading = false;
        if (!state.current.completed.includes(requestToken)) {
          state.current.completed.push(requestToken);
        }
        publish();
        return;
      }

      // A pending result belongs to this generation.  Capture it in the retry
      // callback so a timer that escaped cancellation cannot start work for a
      // dialog that has since been closed, reopened, or retargeted.
      state.current.retryScheduled = true;
      let handle = null;
      const retry = () => {
        if (lifecycle.current.disposed || generation !== lifecycle.current.generation) return;
        if (lifecycle.current.retryHandle === handle) {
          lifecycle.current.retryHandle = null;
        }
        state.current.retryScheduled = false;
        check(generation);
      };
      handle = schedulePreparationRetry(retry);
      lifecycle.current.retryHandle = handle;
      publish();
    });
  };

  React.useEffect(() => () => {
    lifecycle.current.disposed = true;
    beginGeneration();
  }, []);

  return {
    start() {
      state.current.visible = true;
      check(beginGeneration());
    },
    close() {
      state.current.visible = false;
      if (invalidateOnClose) beginGeneration();
      publish();
    },
    reopen(nextToken) {
      state.current.token = nextToken;
      state.current.visible = true;
      publish();
      check(beginGeneration());
    },
    snapshot() {
      return { ...state.current, completed: [...state.current.completed] };
    },
  };
}

module.exports = { usePreparation };
