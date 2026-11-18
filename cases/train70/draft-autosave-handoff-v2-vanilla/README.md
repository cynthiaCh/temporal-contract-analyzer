# Coalesce document-owned draft writes without navigation callbacks

Case ID: `draft-autosave-handoff-v2-vanilla`. Directory: `case-clusters/draft-handoff-decomposition/arms/draft-autosave-handoff-v2-vanilla/`.

This unit isolates autosave handoff from the original `draft-autosave-handoff` construction. Normal saves write only to the document store and update the current document's save status; save callbacks have no navigation capability. The case measures 120 ms coalescing, departure flush, document ownership, view retirement, exactly-once writes, and discard behavior in the adjacent preview.

Run from the repository root with the required evaluation dependencies installed. Use a fresh output directory. Neither command calls a model.

```bash
node case-clusters/draft-handoff-decomposition/arms/draft-autosave-handoff-v2-vanilla/oracle/demo.cjs
python3 -B swe_tempoc.py verify --case draft-autosave-handoff-v2-vanilla --output workspaces/draft-autosave-handoff-v2-vanilla-controls
```

Trusted tests are in `oracle/`; candidate-visible source is in `base/`. Source attribution follows `source_unit` in the release roster. This case does not inherit historical results from the old synthetic-reentrancy case and is not a new independent production incident.

[Case roster](../../../../benchmark/swe-tempoc.json)
