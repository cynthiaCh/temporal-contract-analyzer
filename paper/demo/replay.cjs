'use strict';
// Executes only the paper's explicitly synthetic examples, not scan targets.
const assert = require('node:assert/strict');
async function replay(variant) {
  const {createPanel} = require(`./${variant}/panel.cjs`);
  let complete;
  const pending = new Promise(resolve => { complete = resolve; });
  const trace = [], outputs = [];
  const panel = createPanel(() => pending, value => {
    trace.push('publish'); outputs.push(value);
  });
  trace.push('refresh'); const work = panel.refresh();
  trace.push('close'); panel.close();
  trace.push('resolve'); complete('old result');
  await work; trace.push('refresh completed');
  return {variant, schedule: 'refresh -> close -> resolve -> continuation', trace, outputs};
}
(async () => {
  const records = await Promise.all(['unguarded', 'guarded'].map(replay));
  assert.deepEqual(records[0].outputs, ['old result']);
  assert.deepEqual(records[1].outputs, []);
  console.log(JSON.stringify({kind:'synthetic-demonstration',records}, null, 2));
})().catch(error => { console.error(error); process.exitCode = 1; });
