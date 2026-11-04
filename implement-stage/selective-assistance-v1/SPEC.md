# Conservative, explainable A/D routing candidate

Original request: summarize when the tool is useful, invoke it there, otherwise use A.

Implement an opt-in, deterministic routing candidate based only on original task text and frozen static evidence. Defaults to A. Candidate D families: pending/ready polling with continuation evidence; missing initial state with direct connect-before-listen evidence. Abstain on multi-effect audit/retry/ordering compositions, ambiguous tasks, incomplete scans and insufficient relevant evidence. Do not use case IDs, model IDs, outcomes, oracle checks or lessons as decision inputs. Preserve original A/D experiments and prompts; log decisions outside model-visible files.

Expose offline decision CLI and Workbench/CLI selective preparation/execution. Replay the original 24 paired configurations without new model calls; label this discovery-data replay, not an independent result or trained gate. Produce per-case routes, action reasons, result/partial-effect tradeoffs and cost of report delivery.

Base: 3a8fd7868128a8c5b7b93bd24666d3f5a92cc62b plus existing uncommitted implementation; do not overwrite earlier work.

Checks: meaningful gate/feedback-leakage/integration tests, affected workbench suites, frozen-data replay and fresh same-family assumption review (provisional).
