// Independent bounded runtime check, not imported by either engine.
const assert = require('node:assert/strict');
const path = require('node:path');
const subject = path.resolve(process.argv[2]);
let factory, wrapped, count = 0, nested = false;
try { factory = require(subject); }
catch (error) { console.log(JSON.stringify({status: 'setup_error', error: String(error)})); process.exit(2); }
try {
  wrapped = factory(() => {
    count++;
    if (!nested) { nested = true; wrapped(0); }
    return 42;
  });
  wrapped(0);
  assert.equal(count, 1);
  console.log(JSON.stringify({status: 'observed', count, passed: true}));
} catch (error) {
  console.log(JSON.stringify({status: error.name === 'AssertionError' ? 'observed' : 'runtime_error',
    count, passed: false, error: String(error)}));
  process.exitCode = 1;
}
