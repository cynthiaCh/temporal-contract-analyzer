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

  const publish = () => { if (mounted.current) render(); };
  const stop = () => {
    visit.current += 1;
    if (retry.current !== null) cancelPreparationRetry(retry.current);
    retry.current = null;
    state.current.retryScheduled = false;
    state.current.loading = false;
  };
  const check = (currentVisit = visit.current) => {
    if (!mounted.current || !state.current.visible || currentVisit !== visit.current) return;
    retry.current = null;
    state.current.retryScheduled = false;
    const requestToken = state.current.token;
    state.current.loading = true;
    state.current.checkCount += 1;
    publish();
    checkPreparation(requestToken).then((status) => {
      if (!mounted.current || currentVisit !== visit.current || !state.current.visible) return;
      state.current.loading = false;
      if (status) {
        if (!state.current.completed.includes(requestToken)) state.current.completed.push(requestToken);
      } else {
        state.current.retryScheduled = true;
        let fired = false;
        const handle = schedulePreparationRetry(() => {
          fired = true;
          check(currentVisit);
        });
        if (currentVisit !== visit.current || !mounted.current || !state.current.visible) {
          cancelPreparationRetry(handle);
        } else if (!fired) {
          retry.current = handle;
        }
      }
      publish();
    });
  };

  return {
    start() {
      stop();
      check();
    },
    close() {
      stop();
      state.current.visible = false;
      publish();
    },
    reopen(nextToken) {
      stop();
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
