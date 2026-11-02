// @flow
                                                  

const simpleIsEqual             = (a       , b       )          => a === b;

// <ResultFn: (...Array<any>) => mixed>
// The purpose of this typing is to ensure that the returned memoized
// function has the same type as the provided function (`resultFn`).
// ResultFn:        Generic type (which is the same as the resultFn).
// (...Array<any>): Accepts any length of arguments - and they are not checked
// mixed:           The result can be anything but needs to be checked before usage
export default function                                     (resultFn          , isEqual              = simpleIsEqual)           {
  let lastThis       ;
  let lastArgs               = [];
  let lastResult       ;
  let calledOnce          = false;

  const isNewArgEqualToLast = (newArg       , index        )          => isEqual(newArg, lastArgs[index]);

  // breaking cache when context (this) or arguments change
  const result = function (...newArgs              ) {
    if (calledOnce &&
      lastThis === this &&
      newArgs.length === lastArgs.length &&
      newArgs.every(isNewArgEqualToLast)) {
      return lastResult;
    }

    calledOnce = true;
    lastThis = this;
    lastArgs = newArgs;
    lastResult = resultFn.apply(this, newArgs);
    return lastResult;
  };

  // telling flow to ignore the type of `result` as we know it is `ResultFn`
  return (result     );
}