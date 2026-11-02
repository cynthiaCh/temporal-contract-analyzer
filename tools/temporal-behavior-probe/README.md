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
