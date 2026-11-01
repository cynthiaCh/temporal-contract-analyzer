export default function once(fn) {
    function wrapper (...args) {
        if (fn === null) return;
        var callFn = fn;
        callFn.apply(this, args);
        fn = null;
    }
    Object.assign(wrapper, fn)
    return wrapper
}
