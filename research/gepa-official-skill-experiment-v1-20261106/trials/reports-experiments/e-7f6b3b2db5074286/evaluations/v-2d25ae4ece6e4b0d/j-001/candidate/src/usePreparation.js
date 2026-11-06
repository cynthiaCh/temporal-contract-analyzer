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
  const visit = React.useRef(0);
  const retry = React.useRef(null);
  const mounted = React.useRef(true);

  const publish = () => render();
  const cancelRetry = () => {
    if (retry.current !== null) {
      cancelPreparationRetry(retry.current);
      retry.current = null;
    }
    state.current.retryScheduled = false;
  };
  const check = () => {
    if (!mounted.current || !state.current.visible) return;
    cancelRetry();
    const currentVisit = ++visit.current;
    const requestToken = state.current.token;
    state.current.loading = true;
    state.current.checkCount += 1;
    publish();
    checkPreparation(requestToken).then((status) => {
      if (!mounted.current || currentVisit !== visit.current || !state.current.visible) return;
      if (!status) {
        state.current.retryScheduled = true;
        publish();
        // A scheduler may invoke its callback before returning its handle.
        const handle = schedulePreparationRetry(() => {
          if (currentVisit !== visit.current || !mounted.current || !state.current.visible) return;
          retry.current = null;
          check();
        });
        if (currentVisit === visit.current && mounted.current && state.current.visible) retry.current = handle;
        else cancelPreparationRetry(handle);
        return;
      }
      state.current.loading = false;
      state.current.retryScheduled = false;
      if (!state.current.completed.includes(requestToken)) state.current.completed.push(requestToken);
      publish();
    });
  };

  React.useEffect(() => {
    mounted.current = true;
    return () => {
      mounted.current = false;
      visit.current += 1;
      cancelRetry();
    };
  }, []);

  return {
    start: check,
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
      publish();
      check();
    },
    snapshot() {
      return { ...state.current, completed: [...state.current.completed] };
    },
  };
}

module.exports = { usePreparation };
