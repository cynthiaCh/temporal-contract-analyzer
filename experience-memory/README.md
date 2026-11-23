# Categorized experience library

**Current experience lives in `library/`, with one JSON file per topic.**

| Category file | Stored entries | Active entries |
| --- | ---: | ---: |
| [mechanisms.json](library/mechanisms.json) | 12 | 5 |
| [progress-subscriptions.json](library/progress-subscriptions.json) | 8 | 5 |
| [deferred-persistence.json](library/deferred-persistence.json) | 11 | 7 |
| [shared-work-cancellation.json](library/shared-work-cancellation.json) | 6 | 5 |
| [candidates.json](library/candidates.json) | 37 | 30 |
| [zz-consolidated.json](library/zz-consolidated.json) | 6 | 6 |

The library contains 80 stored entries and 58 active entries. Explicitly replaced
entries remain stored but are excluded from the review queue and new retrieval.
Ordinary updates keep the same ID. They do not create a version chain.

Each entry includes a stable ID, English title, labels, applicability conditions, recommendation, preservation requirements, counterexamples and verification. Inline `review` records store reviewer, decision and time, under this session's authorization for Iris to accept experience. New entries without `review` appear as pending and are excluded from default retrieval. Content acceptance does not establish success in new transfer experiments.

New training candidates are published centrally to `library/candidates.json` as needed, appear directly in the review page as pending, and are excluded from default retrieval without changing existing approved snapshots. New mechanisms receive a stable ID. Revisions overwrite the target entry in place and reset content/summary review to pending; merges retain the primary ID and explicitly mark other targets as replaced after acceptance. Detailed reflections remain in the task's original `candidate-pool/`, without copying legacy source, version or decision files. Evidence-only additions with unchanged experience content retain the original candidate rather than creating duplicates.

Double-click `launch-experience-review.command` at the repository root to open review. Filter by category and review state together. Decisions are written only to the entry's category file, without separate decision files, case copies or source archives. Direct file editing is also supported; IDs must be unique across files. New topics can use additional files in the same format, discovered automatically by the page.

```bash
python3 -B -m temporal_contract_analyzer experience-memory review --store experience-memory/library
python3 -B -m temporal_contract_analyzer experience-memory freeze --store experience-memory/library
```

Old `records/`, `sources/` and similar directories are historical material, excluded from current categorized-library reads. The old single-file `experiences.json` was removed to avoid competing current entry points.

## Preserving training candidates in Git

Pending, rejected and evidence-only candidates must also be committed to Git. External experiment directories are outside this repository's Git management and cannot be the sole preservation location. At the end of each training round, archive temporary experience, candidate reflections and evidence proposals unchanged under `training-runs/<run-id>/`, with file hashes and provenance manifests, and commit them. Publish content revisions separately as pending entries in `library/candidates.json`. Archive directories are not category libraries or default retrieval inputs. A Git commit is not review approval and must not change frozen snapshots or automatically activate experience.

## Experience and summary review

The category files in `library/` are the current source of truth for both guidance
and its `summary` object (`text`, `expert_questions`, exact `source_record`, and
inline `review`). All current abstracts are in English and accepted under Rhys,
with expert judgments incorporated into their applicability boundaries. Guidance
acceptance and replacement targets are unchanged. Redundant standalone summary
exports have been removed; edit and review summaries in the library.

Open `launch-experience-review.command`. The review queue supports content search,
category, experience state and summary state filters. Select an entry, compare its
editable summary and expert questions against the full experience, then enter your
name and save a draft or review decision. Experience acceptance and summary
acceptance are separate. Neither opening the page nor saving a review calls a model.

New contrastive training publications include a model-written English Abstract in the same record, pending review.
Only accepted summaries bound to the current experience version enter newly frozen
snapshots. Pending, rejected, missing or outdated summaries fall back to the existing
extractive preview; accepted guidance remains eligible. Editing a summary requires
an explicit new decision, and concurrent edits are rejected rather than overwritten.
Changing guidance invalidates its old summary for retrieval until it is reviewed again.

Business matching prioritizes accepted summaries in the local index, retaining the
original extractive terms for English/Chinese matching. The top 6 candidates still
include full guidance for source-based applicability checks; final delivery remains
limited to three entries / 8000 characters. Frozen snapshots include the accepted summary and its review,
so later summary edits do not change an existing run. No new repair benefit is claimed.

## Simple learning and priority

First-Action successes skip extraction. Only failed-to-successful training
trajectories call the existing extractor, using patch differences and at most
three related entries instead of the full library and repeated source snapshots.
Implementation-only fixes do not produce new guidance. Three failures still
request an expert summary. No additional scoring model call is added.

Each entry keeps `learning.origin`, `initial_priority` and `usage_by_model`.
Origins record the verified reflection model/effort, repair model and first
successful Action. Unknown historical origins remain null; existing entries start
at zero rather than receiving invented credit. A source-supported experience-gap
correction starts at one. Unique-case observations count deliveries, evidenced
adoptions and specifically evidenced misleading recommendations separately.
Small case-result keys in the same JSON make updates idempotent across retries;
full evidence remains in the existing trajectory. Literal rule/code/source quotes
are checked, but semantic contribution judgments remain fallible and are not causal
proof. Uncertain or malformed claims receive no credit. A rule-error finding pauses
the entry for content review. Case failure alone never decrements every entry.

Priority is clamped to [-3, 5]: initial priority plus positive cases minus negative
cases. Current-repair-model observations are preferred; absent those, global
observations are used. Relevance and applicability remain ahead of priority.
Statistics never enter model prompts or change guidance identity/summary approval.
Training updates live statistics only after completion; testing never writes them.
Frozen snapshots retain the exact source, review, Abstract and learning metadata
used by a run, so an in-place library edit does not change an existing experiment.
