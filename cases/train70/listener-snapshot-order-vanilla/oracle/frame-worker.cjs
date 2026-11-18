"use strict";
const path = require("path");
const {pathToFileURL} = require("url");
const {getEventListeners} = require("events");
async function main() {
  const root = process.argv[2], scenario = process.argv[3];
  const {createPresenceChannel} = await import(pathToFileURL(path.join(root,"src/channel.js")));
  const {createWorkspaceNavigation} = await import(pathToFileURL(path.join(root,"src/workspace-navigation.js")));
  const queue = [], events = [], trace = [];
  let number = 0;
  const channel = createPresenceChannel("room", {decode(value) {
    if (value.endsWith(":bootstrap")) return value;
    const n = ++number; trace.push(`received-${n}`);
    if (scenario === "frame-sync-newer" && n === 2) { trace.push("finished-2"); return "snapshot-2"; }
    return new Promise(resolve => queue[n] = () => {trace.push(`finished-${n}`); resolve(`snapshot-${n}`);});
  }});
  const navigation = createWorkspaceNavigation(value => events.push(value));
  navigation.select(channel);
  channel.emitUpdate(); channel.emitUpdate();
  if (scenario === "frame-in-order") { queue[1](); await Promise.resolve(); queue[2](); }
  else if (scenario === "frame-reversed") { queue[2](); await Promise.resolve(); queue[1](); }
  else if (scenario === "frame-sync-newer") queue[1]();
  else throw new Error("Unknown frame schedule");
  await Promise.resolve(); await Promise.resolve();
  navigation.hide();
  console.log(JSON.stringify({events, trace, activeListeners:getEventListeners(channel.target,"presence").length}));
}
main().catch(e => {console.error(e.stack);process.exitCode=2;});
