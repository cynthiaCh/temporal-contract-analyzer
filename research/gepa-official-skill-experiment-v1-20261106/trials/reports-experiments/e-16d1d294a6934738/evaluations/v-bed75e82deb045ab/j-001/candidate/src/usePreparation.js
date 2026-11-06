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
  const retry = React.useRef(null);
  const visit = React.useRef(0);
  const mounted = React.useRef(true);

  React.useEffect(() => {
    mounted.current = true;
    return () => {
      mounted.current = false;
      visit.current += 1;
      if (retry.current !== null) cancelPreparationRetry(retry.current);
      retry.current = null;
    };
  }, []);

  const publish = () => render();
  const cancelRetry = () => {
    if (retry.current !== null) cancelPreparationRetry(retry.current);
    retry.current = null;
    state.current.retryScheduled = false;
  };
  const check = () => {
    cancelRetry();
    const currentVisit = ++visit.current;
    const requestToken = state.current.token;
    state.current.loading = true;
    state.current.checkCount += 1;
    publish();
    checkPreparation(requestToken).then((status) => {
      if (!mounted.current || currentVisit !== visit.current) return;
      if (!status) {
        retry.current = schedulePreparationRetry(() => {
          if (!mounted.current || currentVisit !== visit.current) return;
          retry.current = null;
          check();
        });
        state.current.retryScheduled = true;
        publish();
        return;
      }
      state.current.loading = false;
      if (!state.current.completed.includes(requestToken)) state.current.completed.push(requestToken);
      publish();
    });
  };

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
