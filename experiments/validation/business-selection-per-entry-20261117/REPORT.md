# Per-entry selection validation replay

The selector now rejects invalid candidate assessments individually instead of
clearing independently validated guidance. Identical duplicate assessments are
merged; conflicting duplicates are rejected as a group. Unknown prerequisites
remain unsupported. Shared obligation errors invalidate their dependent rows.

Offline replay used the frozen public task, original source inventory, approved
bank, recalled candidates and raw selection outputs from
`tempoevo-gpt6-medium-low20-workers8-20261117_112828`. It read no Gold files and
performed no model calls, code repair or scoring. Historical files were not modified.

All 8 cases whose entire selection was previously discarded retain valid guidance
under the new policy: 15 experience deliveries in total (1–3 per case). Each case's
first selection output is independently usable; no correction request would be
needed. Corrected historical outputs were also replayed for diagnostics but do not
override the first usable output. Full selected IDs, source-result hashes and
validation issues are in `replay.json`.

This establishes recovery of validated guidance, **not an improvement in task pass
rate**. Measuring repair performance requires a newly prepared test run.

Reproduce from the repository root:

```sh
python3 experiments/validation/business-selection-per-entry-20261117/replay.py /path/to/tempoevo-gpt6-medium-low20-workers8-20261117_112828
```

Validation: all 10 targeted business-retrieval tests pass, including partial
selection reaching Contract and Action without an extra correction, conflicting
and identical duplicates, unsupported prerequisites and invalid source quotes.
Full suite: 679 tests, 678 pass; the existing unrelated
`test_incremental_review.IncrementalReviewTests.test_browser_form_only_submits_changed_rule_and_can_switch_to_full`
fails with `Cannot read properties of undefined (reading 'replaceChildren')`.
