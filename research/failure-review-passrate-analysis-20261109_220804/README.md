Historical case pass-rate ranking

Open `ranking.html` for a standalone sortable table. Filter by model, effort, prompt condition, variant and minimum valid sample size. The default pools all saved configurations; it is a descriptive archive summary, not an intrinsic-difficulty estimate.

Use `case_ranking.csv` in Excel for the complete ranking of all 249 case IDs. Equal pass fractions share a dense rank. The lowest-rate view is useful for difficulty screening, but a 0/2 observation should not outrank a well-supported difficulty claim. One case has no admissible score evidence and remains N/A.

Main result: 6,603 / 9,694 = 68.11%, after exact-copy folding and explicit receipt admission. The failure-only index is not the denominator. Contaminated PASS labels, unscored/invalid statuses and missing saved-score evidence are excluded. Six completed candidate runtime failures retain their original non-PASS grades; runtime-error exclusion sensitivity is saved separately.

Files:

- `REPORT.md`: method, overall statistics, low/high-rate examples, recent discussion cases, all-case table and limitations.
- `case_model_condition.csv`, `case_model_condition_version.csv`: model/effort/condition and available-version details. Use these before selecting a case for a new protocol.
- `case_ranking_raw_receipts.csv`: sensitivity to retaining every saved copy.
- `condition_deltas_descriptive.csv`: differences from latent-maintenance within recorded strata; no causal-effect claim or fabricated zero-rate baseline.
- `execution_groups.csv/json`, `duplicate_groups.csv`, `excluded_records.csv`: complete row-level audit and original paths. Excluded CSV includes both real-model exceptions and two model stubs; summary primary counts include real models only.
- `runtime-result-review.json`, `export-reconciliation.json`: candidate-runtime evidence and differences from the exporter's provisional classifications.
- `raw-run-receipts.jsonl`, `run-receipts.json`, `score-projections.json`, `outer-projections.json`: archived input objects and reduced analysis data.
- `source-provenance.json`, `integrity.json`, `ARTIFACTS.sha256`: source identity and artifact integrity.

Reproduce with Python 3 standard library:

```bash
python3 -B research/failure-review-passrate-analysis-20261109_220804/read_inventory.py
python3 -B research/failure-review-passrate-analysis-20261109_220804/analyze.py
python3 -B research/failure-review-passrate-analysis-20261109_220804/build_report.py
```

These commands only analyze local data. They do not call a model, rerun grading or execute scripts from the ZIP. `read_inventory.py` reads a 2.88-GB uncompressed ledger, so let the stream finish. No archive contents need to be fully extracted.

Eleven offline analysis tests passed. Seven standalone HTML DOM-logic checks passed, including full row counts, N/A handling and matched model/effort filtering. This is not a full browser layout test. No production files or original results were changed, and no Git commit was created.
