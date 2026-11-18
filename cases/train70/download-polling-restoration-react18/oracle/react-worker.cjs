"use strict";

const path = require("path");
const candidateRoot = path.resolve(process.argv[2] || "");
const surface = process.argv[3];
const scenario = process.argv[4];
if (!['download', 'background'].includes(surface)) throw new Error('unknown surface');

const runtimeRoot = path.resolve(__dirname, "../../../../../runtimes/react18");
process.env.NODE_PATH = path.join(runtimeRoot, "node_modules");
require("module").Module._initPaths();
require.extensions[".jsx"] = require.extensions[".js"];
const { JSDOM } = require(path.join(runtimeRoot, "node_modules/jsdom"));
const React = require(path.join(runtimeRoot, "node_modules/react"));
const { act } = React;
const { createRoot } = require(path.join(runtimeRoot, "node_modules/react-dom/client"));

const dom = new JSDOM("<!doctype html><html><body><div id=root></div></body></html>");
global.window = dom.window;
global.document = dom.window.document;
global.navigator = dom.window.navigator;
global.IS_REACT_ACT_ENVIRONMENT = true;

function deferred() {
  let resolve;
  const promise = new Promise((accept) => { resolve = accept; });
  return { promise, resolve };
}

async function flush(action) {
  await act(async () => {
    if (action) action();
    await Promise.resolve();
    await Promise.resolve();
  });
}

async function main() {
  const requests = [];
  const retries = new Map();
  let retryId = 0;
  global.__preparationTransport = (token) => {
    const pending = deferred();
    requests.push({ token, ...pending });
    return pending.promise;
  };
  global.__schedulePreparationRetry = (callback) => {
    const id = ++retryId;
    retries.set(id, callback);
    return id;
  };
  global.__cancelPreparationRetry = (id) => retries.delete(id);
  const fireRetry = async () => {
    const entry = [...retries.entries()][0];
    if (!entry) return false;
    retries.delete(entry[0]);
    await flush(entry[1]);
    return true;
  };
  const settle = async (index, ready) => {
    if (!requests[index]) throw new Error(`request ${index} is missing`);
    await flush(() => requests[index].resolve(ready));
  };

  const Component = require(path.join(candidateRoot, "src", surface === 'download' ? "DownloadDialog.jsx" : "BackgroundExportPanel.jsx"))[surface === 'download' ? "DownloadDialog" : "BackgroundExportPanel"];
  const ref = React.createRef();
  const root = createRoot(document.getElementById("root"));
  const initialToken = surface === 'download' ? 'package-a' : 'workspace-export';
  await flush(() => root.render(React.createElement(Component, { token: initialToken, ref })));
  const snapshot = () => ref.current.snapshot();
  const record = { initial: snapshot() };

  if (scenario === 'pending-then-ready') {
    await flush(() => ref.current.start());
    await settle(0, false);
    record.afterFirstPending = snapshot();
    record.firstRetryFired = await fireRetry();
    if (record.firstRetryFired) {
      await settle(1, false);
      record.afterSecondPending = snapshot();
      record.secondRetryFired = await fireRetry();
      if (record.secondRetryFired) await settle(2, true);
    } else {
      record.afterSecondPending = snapshot();
      record.secondRetryFired = false;
    }
    record.final = snapshot();
  } else if (scenario === 'close-pending' || scenario === 'close-ready') {
    await flush(() => ref.current.start());
    await flush(() => ref.current.close());
    record.afterClose = snapshot();
    await settle(0, scenario === 'close-ready');
    record.afterResponse = snapshot();
    record.retryFired = await fireRetry();
    if (surface === 'background' && record.retryFired) await settle(1, true);
    record.final = snapshot();
  } else if (scenario === 'reopen-stale') {
    await flush(() => ref.current.start());
    await flush(() => ref.current.close());
    await flush(() => ref.current.reopen('package-b'));
    await settle(0, true);
    record.afterStale = snapshot();
    await settle(1, true);
    record.final = snapshot();
  } else {
    throw new Error('unknown scenario');
  }
  record.requests = requests.map(({ token }) => token);
  await flush(() => root.unmount());
  process.stdout.write(JSON.stringify(record));
}

main().catch((error) => {
  process.stderr.write(`${error.stack || error.message}\n`);
  process.exitCode = 2;
});
