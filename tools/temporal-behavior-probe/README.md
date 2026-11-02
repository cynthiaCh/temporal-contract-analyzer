# Temporal behavior probe — experimental prototype

Generate and run bounded callback scenarios against two explicitly supplied local modules. This CLI is separate from the frozen static analyzer. It accepts declarative API bindings and behavioral requirements, not repository-specific test-function bodies.

It supports three API shapes:

- `wrapper`: a factory receiving a callback and returning a callable. Shared scenes cover sequential calls, one synchronous reentry, exception/retry and two overlapping calls.
- `emitter`: a callable or constructor exposing configured on/off/emit methods and optionally once. Shared scenes vary listener count, reentry and removal of self/next listener.
- `keyed_completion`: registration `(key, callback)` returns the first request's completion function, or null for subsequent queued registrations. Scenes cover completion, callback failure and registration during delivery.

This is template/operation composition on known API shapes. It does not infer arbitrary APIs or natural-language contracts, synthesize new callback logic from source, or establish general effectiveness.

## Example

Save a JSON plan, resolving paths relative to that plan:

```json
{
  "api": {"kind": "emitter", "construct": true,
    "methods": {"on": "on", "off": "removeListener", "emit": "emit", "once": "once"}},
  "contracts": {"once_delivery": true},
  "before": {"root": "old", "entry": "index.js", "module": "commonjs"},
  "after": {"root": "new", "entry": "index.js", "module": "commonjs"}
}
```

Run from the repository root:

```sh
python3 tools/temporal-behavior-probe/probe.py /path/to/plan.json --output /path/to/new-report.json
```

Replay one reported scene with `--scenario once-reentry-2`. `--node` selects the runtime; the default is VS Code's embedded Node. The existing feasibility corpus uses Node v24.21.0. Outputs are exclusive-create JSON files.

## Meaning of requirements

Only explicitly enabled booleans are checked. A changed observation with no applicable requirement is `observation_only`.

| Requirement | Evaluated scenes and meaning |
| --- | --- |
| at_most_once | Wrapper scenes: total callback invocations at most one; does not promise liveness |
| repeat_rejected | Sequential/reentrant second invocation throws |
| cache_repeated | Two sequential identical calls share one callback evaluation and returned value |
| failure_rethrows | Inputs that make the supplied callback throw do not return a cached success; no requirement to cache or retry the exception |
| preserve_success_after_failure | A failing different argument does not replace the previous successful cached result |
| coalesce_pending | Two overlapping calls with a deferred callback result share one evaluation; direct synchronous reentry is separately observed, without an implied coalescing requirement |
| once_delivery | Once listeners are each delivered exactly once during the tested first/nested dispatch sequence |
| snapshot_delivery | Ordinary dispatch and self/next removal deliver each listener present at dispatch start |
| restart_after_failure | Keyed completion: after a callback throws, registration for that key can start again |
| queued_delivery | Keyed completion: ordinary queued callbacks and the callback registered during delivery are delivered |

The operator must confirm argument domain (numeric 0/1 and fixed string event/request keys), factory shape and these requirements from project evidence. These inputs carry semantic information; the generator is not discovering it.

## Execution and evidence

Each side/scene runs in a fresh process with a five-second timeout and a bounded callback trace. Input roots are copied into temporary directories. Declared dependency directories are copied into the isolated module-resolution tree. Optional `export` is an explicit namespace path such as `default.strict`. Legacy corpus inputs may declare the existing type-only Flow eraser; TS uses native erasure and extensionless-import symlinks. No package installation occurs.

The output includes scenario descriptions, callback counts, operation returns/throws, source call frames, contract checks and transitions. `<subject>` in source frames refers to that side's declared root. Setup errors, timeouts and trace-budget exhaustion are inconclusive. Temporary execution is **not a security sandbox**; only run trusted local code supplied for this purpose. Prototype encoders expect these examples' JSON-compatible callback inputs/results.

`resolved_for_generated_scene` means a particular before-version failure disappears in the after-version scene, not that the code is completely fixed. `violates_on_both` preserves residual failures. Passing the bounded checks never establishes safety.

The static analyzer neither calls this prototype nor executes candidate programs. Its existing no-execution guarantee is unchanged.

## Narrow automatic wrapper binding

`auto_once.py` proposes the existing wrapper profile from two local source files:

```sh
python3 tools/temporal-behavior-probe/auto_once.py before/index.js after/index.js \
  --output proposal.json
```

This mode reads source text through the repository's already pinned Babel parser and does not import the subject. Supported syntax is deliberately narrow: one direct top-level CommonJS function export, one identifier parameter, and a returned local callable containing a direct call/call/apply of that parameter. It does not prove runtime binding identity or infer once semantics. Reexports, ESM, emitters, unresolved callback aliases, async factories/callables and ambiguous exports are outside this increment. Missing parser setup produces an unsupported result.

After checking the proposed binding and requirement, explicitly confirm execution:

```sh
python3 tools/temporal-behavior-probe/auto_once.py before/index.js after/index.js \
  --confirm-at-most-once --output report.json
```

This checks only **at most one callback entry across one outer invocation and one synchronous reentry**, with numeric argument 0 and the existing runner's call convention. It does not establish liveness, exception-retry, promise behavior or safety outside that scene. A name such as `once` never supplies the obligation automatically. The report retains source evidence, generated `candidate_plan`, paired execution and a fresh-output `replay_command`. Unsupported source remains unexecuted even with the flag; loader failures are inconclusive. Output files are exclusive-create before any execution. `--node` selects the runtime.

The file's parent becomes its module root; its basename becomes the entry. Sibling local files are copied by the existing runner. External dependencies are neither inferred nor installed. The same generated plan is usable by other execution engines, including the independent fast-check baseline. The benefit being attempted is reduced manual binding work, not stronger counterexample generation. Selecting this specialized command already conveys domain knowledge; fewer JSON fields alone do not demonstrate lower cognitive effort.

Execution validity is separate from the count predicate. If the factory calls the supplied callback during construction, the inherited runner's reentry trigger can fire before the returned callable exists; this frontend marks that side and pair inconclusive and clears the in-scope checks. `execution_validity` also records whether a nested attempt actually occurred. Zero callback entries satisfy at-most-once without exercising reentry, so they do not demonstrate delivery or a reentrant path. `observed` means observations are available, including throws or violations. CLI exit 0 means a report was emitted (including confirmation-required or inconclusive); inspect the report for the behavioral verdict. Unsupported inputs exit 2.

The copied runtime excludes node_modules and replaces package.json in the copy with CommonJS metadata. Therefore it can differ from an already configured working repository. The replay command reruns against current source paths, implementation and runtime and needs an unused output file; it is not a bundled immutable reproduction. Keep those inputs unchanged or archive them separately.

The numeric argument 0 in the scope description is the **outer** input. The nested attempt passes the first argument actually received by the callback; if the wrapper transforms or omits that value, the nested input changes accordingly. Same-argument preservation is not assumed.
