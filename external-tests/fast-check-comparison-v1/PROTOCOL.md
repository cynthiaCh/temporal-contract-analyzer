# fast-check comparison protocol

Question: does the existing prototype offer an advantage over directly using a testing framework for obtaining, locating and understanding before/after temporal counterexamples?

This is a local development comparison, not a human study, independent hold-out evaluation, or formal novelty claim. Reuse all 10 plans (7 implementations, five real fix pairs and five control configurations) from behavior-probe-feasibility-v1/run-02. The static analyzer and prototype remain unchanged.

## Design fixed before baseline execution

- A direct fast-check baseline receives exactly the same declarative API bindings, contracts, source modules and runtime preparation. It does not import the prototype's scenario generator, executor or evaluator. Independently implement reusable property models for the three API shapes, rather than writing project-specific tests or intentionally giving the baseline weak ordinary-only scenarios.
- Use the latest stable fast-check version resolved once from the public npm registry and record its exact version and distribution integrity. Copy test-only published dependencies into this study, without npm install or changes to tool package dependencies.
- Three fixed seeds (17, 42, 2027); 100 runs per enabled property; shrinking enabled. Emitter listener counts 1..4, wrapper repetition/failure counts bounded 2..4, and one reentry. This is a bounded, property-informed search; not arbitrary code synthesis. The baseline may find more than the prototype's fixed 57 scenes. Do not compare wall time as though coverage and isolation costs were equal.
- Use a fresh module instance per property trial (CJS cache reset or unique ESM import URL) and fresh callback/emitter state. Cases execute in fresh processes per side/seed. Capture raw failures and infrastructure failures separately. Declared source values and contract meanings follow the documented profiles.
- Preserve native fast-check failure output (seed, path, shrunk input, assertion stack) and an instrumented baseline with callback counts/source frames. Do not hide information the baseline can easily provide.
- Replay the minimized before counterexample on both versions, and also search each version independently. A residual after-version failure must not hide improvement for a particular shared counterexample.
- Compare ability to obtain the known counterexample, replay it and associate callback execution with source frames. Count common model/engine code and per-project binding effort separately. No developer time, ease-of-understanding or causal productivity claim without user evidence. Identical passing controls do not establish general false-positive rates.

Existing prototype results and independent historical runtime labels are evaluation references only, never inputs to the fast-check property generator or predicate. Both approaches have manually authored domain knowledge; account for this instead of counting only the prototype's JSON configuration lines.
