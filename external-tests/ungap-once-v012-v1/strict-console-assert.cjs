// Test-only adapter: upstream console.assert failures must fail the subprocess.
const assert = require('node:assert/strict');
const fs = require('node:fs');
let count = 0;
console.assert = (condition, ...message) => {
  count++;
  assert.ok(condition, message.join(' '));
};
process.on('exit', code => fs.writeFileSync(process.env.TCA_NATIVE_RESULT,
  JSON.stringify({assertions: count, exitCode: code}, null, 2) + '\n'));
