# Listener bootstrap ordering with reentrant navigation and pending decoding

Case ID: `listener-registration-order-vanilla`. Directory: `case-clusters/listener-registration-order/arms/listener-registration-order-vanilla/`.

| Field | Recorded value |
|---|---|
| Language | javascript-typescript |
| Source | clean_room_reconstruction (clean-room reconstruction of the issue mechanism) |
| Research unit | `listener-registration-order` |
| Mechanism index | precedence |
| Metadata | [case.json](case.json) |

## Target obligations and evidence

Presence must receive bootstrap while preserving visit-bound decoded delivery and cleanup across reentrant navigation; metrics retains its separate policy.

Source provenance, historical exposure, and independent review are recorded in metadata. Directory names and fields do not imply a case stage. Mechanism names are research indices, not automatically validated classification results.

## Local verification and task preparation

Run from the repository root in an evaluation environment with the required dependencies installed:

```bash
python3 -B swe_tempoc.py verify --case listener-registration-order-vanilla --output workspaces/listener-registration-order-vanilla-controls
python3 -B swe_tempoc.py prepare --case listener-registration-order-vanilla --condition L --output workspaces/listener-registration-order-vanilla-L
```

`verify` checks the correct reference repair and its registered negative control; `prepare` exports the prompt and initial candidate code.
Neither command calls a model. Use fresh output directories; passing controls does not replace independent semantic review.
Replace `--condition L` with `--condition C` to prepare the condition that explicitly supplies temporal contracts.
Give the agent only the exported `prompt.md` and `candidate/`; keep evaluation materials on the evaluator side.
See the [usage guide](../../../../README.md) for setup, grading, and the separate experiment runner.

[Case roster](../../../../benchmark/swe-tempoc.json) · [Evaluation guide](../../../../README.md)
