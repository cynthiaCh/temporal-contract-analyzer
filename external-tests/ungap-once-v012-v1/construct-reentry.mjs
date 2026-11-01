// Supplemental researcher probe; the original seven checks stay unchanged.
import assert from 'node:assert/strict';
import {pathToFileURL} from 'node:url';
delete Function.prototype.once;
await import(pathToFileURL(process.argv[2]).href);
let calls = 0;
let Wrapped;
class Item {
  constructor() {
    calls++;
    if (calls === 1) new Wrapped();
  }
}
Wrapped = Item.once();
const item = new Wrapped();
console.log(JSON.stringify({constructorCalls: calls, itemIsItem: item instanceof Item}));
assert.equal(calls, 1, 'synchronous constructor reentry must not construct twice');
