Looking up an early matching record can leave the stream resource occupied. Repair first_match(records, predicate) in src/search.js while preserving scan order and error behavior.

Keep the documented public interfaces and unrelated behavior. Use the existing JavaScript runtime and pinned framework dependencies.
