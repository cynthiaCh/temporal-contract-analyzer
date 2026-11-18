"use strict";
const React = require("react");
const { checkPreparation, schedulePreparationRetry } = require("./preparation-api.js");
function usePreparation(initialToken) {
  const state = React.useRef({ visible: true, loading: false, retryScheduled: false, checkCount: 0, completed: [], token: initialToken });
  const [, render] = React.useReducer((value) => value + 1, 0);
  const check = () => {
    const requestToken = state.current.token;
    state.current.loading = true;
    state.current.checkCount += 1;
    render();
    checkPreparation(requestToken).then((ready) => {
      if (ready) {
        state.current.loading = false;
        state.current.retryScheduled = false;
        state.current.completed.push(requestToken);
        render();
      } else {
        state.current.retryScheduled = true;
        schedulePreparationRetry(() => { state.current.retryScheduled = false; check(); });
        render();
      }
    });
  };
  return {
    start: check,
    close() { state.current.visible = false; render(); },
    reopen(nextToken) { state.current.token = nextToken; state.current.visible = true; render(); check(); },
    snapshot() { return { ...state.current, completed: [...state.current.completed] }; },
  };
}
module.exports = { usePreparation };

