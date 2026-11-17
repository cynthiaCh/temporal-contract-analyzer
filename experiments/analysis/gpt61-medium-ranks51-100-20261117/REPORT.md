# GPT-6.1 medium failure ranks 51–100

Rank `gpt-6.1-sol` / `medium` by original latent failure fraction over valid
trials, descending. Break ties by valid sample count descending, then exact ID.
This is a new single-model ranking, not the previous two-model composite hard100.
Missing/invalid trials are not failures. Data source: frozen
`swe242-per-case-model.csv` (hashes in `summary.json`).

| Original latent baseline | Cases | Valid trials | Failures |
|---|---:|---:|---:|
| 11/11 passes | 5 | 55 | 0 |
| 10/10 passes | 4 | 40 | 0 |
| 2/2 passes | 14 | 28 | 0 |
| 1/1 passes | 27 | 27 | 0 |
| Total | 50 | 150 | 0 |

1. Observed pooled and per-case failure rates are **0%**. Only 41 of all 214
   eligible cases have any observed GPT-6.1 medium latent failures. Thus positions
   51–100 belong to a broad zero-failure tie, not an established difficulty tier.
   41/50 have at most two samples; zero observed failures does not establish the
   true failure probability.
2. Public protocol/state audit finds 11/50 completed experience-pipeline tests;
   39 have no completed test. 12 exact IDs are in train70 (one also tested), leaving
   28 without any observed started learning/testing trajectory. All 50 already
   have original baseline evaluations. See `exposure-evidence.json` for run paths.
3. All 15 core classes (`parent_case_id`) have examples in the actual incremental
   train70 roster: coverage 15/15 clusters and 50/50 selected cases. Exact-ID overlap
   is 12/50. Cluster coverage does not certify correct experience retrieval or
   applicability. Full per-core counts: `cores.csv`; full 50-case roster: `cases.csv`.

Suggested next step: if evaluating difficult failures, use observed-failure cases
or repeat sparse baselines before selecting more cases. If testing transfer within
covered core classes, the 28 not previously run are available diagnostic candidates,
but these zero-failure baselines offer little room for measured improvement.

Audit scope: sibling tempoevo protocol/state directories at the documented run
layouts plus the earlier exposure inventory. Absence means no record found within
this scope; it does not certify globally unseen data or complete older experience
lineage. No models launched, no historical scores changed.

Reproduce: `python3 experiments/analysis/gpt61-medium-ranks51-100-20261117/analyze.py`
