"use strict";

const React = require("react");
const {
  checkPreparation,
  schedulePreparationRetry,
  cancelPreparationRetry,
} = require("./preparation-api.js");

function usePreparation(initialToken) {
  const state = React.useRef({
    visible: true,
    loading: false,
    retryScheduled: false,
    checkCount: 0,
    completed: [],
    token: initialToken,
  });
  const retry = React.useRef(null);
  const active = React.useRef(true);
  const [, render] = React.useReducer((value) => value + 1, 0);

  const publish = () => render();
  const check = React.useCallback(() => {
    const requestToken = state.current.token;
    state.current.loading = true;
    state.current.checkCount += 1;
    publish();
    checkPreparation(requestToken).then((ready) => {
      if (!active.current) return;

      if (ready) {
        retry.current = null;
        state.current.loading = false;
        if (!state.current.completed.includes(requestToken)) {
          state.current.completed.push(requestToken);
        }
        state.current.retryScheduled = false;
      } else {
        retry.current = schedulePreparationRetry(check);
        state.current.retryScheduled = true;
      }
      publish();
    });
  }, []);

  React.useEffect(() => {
    active.current = true;
    return () => {
      active.current = false;
      if (retry.current !== null) cancelPreparationRetry(retry.current);
    };
  }, []);

  return {
    start: check,
    close() {
      state.current.visible = false;
      publish();
    },
    reopen(nextToken) {
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
