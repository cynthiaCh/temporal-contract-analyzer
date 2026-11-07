"use strict";

const React = require("react");
const api = require("./preparation-api.js");

function isReady(status) {
  return status === true || status === "ready" ||
    Boolean(status && (status.ready === true || status.status === "ready"));
}

// Background exports are normally owned by the workspace.  A token ending in
// this authorization suffix is the explicit exception: it belongs to the
// foreground dialog and must stop when that surface is closed.
function isDialogOwned(token) {
  return typeof token === "string" && token.endsWith(":dialog");
}

class BackgroundExportPanel extends React.Component {
  constructor(props) {
    super(props);
    this.state = { visible: true, loading: false, retryScheduled: false, checkCount: 0, completed: [], token: props.token };
    this.retry = null;
    this.active = true;
  }

  componentWillUnmount() {
    this.active = false;
    if (this.retry !== null) api.cancelPreparationRetry(this.retry);
  }

  start = () => {
    const token = this.state.token;
    this.setState((state) => ({ loading: true, checkCount: state.checkCount + 1 }));
    api.checkPreparation(token).then((done) => {
      if (!this.active) return;
      if (isReady(done)) {
        this.retry = null;
        this.setState((state) => ({
          loading: false,
          retryScheduled: false,
          completed: state.completed.includes(token) ? state.completed : [...state.completed, token],
        }));
      } else {
        this.retry = api.schedulePreparationRetry(this.start);
        this.setState({ retryScheduled: true });
      }
    });
  };

  close = () => {
    if (isDialogOwned(this.state.token)) {
      this.active = false;
      if (this.retry !== null) {
        api.cancelPreparationRetry(this.retry);
        this.retry = null;
      }
      this.setState({ visible: false, loading: false, retryScheduled: false });
      return;
    }
    this.setState({ visible: false });
  };

  snapshot = () => ({ ...this.state, completed: [...this.state.completed] });

  render() {
    return React.createElement("section", {
      "data-surface": "background-export",
      "data-visible": String(this.state.visible),
      "data-loading": String(this.state.loading),
    });
  }
}

module.exports = { BackgroundExportPanel };
