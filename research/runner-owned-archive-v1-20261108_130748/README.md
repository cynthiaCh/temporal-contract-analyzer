# Runner-owned research archives v1

This directory is a new research implementation, not an executed experiment. Historical frozen scripts, prompts, traces and results are unchanged. Start with [REPORT.md](REPORT.md), [offline-validation.json](offline-validation.json) and [history-audit.json](history-audit.json).

The session lifecycle is adapted from `research/transfer-reflection-crosslang-20261108_202000/runner.py`, with the earlier `contract-repair-small-v1-20261108/runner.py` inspected as its source lineage. No historical dispatcher is imported or executed. Source hashes and function reuse are in [provenance.json](provenance.json).

## Responsibilities and files

- `runner.py`: one existing autonomous session lifecycle, original role models/efforts/request caps, process-group timeout, always-attempted archival, trusted external evaluation handoff. No scheduler or retry. Native model execution is disabled by default; a future explicitly authorized protocol must opt in and provide frozen file hashes.
- `archive.py`: freeze input, create isolated workspace, preserve final snapshot, generate `patch.diff`, collect event/tool output/answer/usage, record errors and provenance of extra files. No LLM calls.
- `prompts.py`: replace only the known mechanical archival clause, identically for both arms; append raw experience unchanged after shared instructions.
- `native_backend.py`: reused CLI namespace and flags; host output/meter archive directories are no longer mounted. Final answer comes from completed JSON event output, rather than an actor-accessible host output directory.
- `guard_server.py` / `guard_client.py`: local Unix-socket event relay to the unchanged host-side `request_guard.account`. This is bookkeeping transport, not a reasoning controller. No shell keyword blacklist is added. `request_guard.py` and `read_policy.py` are byte-identical copies.

## Session layout and lifecycle

```text
run/
  workspace/                      # only writable business tree mounted at /workspace
  archive/                        # not mounted or accessible inside actor namespace
    input/original/               # complete original candidate snapshot
    input/task.md
    input/actual-prompt.md
    input/config.json
    input/frozen-start.json
    events.jsonl                  # streamed stdout, including tool output
    stderr.log
    meter/                        # host-owned real hook ledger
    final-candidate/              # copied only after actor process stops
    final-manifest.json
    patch.diff
    diff-result.json
    diff.stderr
    nontext-changes.json
    file-changes.json             # all additions/deletions, event provenance where available
    tool-outputs.jsonl
    collection.json
    raw-answer.txt                # missing explicitly marked; partial answer separate
    usage.json                    # missing usage remains unknown
    model-outcome.json            # model/process cause separate from archive errors
    archive-status.json
    receipt.json
    score/                        # only when caller explicitly supplies trusted scorer
    ARTIFACTS.sha256
```

Before launch, Python freezes the original candidate, task, exact prompt and configuration, then copies a separate writable workspace. Input version assertions precede native launch. During execution Python writes events/stderr directly outside the namespace; hooks synchronously relay events to the same accounting guard and host ledger. The actor sees only the business workspace, standard runtime, schemas, isolated CLI profile and local hook endpoint, not snapshots/logs/archive/meter directories. Authentication and temporary profile live outside Git and are removed after stopping.

After process stop, `finally` attempts final copy and diff even for timeout, abnormal exit, missing CLI or missing final answer. GNU diff is reused; regular file hunks use `a/` / `b/` and `/dev/null` labels for additions/deletions. Return codes 0/1 are normal; others and unavailable executable are errors, never empty-success. Full snapshots and manifests retain binary bytes, symlinks, empty-file/type/mode changes even when a text patch cannot encode them. Do not treat text diff alone as the complete filesystem snapshot.

Any added workspace entry is preserved, including legitimate `.patch` files or directories named `backup`. No filename-based cleanup is performed. Explicit file-change events provide provenance when available; unproven origins remain unclassified and all entries remain in scorer input. Python cleans only its own external temporary profile, not candidate files.

`receipt.archive_failure_requires_stop` must stop the caller's experiment on archival error. It is separate from model `failure_class`, `stop_reason`, exit code and resource-limit evidence, which are retained. No model is asked to fix archives. No automatic retry occurs.

## Future integration boundary (no execution authorized by this artifact)

A new protocol can import `session(...)` and `build_prompt(...)` for both AUTO and AUTO_EXP. It must freeze this implementation and its inputs, use fresh run directories, preserve its own stage gates/total budget and supply its existing trusted scorer explicitly as `score_fn(final_candidate, score_dir)`. Keep the original task/Contract/experience/model/effort/output rules and official evaluator checks. The callback receives the copied final candidate, never an independently reconstructed or model-authored patch. The runner verifies the candidate digest before/after evaluation and preserves any mutation as an evaluation error rather than silently reverting it. With no callback, scoring is `NOT_REQUESTED`.

Do not point this implementation at old run directories, patch old frozen prompts, resume historical scheduling, or infer acceptance of the old rejected experience. `adapted-prompts/` contains only offline equivalence examples, not new approved experiments.

## Offline verification

```sh
python3 -B research/runner-owned-archive-v1-20261108_130748/test_offline.py
```

The test suite uses tiny temporary candidates, local fake processes/events, a local namespace prefix without Codex, and an existing fake score copied by a callback. It invokes no model, maintenance agent or case scorer. Results/log are versioned alongside the code. Future performance effects require a fresh comparison using the same new runner version in both groups.
