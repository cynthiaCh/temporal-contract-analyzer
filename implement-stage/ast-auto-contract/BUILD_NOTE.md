# Build Note

| Rung | Feature | Acceptance check | Tier | Status |
|---|---|---|---|---|
| F0 | Prepare registered source into AST and analysis artifacts | `python3 -B -m unittest discover -s tests -p test_auto_contract.py` | MUST | passed |
| F1 | Analysis model role, explicit review and training continuation | focused analysis/evolution tests | MUST | passed |
| F2 | Native/Docker extraction wiring and docs | focused backend and analysis tests | MUST | passed |

## Run record

- F0: `test_auto_contract.py`, 3 tests passed using `/usr/bin/python3` (3.9.6); CLI preparation produced real local AST artifacts with no model.
- F1: expanded `test_auto_contract.py`, 14 tests passed; analysis/review/training and evaluation exercised with explicitly synthetic responses. Existing evolution tests: 18 passed.
- F2: packaged runner fixture tests: 3 passed; native backend tests: 7 passed; Docker backend tests: 12 passed. No Docker daemon or real model session was required.
- The default `python3` here is 3.7.3, below the repository's declared Python 3.9 minimum; validation uses `/usr/bin/python3`.
- Changes remain in the working tree for review; no implementation commits were created.

- Final full suite: `/usr/bin/python3 -B -m unittest discover -s tests`, 386 tests passed in 113.681 seconds. One later-added starting-repairs-stop regression also passed in the 14-test focused analysis suite. Full log: `/tmp/tca-auto-contract-tests-final.log`.
- The first full run exposed two stale class-reminder expectations from the earlier English prompt change; expectations were updated and the final full suite passed.
- `git diff --check` passed.

## Deferred
Real model runs and repair-benefit claims are outside implementation scope.

## Blockers
None.

## Review

Fresh-context Codex review completed. Two concrete issues were reproduced and fixed (A-010/A-011); final response found zero remaining undeclared assumptions or integration defects. Same-family review remains provisional. Reviewer routing helper was absent; the documented native default was used and recorded.
