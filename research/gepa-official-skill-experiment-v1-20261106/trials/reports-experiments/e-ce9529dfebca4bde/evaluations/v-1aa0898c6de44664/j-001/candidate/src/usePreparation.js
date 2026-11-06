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
  const attempt = React.useRef(0);
  const mounted = React.useRef(true);

  React.useEffect(() => {
    mounted.current = true;
    return () => {
      mounted.current = false;
      attempt.current += 1;
      if (retry.current !== null) cancelPreparationRetry(retry.current);
      retry.current = null;
    };
  }, []);

  const publish = () => render();
  const stop = () => {
    attempt.current += 1;
    if (retry.current !== null) cancelPreparationRetry(retry.current);
    retry.current = null;
    state.current.retryScheduled = false;
    state.current.loading = false;
  };
  const check = (currentAttempt) => {
    if (!mounted.current || currentAttempt !== attempt.current) return;
    retry.current = null;
    state.current.retryScheduled = false;
    const requestToken = state.current.token;
    state.current.loading = true;
    state.current.checkCount += 1;
    publish();
    checkPreparation(requestToken).then((status) => {
      if (!mounted.current || currentAttempt !== attempt.current) return;
      if (status) {
        state.current.loading = false;
        state.current.retryScheduled = false;
        if (!state.current.completed.includes(requestToken)) state.current.completed.push(requestToken);
        publish();
      } else {
        state.current.retryScheduled = true;
        publish();
        let fired = false;
        const handle = schedulePreparationRetry(() => {
          fired = true;
          check(currentAttempt);
        });
        if (fired || !mounted.current || currentAttempt !== attempt.current || !state.current.retryScheduled) {
          cancelPreparationRetry(handle);
        } else {
          retry.current = handle;
        }
      }
    });
  };

  return {
    start() {
      stop();
      check(attempt.current);
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
      check(attempt.current);
    },
    snapshot() {
      return { ...state.current, completed: [...state.current.completed] };
    },
  };
}

module.exports = { usePreparation };
