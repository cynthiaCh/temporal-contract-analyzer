# Low-noise presentation (0.6.2)

Implementation hypothesis: preserve the raw analysis interface and evidence, then narrow the default human-facing output. Filtering checks evidence completeness, does not select hints using known repair outcomes, and does not claim demonstrated benefits for users or LLMs.

- Markdown and HTML default to the focused view, including new archived reports. MCP reads of their full material return this Markdown. Historical archives and frozen A–G experimental material are unchanged.
- Use `--view exploratory` with CLI `scan` / `compare` to restore all hints and syntax events.
- CLI JSON, `analyze_sources` and archived JSON retain all original evidence regardless of `--view`. For compact structured input, use `temporal_contract_analyzer.review.focused_review(report)`.
- By default, only `write_after_call` candidates of `reentrant-state-publication` are shown: the file parses successfully; guard/callback/write and expanded-path references exist in that file; an `external_call_before_state_write` relation exists; no uncertainty is recorded.
- Candidates sharing a file, entry, state binding, guard and write merge into one card, retaining original hint IDs and each call's evidence. Different states or entries are not merged.
- `write_before_call` appears only as an ordering fact. `not_established` and other rules are counted under hiding reasons rather than converted into alerts. Omitted candidates do not establish safety; the current default filter does not cover other temporal issue classes.
- Each source excerpt is limited to 240 characters, with explicit truncation and file/line references. Original source and reports are not truncated.
- Parse failures, skipped scope and analysis limitations remain visible. Comparison sides are filtered independently; a disappearing card does not establish a repair.

Examples:

```sh
python3 -m temporal_contract_analyzer scan /path/to/project --format md
python3 -m temporal_contract_analyzer scan /path/to/project --format html --view exploratory
```

This change does not rebuild the VSIX, change old experiment filters or compute defect probabilities. Reduced output indicates changes in report length and display counts only; precision and practical assistance require independent project evaluation.

## Presentation check using an existing real repair

Analysis version 0.6.2 was rerun on `external-tests/reentry-publication-v1/fixtures/p-debounce/snapshots/{before,after}/index.js`, rendering two Markdown views from the same raw results:

| Version | Raw hints | Default issue cards | Exploratory characters | Low-noise characters |
|---|---:|---:|---:|---:|
| Before repair | 4 | 1 | 11,090 | 1,855 |
| After repair | 4 | 0 | 10,337 | 848 |

The repaired version additionally retains an ordering fact: `currentPromise` is written at L121; the external call is at L129. These are report character counts, not tokens, cost, precision or LLM success rates. This case participated in rule development and is not an independent validation set.

## 0.6.3 addition

The same filter now displays one-shot callback clearing candidates in restricted positive branches, without relaxing the complete-evidence/no-recorded-uncertainty threshold. Fixed onetime source changes from zero cards to one, citing L17 guard, L18 call and L19 clear. See the 0.6.3 section of `STATE_PUBLICATION_REVIEW.md`. Original development checks and historical reports are not overwritten.

## 0.6.4 addition

The threshold is unchanged. New bounded nested paths can establish complete guard/call/flag-write relations. Original component/once source is recognized as writing first and retains ordering facts only; an artificial delayed-flag variant writes afterward and displays one card with the outer receiver condition. Different branches are not merged; `this[key]` state remains unsupported. See `STATE_PUBLICATION_REVIEW.md` for boundaries.

## 0.6.5 addition

The filter threshold is unchanged. Simple one-hop parameter-copy calls after a strict null early return are supported. Default cards retain the copy location and distinguish original-binding clearing from copy overwriting. Original Async.once source lists a clear-before-call fact only; an artificial delayed-clear variant displays one card. Full limitations appear in `STATE_PUBLICATION_REVIEW.md`.

## 0.6.6 addition

The threshold is unchanged. Reflect.apply/construct candidates for a captured receiver function are stored separately per call; selected conditional arms are not combined as simultaneous execution. The default view merges candidates for the same flag while retaining both call locations and provenance. Original @ungap/once source lists two write-before-call facts; an artificial variant merges into one issue card. See `STATE_PUBLICATION_REVIEW.md`.

## 0.6.7 addition

The default filter can use new post-call clearing evidence without weakening source/relation completeness requirements. Reports separate entry-state write ordering from subsequent callback-binding clearing. The latter receives a neutral note rather than automatically becoming an issue. Original just-once retains cleanup without an alert; an artificial delayed-flag variant displays one card. Candidates lacking the new relation fields are conservatively hidden.

## 0.6.8 addition

The threshold is unchanged. Restricted numeric-budget checks list decrement-before-call as an ordering fact; decrement-after-call can produce one review card. Associated conditional cleanup is shown with its own condition, without treating clearing as inevitable on every path. Interpretation depends on a finite safe-integer budget and its actual purpose. See `STATE_PUBLICATION_REVIEW.md`.
