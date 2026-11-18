Implement the following maintenance request in the provided repository. Preserve existing supported behavior. Keep dependency versions and build/test configuration unchanged. You may inspect the repository, edit product code, add tests, and run local commands. Evaluation applies trusted tests in a separate workspace after you finish. Do not consult external issues, pull requests, or reference solutions.

Add a public `clear(): void` operation to `AsyncSubject` so callers can discard a buffered result that is no longer needed, without discarding the subject or its subscribers.

While the subject is active, clear must remove its buffered value without emitting a notification or completing the subject. Calling it when no value is buffered, or calling it repeatedly, is harmless. A later next call can establish a new buffered value, including undefined. Clear must have no effect on a completed, errored, or unsubscribed subject. Preserve the current behavior of next, error, complete, and subscribe, and keep each instance independent.

The pinned runtime and dependencies are prepared. From the candidate workspace root, run the existing local checks in rxjs/. The subshell preserves the workspace root as the working directory for subsequent commands:
```sh
(
  cd rxjs &&
  node node_modules/typescript/bin/tsc -b --force src/tsconfig.cjs.json src/tsconfig.cjs.spec.json spec/tsconfig.json &&
  node node_modules/mocha/bin/mocha --config spec/support/.mocharc.js dist/spec/subjects/AsyncSubject-spec.js dist/spec/Subject-spec.js dist/spec/subjects/BehaviorSubject-spec.js dist/spec/subjects/ReplaySubject-spec.js
)
```

Synthetic native buffer binding port: product source is under rxjs/ with unchanged build/dependency configuration. Actual native buffer source and host consumer are under src/. Preserve the full declared upstream API and regression behavior.
