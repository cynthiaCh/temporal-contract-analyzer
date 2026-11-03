# Build Note — listener split

| Rung | Feature | Acceptance check | Tier | Status |
|------|---------|------------------|------|--------|
| F0 | Synchronous case base → oracle JSON; bounded repair → PASS | `/usr/bin/python3 -B -m unittest discover -s tests -p test_listener_split.py -k bootstrap` | MUST | passed |
| F1 | Asynchronous case and boundary-discriminating checks | `/usr/bin/python3 -B -m unittest discover -s tests -p test_listener_split.py` | MUST | passed |
| F2 | Local selection, prompt isolation and evaluation integration | `/usr/bin/python3 -B -m unittest discover -s tests -p test_experiment_workbench.py` | MUST | passed |

## Run record

F0: bootstrap check exited 0; `F0-smoke.json` records actual deterministic checks.

F1: four deterministic checks passed, including both bounded references, a reception-only incomplete repair, and metrics-policy negative controls.

F2: local catalog, preparation isolation and reference-calibrated evaluation passed; 16 original workbench tests passed.

## Deferred

Actual A/D/E model calls and statistical claims require a separately fixed experiment run. No automatic commits.

## Blockers

None at initialization.

Final executor closure: initial review found synchronous post-retirement reception during bootstrap in case 2. Declared A-008, added the optional predicate, guarded immediate delivery and added both inline-update and decoder-reentry schedules. All five split tests passed after updating the order-only negative control. Second review requested.

Second review returned clean, zero undeclared semantic decisions; same-family/provisional. No live stubs. All MUST rungs passed; no model calls or commits.
