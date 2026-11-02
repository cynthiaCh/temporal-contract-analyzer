# Callback-change review evidence pilot

The probe supplies reproducible evidence about bounded callback requirements. This pilot **does not show that its evidence improves LLM review accuracy**: code-only, raw-evidence and indexed-evidence conditions all reached the same ceiling.

## Measured result

Three previously inspected historical source pairs (eventemitter3, p-memoize, memoize-one), each reviewed in both directions, yield six correlated tasks. Each condition received two fresh prompt-only completions, with task ordering reversed in the second repeat. Requested model: `gpt-6.1-sol`, low reasoning effort. All six calls succeeded, and event logs contain no tool executions. This is a model-based proxy, not a developer study.

| Input | Correct pair of decisions | Exact observable witness | Relevant witness and valid references | All criteria |
| --- | --- | --- | --- | --- |
| A: numbered sources, diff, explicit contract/scenarios, sequential smoke | 12/12 | 12/12 | 12/12 | 12/12 |
| B: A + native fast-check reports + paired execution observations | 12/12 | 12/12 | 12/12 | 12/12 |
| C: B + redundant observation/source index | 12/12 | 12/12 | 12/12 | 12/12 |

The two decisions are deliberately separate: **does the change introduce a new violation?** and **does any violation remain after the change?** References are checked for existence, not automatically accepted as causally sufficient. Manual inspection of all 36 short explanations found the expected causal orders: removal before/after reentry, pending-promise publication before/after suspension, and failing-key publication without exception replay. This inspection was performed by the implementing assistant, not an independent reviewer; it supplies no additional quantitative comprehension score.

Code-only answers correctly described their witnesses as source inferences. Evidence conditions described them as observations. The distinction is useful for auditability, but these results do not demonstrate better decisions, faster work, or better human understanding. B also contains native testing-framework evidence, so a future A→B gain would not establish a tool-specific advantage. There is no observed B→C gain here.

## Concrete evidence

Fresh executions reproduced all five supplied scenarios (ten before/after executions), matching the frozen observations exactly:

| Historical change, forward direction | Before | After | Bounded interpretation |
| --- | --- | --- | --- |
| eventemitter3, one once listener reenters | A executes twice | A executes once | This scenario is repaired |
| eventemitter3, A then B, A reenters | A twice, B twice | A once, B twice | A pre-existing violation remains |
| p-memoize, two overlapping equal calls | Underlying callback twice | Callback once | Sharing requirement repaired |
| memoize-one, first failing call then retry | Throws, then returns | Throws, then throws | Failure requirement repaired |
| memoize-one, success then failure then retry | Returns, throws, returns | Returns, throws, throws | Failure requirement repaired |

The eventemitter3 forward change is **not fully correct**: its two-listener case remains failing. Reversing it newly breaks the single-listener case. This is why reporting just “tests fail after” would give an incomplete review of the change. Callback frames identify invocation sites; causal explanations additionally require inspecting surrounding control flow. Historical Flow source uses the existing type-only eraser for execution.

Evidence locations:

- `run-01/REPLAY_VALIDATION.json` and `run-01/replay/*.json`: fresh raw executions, counts, returns/throws, source frames, requirement checks and transitions.
- `run-01/SCORES.json`: deterministic task-level scores.
- `run-01/r*-*/`: exact prompts, command/config provenance, raw events, answers, stderr, usage and transport status.
- `tasks/T01..T06/{A,B,C}.txt`: actual evidence packets; B includes all of A, C includes all of B. Gold labels are stored separately in `GOLD.json` and not included in the packets.
- `../unseen-small-implementations-v1/CASES.json`: historical commit and upstream-fix provenance.
- `PROTOCOL.md`: design frozen before task answers.

## Limits and decision

- These are seen development cases, with explicit requirements, API bindings and exact permitted scenarios supplied by us. This is neither automatic contract discovery nor a held-out bug-discovery evaluation.
- Forward/reverse tasks expose the same source pair within a completion; tasks and repeats are correlated. Source symbols remain recognizable and model training-data familiarity is uncontrolled.
- Passing only these finite scenes never establishes universal safety. Missing/inconclusive execution must not be called safe.
- No timing/effort comparison is claimed: prompt sizes differ, transport/cache conditions vary, and no developer worked through the tasks.
- Native fast-check already reproduced these issues and source frames in the previous comparison. This pilot establishes no detection, localization or evidence-indexing advantage over that baseline.
- Consequently this is evidence of a working, auditable bounded-check workflow, **not sufficient evidence for a claim of improved review effectiveness or an ICPC acceptance prediction**. The next useful evaluation would use independently selected unseen changes and actual review tasks. Do not expand this same pilot adaptively to manufacture a gain.

## Reproduction and validation

From the analyzer repository root:

```sh
python3 external-tests/review-evidence-pilot-v1/score.py
python3 -m unittest discover -s tests -p test_behavior_probe.py
```

The scoped probe suite passed 9/9. `verify.py` replays the five scenes and validates packet nesting; it uses exclusive creation and needs a fresh output path for another replay. `run.py` similarly refuses to overwrite existing runs. `prepare.py` refuses to overwrite prepared tasks. Preserve existing results when adapting output locations for replication.

Model transport initially failed: the first smoke call timed out after 90 seconds without persisted partial logs; smoke-02 retained retry/timeout logs. Smoke-03 succeeded after enabling the CLI's `respect_system_proxy` feature to honor the already configured macOS system proxy. No task answers existed before that transport change. All measured calls used that same setting and provider/model request. The first smoke's missing logs are a provenance limitation, not an evaluation result.

Only this external-test study was added. The static analyzer, dynamic probe engine and original source snapshots were not modified. No product dependencies were added and no Git commit was created.
