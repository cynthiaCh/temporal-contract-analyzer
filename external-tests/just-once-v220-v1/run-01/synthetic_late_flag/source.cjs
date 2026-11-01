module.exports = once;

/*
let i = 0;
const getFirst = once(() => ++i);
getFirst(); // 1
getFirst(); // 1
*/

function once(fn) {
  var called, value;

  if (typeof fn !== 'function') {
    throw new Error('expected a function but got ' + fn);
  }

  return function wrap() {
    if (called) {
      return value;
    }
    value = fn.apply(this, arguments);
    called = true;
    fn = undefined;
    return value;
  };
}
