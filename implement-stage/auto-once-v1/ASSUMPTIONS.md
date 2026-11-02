# Assumption ledger

ASK=never. Sources below are explicit defaults, not user-confirmed scientific findings.

| ID | Decision | Chosen | Class | Source |
| --- | --- | --- | --- | --- |
| A1 | First supported API | Single-file CommonJS factory with one identifier parameter, returning a local callable that syntactically invokes that parameter directly or through call/apply. No alias inference, reexports, ESM or emitter binding in this increment. | interface | default |
| A2 | What is inferred | API candidate only; no once semantics inferred from names or guards. Require --confirm-at-most-once to execute; unconfirmed mode parses source text only. | semantic | default |
| A3 | Requirement/domain | At most one callback entry during an outer invocation and a synchronous nested invocation attempted on the first callback entry; no entry means no reentry, with no liveness guarantee. Numeric argument 0. Construction-time callback entries invalidate the scene as inconclusive. No promise/exception-retry guarantee. | semantic | sweep |
| A4 | Experiment meaning | Fresh-repository migration after synthetic development; informed implementer, no blind discovery or human-effort claim. Report supported and unsupported selections without adjusting code for them. | semantic | default |
| A5 | Baseline | The generated binding is also passed to existing independent fast-check. Any binding savings belong to this frontend, not a stronger test generator. Compare model coverage separately. | semantic | default |
| A6 | Runtime preparation | Root is each supplied file's parent, entry is its basename, module commonjs; missing dependencies become inconclusive, no installation or source rewrite. Existing pinned Babel dependency is reused. | interface | default |
| A7 | Refusal | Both versions must match the same narrow shape. Structural match does not prove runtime export behavior; setup errors remain inconclusive. No result is called safe. | semantic | default |
| A8 | Recognition strength | Returned-callable candidates are syntactic, not control-flow or complete lexical-binding proofs. At least one returned callable subtree contains a matching callback call; other callable paths may not execute it. | interface | sweep |
| A9 | Prepared environment | Existing probe copies the parent subtree excluding node_modules and overwrites the copy's package.json with CommonJS metadata; no dependency roots are supplied. This can differ from the operator's working repository. | interface | sweep |
| A10 | Status/exit meaning | observed means usable observations, including invocation throws or violations. Zero callbacks satisfy at-most-once without exercising reentry. CLI 0 means artifact emitted (also confirmation_required/inconclusive), 2 means unsupported; neither is a pass/fail verdict. Read status, checks and execution_validity. | semantic | sweep |
| A11 | Replay | Rerun recipe against current absolute paths, current implementation and runtime, assuming unchanged inputs and an unused output path. It does not bundle snapshots or verify immutable content. External experiment separately retains source snapshots and frozen versions. | interface | sweep |
| A12 | Nested argument convention | Numeric argument 0 refers to the outer call. The nested call receives the first argument actually delivered to the callback, which may be transformed or omitted by the wrapper. A callback argument change may therefore change the nested input. The existing runner implements this convention; no same-argument guarantee is made. | semantic | sweep |
