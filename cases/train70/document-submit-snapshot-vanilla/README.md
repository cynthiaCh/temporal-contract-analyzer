# Coalesce document edits while preserving accepted submission snapshots

Case ID: `document-submit-snapshot-vanilla`. Directory: `case-clusters/document-review-binding/arms/document-submit-snapshot-vanilla/`.

| Field | Recorded value |
|---|---|
| Language | javascript-typescript |
| Source | authored_development |
| Research unit | `debounced-submit-flush` |
| Mechanism index | barrier_flush |
| Metadata | [case.json](case.json) |

## Target obligations and evidence

Persist accepted text before receipt capture, retain the entry-owned submission across inline navigation, and suppress only a retired visit notice while preserving departure and preview contracts.

Source provenance, historical exposure, and independent review are recorded in metadata. Directory names and fields do not imply a case stage. Mechanism names are research indices, not automatically validated classification results.

## Local verification and task preparation

Run from the repository root in an evaluation environment with the required dependencies installed:

```bash
python3 -B swe_tempoc.py verify --case document-submit-snapshot-vanilla --output workspaces/document-submit-snapshot-vanilla-controls
python3 -B swe_tempoc.py prepare --case document-submit-snapshot-vanilla --condition L --output workspaces/document-submit-snapshot-vanilla-L
```

`verify` checks the correct reference repair and its registered negative control; `prepare` exports the prompt and initial candidate code.
Neither command calls a model. Use fresh output directories; passing controls does not replace independent semantic review.
Replace `--condition L` with `--condition C` to prepare the condition that explicitly supplies temporal contracts.
Give the agent only the exported `prompt.md` and `candidate/`; keep evaluation materials on the evaluator side.
See the [usage guide](../../../../README.md) for setup, grading, and the separate experiment runner.

[Case roster](../../../../benchmark/swe-tempoc.json) · [Evaluation guide](../../../../README.md)
