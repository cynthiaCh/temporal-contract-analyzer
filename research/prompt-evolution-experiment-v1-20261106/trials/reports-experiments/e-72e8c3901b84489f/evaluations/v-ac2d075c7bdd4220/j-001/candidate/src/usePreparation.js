"use strict";

const React = require("react");
const { checkPreparation, schedulePreparationRetry, cancelPreparationRetry } = require("./preparation-api.js");

function usePreparation(initialToken) {
  const state = React.useRef({
    visible: true,
    loading: false,
    retryScheduled: false,
    checkCount: 0,
    completed: [],
    token: initialToken,
  });
  const [, render] = React.useReducer((value) => value + 1, 0);
  const lifecycle = React.useRef({ active: true, run: 0, retry: null });

  React.useEffect(() => {
    lifecycle.current.active = true;
    return () => {
      lifecycle.current.active = false;
      lifecycle.current.run += 1;
      if (lifecycle.current.retry !== null) cancelPreparationRetry(lifecycle.current.retry);
      lifecycle.current.retry = null;
    };
  }, []);

  const publish = () => render();
  const cancelRetry = () => {
    if (lifecycle.current.retry !== null) cancelPreparationRetry(lifecycle.current.retry);
    lifecycle.current.retry = null;
    state.current.retryScheduled = false;
  };
  const check = (run) => {
    if (!lifecycle.current.active || lifecycle.current.run !== run || !state.current.visible) return;
    const requestToken = state.current.token;
    lifecycle.current.retry = null;
    state.current.retryScheduled = false;
    state.current.loading = true;
    state.current.checkCount += 1;
    publish();
    checkPreparation(requestToken).then((status) => {
      if (!lifecycle.current.active || lifecycle.current.run !== run || !state.current.visible) return;
      if (status) {
        state.current.loading = false;
        state.current.retryScheduled = false;
        if (!state.current.completed.includes(requestToken)) state.current.completed.push(requestToken);
        publish();
      } else {
        state.current.retryScheduled = true;
        publish();
        const scheduledAfterCheck = state.current.checkCount;
        const handle = schedulePreparationRetry(() => check(run));
        if (lifecycle.current.active && lifecycle.current.run === run && state.current.retryScheduled && state.current.checkCount === scheduledAfterCheck) {
          lifecycle.current.retry = handle;
        } else {
          cancelPreparationRetry(handle);
        }
      }
    });
  };

  const start = () => {
    lifecycle.current.run += 1;
    cancelRetry();
    check(lifecycle.current.run);
  };

  return {
    start,
    close() {
      lifecycle.current.run += 1;
      cancelRetry();
      state.current.visible = false;
      state.current.loading = false;
      publish();
    },
    reopen(nextToken) {
      lifecycle.current.run += 1;
      cancelRetry();
      state.current.token = nextToken;
      state.current.visible = true;
      publish();
      check(lifecycle.current.run);
    },
    snapshot() {
      return { ...state.current, completed: [...state.current.completed] };
    },
  };
}

module.exports = { usePreparation };
