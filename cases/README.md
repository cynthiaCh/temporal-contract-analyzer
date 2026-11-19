# Final experimental cases: train70 / test30

This directory preserves the complete final 100 experimental cases and maintains a single split:

```text
cases/
├── train70/                 # 70 training/development cases, one complete directory per case
├── test30/                  # 30 test cases, one complete directory per case
├── train70.csv              # Training order, ranks 1–70
├── test30.csv               # Test order, ranks 1–30
├── selected_100_cases.csv    # Final 100-case list and original global order
├── split.json               # Sole split definition
├── manifest.json            # Case index, per-file SHA-256 and source identity
└── verify.py                # Offline integrity check; no model calls
```

Each case directory preserves its original `case.json`, initial code `base/`, tasks/prompts `prompts/`, scorer `oracle/`, reference implementation `reference/`, negative variants `mutants/`, and original documentation/provenance. Case contents are byte-identical to the source files used in the final experiments. Organization did not rewrite code, prompts, reference repairs or scoring rules. Dependencies and language toolchains are supplied by the original pinned Docker environment rather than included in case source.

Model execution receives only the public maintenance task and `base/`. `oracle/`, `reference/` and `mutants/` are separate scoring/calibration material, excluded from model input. Minimum runtime versions, original launch instructions and dependencies remain in each case's original documentation.

`train70/` and `test30/` have disjoint case IDs; the 30 test cases match the final results. Training here means development/repair and experience processing, without model-parameter training. Cases have historical exposure and partially shared source mechanisms; this split is not an independent unseen-source test set.

Verify integrity:

```bash
python3 -B cases/verify.py
```

The default experiment preparation entry uses `train70.csv` or `test30.csv` according to run mode. `experiments/evaluation-splits.json` links to this directory's `split.json`. Final experimental scores are documented in the [experience-library size ablation](../experiments/testing-runs/gpt56-library-size-ablation-20261118/README.md).
