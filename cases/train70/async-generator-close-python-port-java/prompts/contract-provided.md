Additional behavioral contract:

first_match owns the supplied async generator and closes it before returning or raising on match, exhaustion, predicate failure, or cancellation. Cleanup may suspend. Preserve the selected row, absence result, original error, and cancellation.

Port mapping: native async cursor ports next/close correspond to supplied asynchronous generator operations; callback completion or native Future acknowledgment corresponds to return/raise. PHP/Ruby/Go explicit cursor callbacks replace language-native async-generator syntax, without claiming an identical built-in generator type. Framework ports use real JS async generators and mounted framework consumers.
