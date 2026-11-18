# React polling restoration with low-salience lifecycle evidence

Case ID: `download-polling-restoration-low-cue-react18`. Directory: `case-clusters/download-polling-restoration/arms/download-polling-restoration-low-cue-react18/`.

| Field | Recorded value |
|---|---|
| Language | javascript-typescript |
| Source | clean_room_reconstruction (clean-room reconstruction of the issue mechanism) |
| Research unit | `download-polling-restoration` |
| Mechanism index | lifecycle_invalidation |
| Metadata | [case.json](case.json) |

## Target obligations and evidence

Pending preparation must retry until ready, while close and reopen invalidate only the foreground dialog's timer and in-flight generation unless broader migration is authorized.

Source provenance, historical exposure, and independent review are recorded in metadata. Directory names and fields do not imply a case stage. Mechanism names are research indices, not automatically validated classification results.

## Local verification and task preparation

Run from the repository root in an evaluation environment with the required dependencies installed:

```bash
python3 -B swe_tempoc.py verify --case download-polling-restoration-low-cue-react18 --output workspaces/download-polling-restoration-low-cue-react18-controls
python3 -B swe_tempoc.py prepare --case download-polling-restoration-low-cue-react18 --condition L --output workspaces/download-polling-restoration-low-cue-react18-L
```

`verify` checks the correct reference repair and its registered negative control; `prepare` exports the prompt and initial candidate code.
Neither command calls a model. Use fresh output directories; passing controls does not replace independent semantic review.
Replace `--condition L` with `--condition C` to prepare the condition that explicitly supplies temporal contracts.
Give the agent only the exported `prompt.md` and `candidate/`; keep evaluation materials on the evaluator side.
See the [usage guide](../../../../README.md) for setup, grading, and the separate experiment runner.

[Case roster](../../../../benchmark/swe-tempoc.json) · [Evaluation guide](../../../../README.md)
