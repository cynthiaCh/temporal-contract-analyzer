# Table 1 update: GPT-5.6-sol medium

| Condition | Raw valid pass rate | Bootstrap mean ± SD (%) | Coverage |
|---|---:|---:|---:|
| Auto-Contract + Experience (historical) | 83.3% (25/30) | 83.47 ± 6.70 | 30/30 |
| Latent + Experience only (new) | 75.9% (22/29) | 75.91 ± 7.68 | 29/30 |

Use `cell.tex` for the new Table 1 cell. These values are the mean and sample SD of bootstrap accuracy, not raw accuracy plus a confidence interval.

Method: the requested tools/generate_bootstrap_indices.py, 1,000 paired draws of 30 case indices with replacement, random.Random seed20260925. Both conditions use identical draws. Unscored outcomes are excluded from each replicate denominator; the scored_flag input column records coverage and is not a ground-truth label. One case is unscored for the new arm, so effective bootstrap denominators vary.

Required table note: "Execution-invalid cases are excluded from the accuracy denominator, including within bootstrap resamples; the GPT-5.6 Latent + Experience arm has 29/30 valid cases. Entries report bootstrap mean ± sample SD over 1,000 shared case resamples (seed 20260925)."

The 61-entry library and historical per-case experience deliveries were frozen. The source/runtime differences from the historical parent are disclosed in the run README.

Overleaf has not been modified: Git authentication is unavailable and there is no connected document session. The exact existing Table 1 source is still required to preserve its structure and notes.

Reproduce from any checkout containing this archive:

```sh
python3 -B experiments/testing-runs/tempoevo-gpt56-sol-medium-latent-experience-test30-workers8-20261122_024039/table1-bootstrap/build.py
```
