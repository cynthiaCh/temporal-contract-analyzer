"use strict";

const React = require("react");
const {
  checkPreparation,
  schedulePreparationRetry,
  cancelPreparationRetry,
} = require("./preparation-api.js");

function isReady(status) {
  // Older transports report readiness as a boolean; newer ones use an
  // explicit status.  In particular, do not treat the truthy "pending"
  // status as a completed download.
  return status === true || status === "ready";
}

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
  const generation = React.useRef(0);
  const mounted = React.useRef(true);
  const [, render] = React.useReducer((value) => value + 1, 0);

  const publish = () => render();

  const cancelRetry = () => {
    if (retry.current !== null) {
      cancelPreparationRetry(retry.current);
      retry.current = null;
    }
    state.current.retryScheduled = false;
  };

  const check = (requestedToken = state.current.token) => {
    cancelRetry();
    const requestToken = requestedToken;
    const requestGeneration = ++generation.current;
    state.current.loading = true;
    state.current.checkCount += 1;
    publish();

    let preparation;
    try {
      preparation = checkPreparation(requestToken);
    } catch (error) {
      if (mounted.current && requestGeneration === generation.current) {
        state.current.loading = false;
        publish();
      }
      return;
    }

    Promise.resolve(preparation)
      .then((status) => {
        if (!mounted.current || requestGeneration !== generation.current) return;
        state.current.loading = false;
        if (isReady(status)) {
          if (!state.current.completed.includes(requestToken)) {
            state.current.completed.push(requestToken);
          }
          publish();
          return;
        }

        state.current.loading = true;
        retry.current = schedulePreparationRetry(() => {
          retry.current = null;
          if (!mounted.current || requestGeneration !== generation.current) return;
          check(requestToken);
        });
        state.current.retryScheduled = true;
        publish();
      })
      .catch(() => {
        if (!mounted.current || requestGeneration !== generation.current) return;
        state.current.loading = false;
        state.current.retryScheduled = false;
        publish();
      });
  };

  React.useEffect(() => {
    mounted.current = true;
    return () => {
      mounted.current = false;
      generation.current += 1;
      cancelRetry();
    };
  }, []);

  return {
    start: check,
    close() {
      state.current.visible = false;
      generation.current += 1;
      state.current.loading = false;
      cancelRetry();
      publish();
    },
    reopen(nextToken) {
      generation.current += 1;
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
