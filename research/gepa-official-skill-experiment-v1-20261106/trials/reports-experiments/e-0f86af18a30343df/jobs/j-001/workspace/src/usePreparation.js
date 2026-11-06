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
  const lifecycle = React.useRef({ generation: 0, retry: null, mounted: true });

  React.useEffect(() => {
    lifecycle.current.mounted = true;
    return () => {
      lifecycle.current.mounted = false;
      lifecycle.current.generation += 1;
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
  const check = (generation) => {
    const requestToken = state.current.token;
    state.current.loading = true;
    state.current.checkCount += 1;
    publish();
    checkPreparation(requestToken).then((status) => {
      if (!lifecycle.current.mounted || lifecycle.current.generation !== generation) return;
      state.current.loading = false;
      if (status) {
        if (!state.current.completed.includes(requestToken)) state.current.completed.push(requestToken);
        state.current.retryScheduled = false;
        publish();
      } else {
        let fired = false;
        const retry = schedulePreparationRetry(() => {
          fired = true;
          if (!lifecycle.current.mounted || lifecycle.current.generation !== generation) return;
          lifecycle.current.retry = null;
          state.current.retryScheduled = false;
          check(generation);
        });
        if (lifecycle.current.mounted && lifecycle.current.generation === generation && !fired) {
          lifecycle.current.retry = retry;
          state.current.retryScheduled = true;
          publish();
        } else {
          cancelPreparationRetry(retry);
        }
      }
    });
  };

  const start = () => {
    lifecycle.current.generation += 1;
    cancelRetry();
    check(lifecycle.current.generation);
  };

  return {
    start,
    close() {
      lifecycle.current.generation += 1;
      cancelRetry();
      state.current.visible = false;
      state.current.loading = false;
      publish();
    },
    reopen(nextToken) {
      lifecycle.current.generation += 1;
      cancelRetry();
      state.current.token = nextToken;
      state.current.visible = true;
      check(lifecycle.current.generation);
    },
    snapshot() {
      return { ...state.current, completed: [...state.current.completed] };
    },
  };
}

module.exports = { usePreparation };
