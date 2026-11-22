# DeepSeek experience-size ablation, 2026-11-22

Authorized: same fixed30 test cases,20 and40 experiences,8 workers,add DeepSeek to Fig3.

- DeepSeek-Flash / low, Qoder Credits, existing Qoder1.1.94 Docker execution.
- Structured testing: selection12 + Auto-Contract12 + Action24 model turns,600s per stage,one Action,frozen library,final Gold only.
- Global maximum8 workers: memory20 first,then memory40; controller owns both batches.
- Freeze the original58-entry bank,sort by bundle SHA256,shuffle once using Python Random(20261118),take prefixes20 and40. Selection never uses test outcomes.
- These are library-size subsets,not historical training checkpoints or number of experiences retrieved per case.
- Same tasks,original sources,model,images and budgets verified against the original58-entry run. Existing committed adapter/runtime diagnostic fixes are retained; no new adapter modifications for this ablation.
- DeepSeek Fig3 points:0(Auto-Contract Only),20,40,58. Preserve the original GPT curve at0,20,40,61. Banks differ; do not relabel58 as61 or interpret this as an isolated model comparison.
- Reuse Table1's1,000 paired30-case bootstrap samples(seed20260925),report mean and sample SD. Candidate crashes count as failure per user policy; infrastructure errors remain separate until resolved. Do not retry valid behavioral failures.

`plan.json` identifies runs and subsets. `paired-input-validation-*.json` records zero-model validation of all30 trajectories per arm. Local live progress is shown at http://127.0.0.1:8765/.

Commands from repository root:

```
# Already executed. Never repeat prepare over the frozen plan:
python3 -B experiments/testing-runs/deepseek-library-size-ablation-20261122/manage.py prepare
# Durable queue is already running; do not start a duplicate:
python3 -B experiments/testing-runs/deepseek-library-size-ablation-20261122/manage.py run
```

Figure source,bootstrap statistics,online source/PDF backups and UI publisher are in `review-drafts/fig3-deepseek-20261122/`. Publication refuses unfinished groups or unresolved execution errors. The final figure will retain the original image and use a new filename.

## Completed results

Both30-case ablations completed; the sole memory20 infrastructure-invalid attempt was replaced by one valid fresh replay. Retained29original memory20 scores and all30memory40 scores.

DeepSeek raw results:0entries6/30(20.0%);20entries18/30(60.0%);40entries17/30(56.7%);58entries18/30(60.0%). Bootstrap means±SD:19.9±7.2,60.5±9.1,56.9±9.0,60.0±9.1. One subset per size; no evidence of a monotonic improvement beyond20entries in this experiment.

Overleaf Fig3 image,caption and accompanying text updated and compiled; original GPT curve preserved. User explicitly deferred page-budget work; no further layout edits performed. See validation.json and summary.json.
