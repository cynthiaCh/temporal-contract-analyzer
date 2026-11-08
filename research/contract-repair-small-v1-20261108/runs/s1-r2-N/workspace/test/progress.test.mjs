import assert from "node:assert/strict";
import { createProgressFeed, createTransferWorkspace, collectProgressTelemetry } from "../src/workspace.js";

function deferred() {
  let resolve;
  const promise = new Promise(currentResolve => { resolve = currentResolve; });
  return { promise, resolve };
}

{
  const history = [];
  const shown = [];
  const feed = createProgressFeed({ initialPacket: { loaded: 4 } });
  const workspace = createTransferWorkspace({
    transport() {}, onCancel() {}, record() {}, showQueued() {},
    recordProgress: item => history.push(item.frame),
    showProgress: item => shown.push(item.frame),
  });

  workspace.select({ id: "warm", progressFeed: feed });
  assert.deepEqual(history, [{ loaded: 4 }]);
  assert.deepEqual(shown, [{ loaded: 4 }]);
}

{
  const earlier = deferred();
  const later = deferred();
  const history = [];
  const shown = [];
  const feed = createProgressFeed({
    decode(packet) { return packet.order === 1 ? earlier.promise : later.promise; },
  });
  const workspace = createTransferWorkspace({
    transport() {}, onCancel() {}, record() {}, showQueued() {},
    recordProgress: item => history.push(item.frame.loaded),
    showProgress: item => shown.push(item.frame.loaded),
  });

  workspace.select({ id: "ordered", progressFeed: feed });
  feed.emit({ order: 1, loaded: 10 });
  feed.emit({ order: 2, loaded: 20 });
  later.resolve({ loaded: 20 });
  await Promise.resolve();
  earlier.resolve({ loaded: 10 });
  await Promise.resolve();

  assert.deepEqual(history, [20, 10]);
  assert.deepEqual(shown, [20]);
}

{
  const telemetry = [];
  const feed = createProgressFeed({ initialPacket: { loaded: 1 } });
  const stop = collectProgressTelemetry(feed, frame => telemetry.push(frame.loaded));
  feed.emit({ loaded: 2 });
  assert.deepEqual(telemetry, [2]);
  stop();
}

{
  const shown = [];
  let detachCount = 0;
  const feed = createProgressFeed({
    initialPacket: { loaded: 3 },
    onDetach() { detachCount++; },
  });
  const workspace = createTransferWorkspace({
    transport() {}, onCancel() {}, record() {}, showQueued() {},
    showProgress: item => shown.push(item.frame.loaded),
  });
  const file = { id: "reused", progressFeed: feed };

  workspace.select(file);
  workspace.hide();
  workspace.select(file);
  assert.deepEqual(shown, [3, 3]);
  assert.equal(detachCount, 1);
}
