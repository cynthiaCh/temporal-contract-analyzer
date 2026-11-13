# Training acceptance change: implementation and offline handoff

## Assumptions and boundaries

- Requested `/Volumes/Extreme/paper+survey/temporal-contract-analyzer` is not mounted
  in this session. Work used the shared Linux checkout at
  `/home/sribd/Downloads/wangshu/temporal-contract-analyzer`.
- No applicable AGENTS.md was found in the checkout or its ancestor directories.
  Initial git status, unstaged diff and staged diff were clean. Existing histories,
  memory records and case split data are not rewritten.
- `gold_evaluator` retains independent-testing semantics; new learning configurations
  must explicitly select `training_evaluator`. No implicit migration/fallback.
- Public checks are required as a whole by default; a false
  `required_visible_checks` explicitly makes them diagnostic, never sufficient alone.
- The original benchmark probe is accessible in the sibling benchmark. Its
  `verdict`, `observed_effects`, `schedules`, runtime errors and exit-code contract
  were inspected. Historical real PASS and UNDERREACH envelopes normalize correctly.
  The scorer criteria and source were not modified.
- No independent dataset split audit is available. Existing registered training
  cases are exposed development; no completed held-out isolation is claimed.

## Task 1: protocol, stopping and experience routing

`tempoevo_v4.py` implements protocol V5. Training evaluates each real candidate
with public checks and training acceptance. Only accepted trajectories enter
success extraction/publication; three effective failures request a real expert.
Invalid assessments are not counted as behavior failures. Completed accepted
checkpoints resume without an extra Action. Testing retains public-only repair,
one final independent Gold, and no memory writes. Old protocol execution is
rejected before lock creation; historical summary inspection does not rewrite it.
Shared transport files and the CLI recognize the new protocol without restoring
any legacy controller. Model and request caps are unchanged; evaluator counts and
timeouts are newly explicit frozen configuration.

## Task 2: scorer adaptation and feedback

`training_acceptance.py` normalizes original verdicts, legacy envelopes and explicit
boolean results. It rejects missing/contradictory verdicts and runtime failures.
Native and Docker transports accept valid negative scorer exit 1 without treating
it as PASS; the benchmark wrapper retains original exit/verdict consistency checks.
Raw JSON is archived separately. Only verdict feedback and opt-in configured public
boolean checkpoint descriptions enter model stages; raw assertions, code, paths,
patches and unconfigured scorer IDs do not. Docker evaluator topology remains
unchanged; no grader/reference mounts are added to model workspaces.

## Task 3: offline checks, examples and documentation

Related test command:

```sh
PYTHONPATH=tests python3 -B -m unittest test_tempoevo_v4 test_training_acceptance test_tempoevo_docker test_analysis_runner test_execution_backend test_history_readonly
```

Validation result: **70 related offline tests passed**, including **17 new acceptance tests**. Python/JSON syntax, affected Markdown links and `git diff --check` passed.

New acceptance tests cover continuing after training Gold failure, public-required
failure, optional public checks, three failures/expert routing, invalid execution,
missing acceptance config, controlled feedback, independent testing isolation,
old protocol rejection/read-only reports, resumed accepted checkpoints, guarded
publication, preserved assessment after extraction failure and raw verdict/exit-1
adaptation. Python syntax, JSON examples and diff whitespace are checked separately.
README, architecture, V5 protocol, Docker instructions, learning examples, offline
demo and batch tooling are updated. Historical V4 protocol documentation is labeled.

Validation is synthetic/offline plus parsing retained real scorer output. No new
benchmark execution, Docker end-to-end scoring, real model request, paid training,
formal experiment, historical replay or Git commit was performed. Real V5
end-to-end deployment remains unverified. Boolean feedback mapping is deliberately
limited; arbitrary expected/actual strings are not passed through. Cross-root and
renamed-source split isolation still requires an audited dataset registry.

Recommended commit text (not committed):

```text
fix(tempoevo): gate learning on per-attempt training acceptance

Introduce V5 train/test acceptance boundaries and controlled scorer feedback.
Gate success experience on training acceptance, preserve read-only V4 history,
and cover retries, invalid scoring, held-out isolation and checkpoint recovery.
```
