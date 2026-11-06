async function runTarget(input) { await Promise.resolve(); const events=[input.commitSucceeds ? "ack" : "error"]; return {value:events[0],events}; }
async function runAdjacent() { await Promise.resolve(); return {value:"accepted",events:["accepted"]}; }

export { runTarget, runAdjacent };

