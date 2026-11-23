# Selected-case Docker batches

`prepare_selected.py` prepares and freezes inputs; it does not call a model.
`run_selected.py --execute` starts the explicitly authorized experiment. Always
use a new output root. Historical trajectories are not reinterpreted or resumed
under a different protocol.

The default selection is `cases/train70.csv` for learning and `cases/test30.csv`
for testing. These are the only current 70/30 split, documented in
[the complete case bundle](../../cases/README.md). To use an explicit ranked CSV,
pass `--selection-file`. To resolve public inputs directly from the
frozen SWE-TempoC roster, also pass `--swe-tempoc-root` (regular cases support training and testing; upstream tasks currently support testing only):

```bash
python3 -B tools/tempoevo-docker/prepare_selected.py \
  --root /new/batch/root \
  --selection-file cases/test30.csv \
  --swe-tempoc-root /path/to/swe-tempoc \
  --solver-image sha256:SOLVER_IMAGE_ID \
  --grader-image sha256:GRADER_IMAGE_ID \
  --mode testing --condition structured --model-profile sol56-medium --limit 30
python3 -B tools/tempoevo-docker/run_selected.py --root /new/batch/root --execute
```

The image arguments require full immutable locally present IDs. Preparation
archives the actual selected CSV and source digest. It validates unique ranks
and case IDs, existing split restrictions, public source identity and the current
protocol. Failed preparation remains explicit in `progress.json`.

Current V13 testing uses Auto-Contract and, for `structured`, a frozen approved
experience snapshot. It permits one bounded Action, then one independent Gold
evaluation. Gold does not enter model feedback or retry decisions. Testing does
not extract or publish experiences. Historical difficulty-based selection is
diagnostic, not evidence of an unseen independent test set.

For regular roster cases, only the public maintenance core and base are loaded;
provided Contract suffixes, references and scorer contents are not solver inputs.
The RxJS upstream maintenance case additionally uses `upstream_inputs.py`: it
extracts all original `src/**`, named original public tests, and root documents
from the checksum-bound original archive. Full upstream npm dependencies are
not mounted in the solver. `upstream_gold.py`, on the trusted side, restores the
unprojected original files and applies the actual submitted changes (including
deletions in the projection), then invokes the unchanged SWE-TempoC scorer.
Trusted tests and reference patches are never copied to the solver. This public
source projection differs from historical full-repository baselines and must be
reported when comparing that case. Full grading is validated by the eventual
final score, not by preparation or source extraction alone.

The explicit learning-only `--training-recipe v8-compatible-v1` restores V8
source-bound experience routing, required external public checks plus Gold, and
the non-cumulative Action feedback format. It requires `--public-checks-docs`
(case ID to public example description) and can use an exact audited
`--memory-snapshot` with its retained approved history in `--store`. The public
evaluator runs outside the solver; only descriptions enter the candidate. Its
original/reference/negative controls are archived alongside independent Gold
controls, and the reference must pass both evaluators. Default retrieval and acceptance settings are
unchanged; V13 uses advisory preparation validation. Testing rejects this recipe and training-only check descriptions.

The current experiment uses the final 30 test cases with frozen approved
libraries of 0/20/40/61 entries. See [the current workflow](../../docs/WORKFLOW.md)
and [the final results](../../experiments/testing-runs/gpt56-library-size-ablation-20261118/README.md).

Training artifacts written outside the Git worktree must not be the only copy of
learned guidance. After a batch, archive provisional entries, candidate reflections
and evidence proposals under `experience-memory/training-runs/<run-id>/`, preserving
original bytes, source paths and SHA-256 hashes, and commit them to Git. Stage content
candidates in the categorized library as pending for review. Committing candidates
does not approve them or change an already frozen retrieval snapshot.

Structured training and testing default to Abstract-based `business-source-v1`.
Training rechecks applicability after Contract revisions, retains its existing
three-Action/public-check/Oracle acceptance flow, and reserves up to 156 requests.
Testing uses one applicability-selection stage,
one Auto-Contract draft, one repair Action, then final-only Gold. All approved
entries are available for retrieval, with at most three applicable entries delivered.
No taxonomy-routing or Contract Review stage is added. Use `--memory-snapshot`
to bind an exact approved bank; pending guidance cannot enter that bank.

V13 preparation validation is advisory: missing mechanism evidence becomes unknown,
and unusable model guidance gets one correction sharing its original request/time
budget. Failed correction discards the guidance and continues to the sole testing
Action; it does not relax tool permissions, approved-memory checks or Gold isolation.
Use a new output root; historical V12 and earlier bindings and results remain read-only.
See [the current workflow](../../docs/WORKFLOW.md).

For a prepared single-group testing batch, `run_testing.py --root RUN_ROOT
--workers 4 --execute` schedules at most four independent trajectories concurrently.
The root contains `plan.json` plus `batch/progress.json`; every case must use the
same frozen approved bank and current single-submission testing protocol. One case
error does not abort the other cases, and incomplete previously started stages
are not replayed. Results retain the full denominator and archive after completion.
The current study uses the full approved categorized library as its retrieval pool;
A/B is historical and is not launched by this command.

For authorized larger testing queues, `run_testing.py --workers 8 --adaptive-workers`
permits eight concurrent case workers. Explicit provider rate/concurrency errors reduce
future admission to six, then four, while existing sessions drain. This never replays
started cases or changes per-case request, Action or scoring budgets. The queue archives
capacity changes and its observed peak; requested concurrency is not a provider guarantee.
