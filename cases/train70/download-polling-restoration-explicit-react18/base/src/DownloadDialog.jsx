"use strict";

const React = require("react");
const { usePreparation } = require("./usePreparation.js");

const DownloadDialog = React.forwardRef(function DownloadDialog({ token }, ref) {
  const preparation = usePreparation(token, { invalidateOnClose: true });
  React.useImperativeHandle(ref, () => preparation);
  const snapshot = preparation.snapshot();
  return React.createElement("section", {
    "data-surface": "download-dialog",
    "data-visible": String(snapshot.visible),
    "data-loading": String(snapshot.loading),
  });
});

module.exports = { DownloadDialog };
