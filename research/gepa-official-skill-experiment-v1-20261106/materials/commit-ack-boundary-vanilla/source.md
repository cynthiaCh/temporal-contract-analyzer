# Retrieved candidate context

Raw source, configuration and documentation excerpts selected using the original task only. Retrieval is incomplete; inspect other candidate files when needed.

## package.json:1-7
```
{
  "name": "commit-ack-boundary-vanilla-fixture",
  "version": "0.1.0",
  "private": true,
  "type": "module"
}
```

## src/temporal-flow.js:1-5
```
async function runTarget(input) { const events=["ack"]; await Promise.resolve(); if(!input.commitSucceeds) events.push("error"); return {value:events[events.length-1],events}; }
async function runAdjacent() { await Promise.resolve(); return {value:"accepted",events:["accepted"]}; }

export { runTarget, runAdjacent };
```

