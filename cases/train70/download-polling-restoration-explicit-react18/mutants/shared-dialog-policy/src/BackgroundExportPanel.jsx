"use strict";
const React = require("react");
const { usePreparation } = require("./usePreparation.js");
const BackgroundExportPanel = React.forwardRef(function BackgroundExportPanel({ token }, ref) {
  const preparation = usePreparation(token, { invalidateOnClose: true });
  React.useImperativeHandle(ref, () => preparation);
  const snapshot = preparation.snapshot();
  return React.createElement("section", { "data-surface": "background-export", "data-visible": String(snapshot.visible), "data-loading": String(snapshot.loading) });
});
module.exports = { BackgroundExportPanel };
