async function runTarget(input) { const events=["ack"]; await Promise.resolve(); if(!input.commitSucceeds) events.push("error"); return {value:events[events.length-1],events}; }
async function runAdjacent() { await Promise.resolve(); return {value:"accepted",events:["accepted"]}; }

export { runTarget, runAdjacent };

