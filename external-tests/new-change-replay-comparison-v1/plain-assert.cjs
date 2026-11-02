const assert = require('node:assert/strict');
const path = require('node:path');
const subject = path.resolve(process.argv[2]);
const EventEmitter = require(subject);
const emitter = new EventEmitter();
let count = 0;
let reentered = false;
const trace = [];
emitter.once('probe', () => {
  count++;
  const source = new Error().stack.split('\n').find(line => line.includes(subject));
  trace.push({count, source: source?.trim() || null});
  if (!reentered) {
    reentered = true;
    emitter.emit('probe');
  }
});
emitter.emit('probe');
console.log(JSON.stringify({requirement: 'once_delivery', scenario: 'one nested emit', count, trace}));
assert.equal(count, 1, 'A once listener must execute exactly once across outer and nested emit');
