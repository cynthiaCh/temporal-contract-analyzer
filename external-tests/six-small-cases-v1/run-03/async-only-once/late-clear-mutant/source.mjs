export default function onlyOnce(fn) {
    return function (...args) {
        if (fn === null) throw new Error("Callback was already called.");
        var callFn = fn;
        callFn.apply(this, args);
        fn = null;
    };
}
