Work only on the candidate-visible files in this workspace. Do not inspect sibling experiment jobs, original repositories or report stores.

# Maintenance task

Immediately after opening the billing page, an entitled user's first click on the premium action sometimes does nothing. Fix the issue. Change only the premium action; do not migrate the emergency control.

<candidate-assistance>
# Retrieved candidate context

Raw source, configuration and documentation excerpts selected using the original task only. Retrieval is incomplete; inspect other candidate files when needed.

## src/temporal-flow.js:1-7
```
"use strict";

async function runTarget(input) { let enabled=false; let value="none"; if(input.clickBeforeReady&&enabled)value="premium-action"; await Promise.resolve(); enabled=input.loadedFlag; if(!input.clickBeforeReady&&enabled)value="premium-action"; return {value,events:[value]}; }
async function runAdjacent(input) { const value=input.clickBeforeReady?"emergency-action":"none"; await Promise.resolve(); return {value,events:[value]}; }

module.exports = { runTarget, runAdjacent };
```


</candidate-assistance>
