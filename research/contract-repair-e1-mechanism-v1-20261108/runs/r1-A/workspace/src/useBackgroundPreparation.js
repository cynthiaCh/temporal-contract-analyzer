"use strict";

const React = require("react");
const {
  PREPARATION_STATUS,
  checkPreparation,
  schedulePreparationRetry,
  cancelPreparationRetry,
} = require("./preparation-api.js");

function useBackgroundPreparation(initialToken) {
  const state = React.useRef({
    visible: true,
    loading: false,
    retryScheduled: false,
    checkCount: 0,
    completed: [],
    token: initialToken,
  });
  const retryHandle = React.useRef(null);
  const active = React.useRef(true);
  const [, render] = React.useReducer((value) => value + 1, 0);
  const publish = () => {
    if (active.current) render();
  };
  const clearRetry = () => {
    if (retryHandle.current !== null) cancelPreparationRetry(retryHandle.current);
    retryHandle.current = null;
    state.current.retryScheduled = false;
  };
  const check = () => {
    const requestToken = state.current.token;
    state.current.loading = true;
    state.current.checkCount += 1;
    publish();
    checkPreparation(requestToken).then((status) => {
      if (!active.current) return;
      if (status === PREPARATION_STATUS.READY) {
        clearRetry();
        state.current.loading = false;
        if (!state.current.completed.includes(requestToken)) {
          state.current.completed.push(requestToken);
        }
        publish();
        return;
      }
      state.current.retryScheduled = true;
      retryHandle.current = schedulePreparationRetry(() => {
        retryHandle.current = null;
        state.current.retryScheduled = false;
        check();
      });
      publish();
    });
  };

  React.useEffect(() => () => {
    active.current = false;
    clearRetry();
  }, []);

  return {
    start: check,
    close() {
      // Closing this progress panel does not cancel workspace-owned work.
      state.current.visible = false;
      publish();
    },
    snapshot() {
      return { ...state.current, completed: [...state.current.completed] };
    },
  };
}

module.exports = { useBackgroundPreparation };
