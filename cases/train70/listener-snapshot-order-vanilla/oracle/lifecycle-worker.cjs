"use strict";
const path = require("path");
const { getEventListeners } = require("events");
const { pathToFileURL } = require("url");
const root = process.argv[2];
const scenario = process.argv[3];
async function main() {
  const { createPresenceChannel } = await import(pathToFileURL(path.join(root, "src/channel.js")));
  const { createWorkspaceNavigation } = await import(pathToFileURL(path.join(root, "src/workspace-navigation.js")));
  const events = [];
  const queued = [];
  const tracked = [];
  function channel(token, delayed = false) {
    const channel = createPresenceChannel(token, { decode(value) {
      if (delayed && value.endsWith(":update")) return new Promise(resolve => queued.push(() => resolve(value)));
      return value;
    }});
    tracked.push(channel.target);
    return channel;
  }
  const a = channel("room-a", true);
  const b = channel("room-b");
  let once = false;
  const navigation = createWorkspaceNavigation((value, nav) => {
    events.push(value);
    if (value === "room-a:bootstrap" && !once) {
      once = true;
      if (scenario === "nested-switch") nav.select(b);
      if (scenario === "nested-close") nav.hide();
    }
  });
  if (scenario.startsWith("nested-")) {
    navigation.select(a);
    a.emitUpdate();
    b.emitUpdate();
    queued.splice(0).forEach(resolve => resolve());
    await Promise.resolve();
  } else {
    navigation.select(a, "deferred");
    await Promise.resolve();
    a.emitUpdate(); // Start decoding in visit 1, then change its owner/lifetime.
    if (scenario === "decode-after-switch") navigation.select(b);
    else if (scenario === "decode-after-close") navigation.hide();
    else if (scenario === "same-channel-reopen") { navigation.hide(); navigation.select(a); }
    else throw new Error("unknown lifecycle schedule");
    queued.splice(0).forEach(resolve => resolve());
    await Promise.resolve();
    if (scenario === "decode-after-switch") b.emitUpdate();
    if (scenario === "same-channel-reopen") { a.emitUpdate(); queued.splice(0).forEach(resolve => resolve()); await Promise.resolve(); }
  }
  navigation.hide();
  const activeListeners = tracked.reduce((count, target) => count + getEventListeners(target, "presence").length, 0);
  // After hide, neither transport is allowed to produce another publication.
  a.emitUpdate(); b.emitUpdate(); queued.splice(0).forEach(resolve => resolve());
  await Promise.resolve();
  process.stdout.write(JSON.stringify({ scenario, events, activeListeners }));
}
main().catch(error => { process.stderr.write(`${error.stack}\n`); process.exitCode = 2; });
