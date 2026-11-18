"use strict";
const path = require("path");
const { pathToFileURL } = require("url");
const candidate = path.resolve(process.argv[2] || "");
const schedule = process.argv[3];
const baseline = process.argv[4] === "baseline";
let now = 0, serial = 0;
const pending = new Map(), writes = [], statuses = [], documents = [], previews = [], assertions = [];
let visible = null, runtimeError = null, previewDelay = null;
const equal = (a, b) => require("util").isDeepStrictEqual(a, b);
const check = (id, actual, expected) => assertions.push({ id, passed: equal(actual, expected), actual, expected });
const timers = {
  schedule(callback, delay) { const id = ++serial; pending.set(id, { callback, at: now + delay }); return id; },
  cancel(id) { pending.delete(id); },
};
function advance(target) {
  let steps = 0;
  while (true) {
    const next = [...pending.entries()].filter(([, item]) => item.at <= target).sort((a,b) => a[1].at-b[1].at || a[0]-b[0])[0];
    if (!next) break;
    if (++steps > 100) throw new Error("timer did not quiesce");
    pending.delete(next[0]); now = next[1].at; next[1].callback();
  }
  now = target;
}
const pairs = () => writes.map(({id,text}) => [id,text]);
const statusPairs = () => statuses.map(({id,text}) => [id,text]);
async function main() {
  const load = async relative => import(pathToFileURL(path.join(candidate, relative)).href);
  const { createDraftStore } = await load("src/draft-store.js");
  const { createWorkspace } = await load("src/workspace.js");
  const { createSearchPreview } = await load("src/search-preview.js");
  const actualStore = createDraftStore({A:"seed-A",B:"seed-B"});
  const store = {
    read: id => actualStore.read(id), subscribe: fn => actualStore.subscribe(fn),
    write(id,text) { writes.push({id,text,time:now}); return actualStore.write(id,text); },
  };
  const workspace = createWorkspace({store,timers,
    renderDocument(value) { visible = value === null ? null : {...value}; documents.push({time:now,value:visible}); },
    renderStatus(event) { statuses.push({time:now,...event}); },
  });
  const preview = createSearchPreview({timers,publish(value){previews.push({time:now,...value});}});
  const finish = (expectedWrites, expectedStatuses) => {
    advance(600);
    check("exact-writes-after-quiescence", pairs(), expectedWrites);
    check("exact-save-statuses", statusPairs(), expectedStatuses);
    check("no-pending-timers", pending.size, 0);
  };
  switch (schedule) {
    case "quiet-burst": {
      workspace.open("A"); workspace.edit("alpha"); advance(30); workspace.edit("beta"); advance(80); workspace.edit("gamma");
      advance(199); check("no-early-save", pairs(), baseline ? [["A","alpha"],["A","beta"],["A","gamma"]] : []);
      advance(200); const expected = baseline ? [["A","alpha"],["A","beta"],["A","gamma"]] : [["A","gamma"]];
      check("save-at-deadline", pairs(), expected); finish(expected, expected); break;
    }
    case "second-burst": {
      workspace.open("A"); workspace.edit("one"); advance(120); workspace.edit("two"); advance(150); workspace.edit("three"); advance(270);
      const expected = baseline ? [["A","one"],["A","two"],["A","three"]] : [["A","one"],["A","three"]];
      finish(expected, expected); break;
    }
    case "close-before-deadline": {
      workspace.open("A"); workspace.edit("leaving-A"); advance(20); workspace.close();
      check("saved-before-return", store.read("A"), "leaving-A"); check("closed", visible, null);
      finish([["A","leaving-A"]], baseline ? [["A","leaving-A"]] : []); break;
    }
    case "switch-before-deadline": {
      workspace.open("A"); workspace.edit("owned-by-A"); advance(20); workspace.open("B");
      check("A-preserved", store.read("A"), "owned-by-A"); check("B-not-retargeted", store.read("B"), "seed-B");
      workspace.edit("owned-by-B"); advance(140);
      finish([["A","owned-by-A"],["B","owned-by-B"]], baseline ? [["A","owned-by-A"],["B","owned-by-B"]] : [["B","owned-by-B"]]); break;
    }
    case "same-document-reopen": {
      workspace.open("A"); workspace.edit("first-visit"); advance(20); workspace.close(); workspace.open("A");
      check("restored", visible, {id:"A",text:"first-visit"}); workspace.edit("second-visit"); advance(40); workspace.close();
      finish([["A","first-visit"],["A","second-visit"]], baseline ? [["A","first-visit"],["A","second-visit"]] : []); break;
    }
    case "preview-delay": {
      preview.query("latest"); advance(40); const at40 = previews.map(x=>x.query); advance(120);
      const observed = previews.map(({time,query})=>[time,query]);
      previewDelay = equal(observed, [[40,"latest"]]) ? 40 : equal(observed, [[120,"latest"]]) ? 120 : null;
      check("recognized-policy", previewDelay === 40 || previewDelay === 120, true); check("at-most-once", previews.length, 1); break;
    }
    case "preview-hide": {
      preview.query("discard-me"); advance(10); preview.hide(); advance(600); check("hidden-never-publishes", previews, []); break;
    }
    case "preview-reuse": {
      preview.query("old"); advance(10); preview.hide(); advance(20); preview.query("new"); advance(140);
      const observed = previews.map(({time,query})=>[time,query]);
      previewDelay = equal(observed, [[60,"new"]]) ? 40 : equal(observed, [[140,"new"]]) ? 120 : null;
      check("only-new-query", previewDelay === 40 || previewDelay === 120, true); check("exactly-once", previews.length, 1); break;
    }
    default: throw new Error(`unknown schedule: ${schedule}`);
  }
  check("schedule-quiescent", pending.size, 0);
  workspace.dispose();
}
main().catch(error => { runtimeError = String(error.stack || error); }).finally(() => {
  process.stdout.write(JSON.stringify({schedule,baseline,passed:runtimeError===null&&assertions.length>0&&assertions.every(x=>x.passed),runtimeError,assertions,writes,statuses,documents,previews,previewDelay,pendingTimers:pending.size})+"\n");
});
