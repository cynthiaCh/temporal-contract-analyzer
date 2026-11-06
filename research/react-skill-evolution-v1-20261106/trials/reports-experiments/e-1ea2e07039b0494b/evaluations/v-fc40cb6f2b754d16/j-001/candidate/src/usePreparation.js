"use strict";

const React = require("react");
const api = require("./preparation-api.js");

function usePreparation(initialToken) {
  const state = React.useRef({
    visible: true,
    loading: false,
    retryScheduled: false,
    checkCount: 0,
    completed: [],
    token: initialToken,
  });
  const visit = React.useRef(0);
  const retry = React.useRef(null);
  const mounted = React.useRef(true);
  const [, render] = React.useReducer((value) => value + 1, 0);

  React.useEffect(() => {
    mounted.current = true;
    return () => {
      mounted.current = false;
      visit.current += 1;
      if (retry.current !== null) api.cancelPreparationRetry(retry.current);
      retry.current = null;
    };
  }, []);

  const publish = () => render();
  const cancelRetry = () => {
    if (retry.current !== null) api.cancelPreparationRetry(retry.current);
    retry.current = null;
    state.current.retryScheduled = false;
  };
  const check = (owner) => {
    if (!mounted.current || owner !== visit.current) return;
    const requestToken = state.current.token;
    state.current.loading = true;
    state.current.checkCount += 1;
    publish();
    api.checkPreparation(requestToken).then((ready) => {
      if (!mounted.current || owner !== visit.current) return;
      if (ready) {
        state.current.loading = false;
        state.current.retryScheduled = false;
        if (!state.current.completed.includes(requestToken)) {
          state.current.completed.push(requestToken);
        }
        publish();
      } else {
        state.current.retryScheduled = true;
        publish();
        const handle = api.schedulePreparationRetry(() => {
          if (!mounted.current || owner !== visit.current) return;
          retry.current = null;
          state.current.retryScheduled = false;
          check(owner);
        });
        if (mounted.current && owner === visit.current && state.current.retryScheduled) {
          retry.current = handle;
        } else {
          api.cancelPreparationRetry(handle);
        }
      }
    });
  };
  const start = () => {
    cancelRetry();
    const owner = ++visit.current;
    check(owner);
  };

  return {
    start,
    close() {
      visit.current += 1;
      cancelRetry();
      state.current.visible = false;
      state.current.loading = false;
      publish();
    },
    reopen(nextToken) {
      visit.current += 1;
      cancelRetry();
      state.current.token = nextToken;
      state.current.visible = true;
      start();
    },
    snapshot() {
      return { ...state.current, completed: [...state.current.completed] };
    },
  };
}

module.exports = { usePreparation };
