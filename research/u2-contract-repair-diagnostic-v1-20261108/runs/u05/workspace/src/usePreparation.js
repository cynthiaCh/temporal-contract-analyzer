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
  const requestVersion = React.useRef(0);
  const mounted = React.useRef(true);
  const [, render] = React.useReducer((value) => value + 1, 0);

  const publish = () => {
    if (mounted.current) render();
  };

  const cancelRetry = () => {
    const scheduled = retry.current;
    if (!scheduled) return;

    retry.current = null;
    state.current.retryScheduled = false;
    cancelPreparationRetry(scheduled.handle);
  };

  const check = () => {
    if (!state.current.visible) return;

    cancelRetry();
    const requestToken = state.current.token;
    const version = ++requestVersion.current;
    state.current.loading = true;
    state.current.checkCount += 1;
    publish();

    let request;
    try {
      request = checkPreparation(requestToken);
    } catch (error) {
      if (version === requestVersion.current) {
        state.current.loading = false;
        publish();
      }
      return;
    }

    Promise.resolve(request).then((status) => {
      if (
        !mounted.current ||
        version !== requestVersion.current ||
        !state.current.visible ||
        state.current.token !== requestToken
      ) {
        return;
      }

      state.current.loading = false;
      if (status === "ready") {
        state.current.completed.push(requestToken);
      } else if (status === "pending") {
        const scheduled = { handle: undefined };
        retry.current = scheduled;
        state.current.retryScheduled = true;
        scheduled.handle = schedulePreparationRetry(() => {
          if (retry.current !== scheduled) return;
          retry.current = null;
          state.current.retryScheduled = false;
          check();
        });
      }
      publish();
    }, () => {
      if (version !== requestVersion.current || !mounted.current) return;
      state.current.loading = false;
      publish();
    });
  };

  React.useEffect(() => () => {
    mounted.current = false;
    requestVersion.current += 1;
    cancelRetry();
  }, []);

  return {
    start: check,
    close() {
      requestVersion.current += 1;
      cancelRetry();
      state.current.visible = false;
      state.current.loading = false;
      publish();
    },
    reopen(nextToken) {
      requestVersion.current += 1;
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
