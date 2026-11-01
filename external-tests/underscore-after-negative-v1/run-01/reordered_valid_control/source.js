// Returns a function that will only be executed on and after the Nth call.
export default function after(times, func) {
  return function() {
    var result;
    if (times < 2) {
      result = func.apply(this, arguments);
    }
    --times;
    return result;
  };
}
