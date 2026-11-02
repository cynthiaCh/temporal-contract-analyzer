'use strict';
// Post-hoc confirmation only: never used as generator input or campaign oracle.
const path = require('path');
const base = path.resolve(__dirname, '../unseen-small-implementations-v1/snapshots');
function observe(Emitter) {
  const emitter = new Emitter();
  const counts = {first: 0, second: 0};
  emitter.once('probe', () => {
    if (++counts.first === 1) emitter.emit('probe');
  });
  emitter.once('probe', () => counts.second++);
  emitter.emit('probe');
  return counts;
}
process.stdout.write(JSON.stringify({
  before: observe(require(path.join(base, 'eventemitter3-before/index.js'))),
  historical_fix: observe(require(path.join(base, 'eventemitter3-fixed/index.js'))),
  native_node_reference: observe(require('node:events').EventEmitter)
}, null, 2) + '\n');
