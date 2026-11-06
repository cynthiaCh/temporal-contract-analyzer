# Retrieved candidate context

Raw source, configuration and documentation excerpts selected using the original task only. Retrieval is incomplete; inspect other candidate files when needed.

## src/temporal-flow.js:1-7
```
"use strict";

async function runTarget(input) { let enabled=false; let value="none"; if(input.clickBeforeReady&&enabled)value="premium-action"; await Promise.resolve(); enabled=input.loadedFlag; if(!input.clickBeforeReady&&enabled)value="premium-action"; return {value,events:[value]}; }
async function runAdjacent(input) { const value=input.clickBeforeReady?"emergency-action":"none"; await Promise.resolve(); return {value,events:[value]}; }

module.exports = { runTarget, runAdjacent };
```

