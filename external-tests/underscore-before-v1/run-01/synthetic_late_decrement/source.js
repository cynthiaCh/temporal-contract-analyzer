// Returns a function that will only be executed up to (but not including) the
// Nth call.
export default function before(times, func) {
  var memo;
  return function() {
    if (times > 1) {
      memo = func.apply(this, arguments);
    }
    --times;
    if (times <= 1) func = null;
    return memo;
  };
}
