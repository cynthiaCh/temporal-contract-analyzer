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

  React.useEffect(() => () => {
    mounted.current = false;
    visit.current += 1;
    if (retry.current && retry.current.handle !== undefined) {
      cancelPreparationRetry(retry.current.handle);
    }
    retry.current = null;
  }, []);

  const publish = () => render();
  const cancelRetry = () => {
    const scheduled = retry.current;
    retry.current = null;
    if (scheduled && scheduled.handle !== undefined) cancelPreparationRetry(scheduled.handle);
    state.current.retryScheduled = false;
  };
  const check = (currentVisit) => {
    if (!mounted.current || currentVisit !== visit.current) return;
    const requestToken = state.current.token;
    state.current.loading = true;
    state.current.retryScheduled = false;
    state.current.checkCount += 1;
    publish();
    checkPreparation(requestToken).then((status) => {
      if (!mounted.current || currentVisit !== visit.current) return;
      state.current.loading = false;
      if (status) {
        if (!state.current.completed.includes(requestToken)) state.current.completed.push(requestToken);
      } else {
        state.current.retryScheduled = true;
        const scheduled = { handle: undefined };
        retry.current = scheduled;
        publish();
        const handle = schedulePreparationRetry(() => {
          if (retry.current !== scheduled) return;
          retry.current = null;
          check(currentVisit);
        });
        if (retry.current === scheduled) scheduled.handle = handle;
        else cancelPreparationRetry(handle);
        return;
      }
      publish();
    });
  };

  const start = () => {
    visit.current += 1;
    cancelRetry();
    check(visit.current);
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
      publish();
      check(visit.current);
    },
    snapshot() {
      return { ...state.current, completed: [...state.current.completed] };
    },
  };
}

module.exports = { usePreparation };
