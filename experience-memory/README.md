# Categorized experience library

**Current experience lives in `library/`, with one JSON file per topic.**

| Category file | Contents | Entries |
| --- | --- | ---: |
| [mechanisms.json](library/mechanisms.json) | General mechanism summaries | 12 |
| [progress-subscriptions.json](library/progress-subscriptions.json) | Initial state, admission windows, auditing, out-of-order results, retries and resource cleanup | 8 |
| [deferred-persistence.json](library/deferred-persistence.json) | Deferred saves, document ownership, commits, confirmation, notification and component cleanup | 11 |
| [shared-work-cancellation.json](library/shared-work-cancellation.json) | Offline recovery, actual consumption, shared observers, background policies and attempt isolation | 6 |

This consolidation combined 524 rules across 71 versions and 54 experience identities in the old library, plus the existing 12 mechanism summaries, into the 37 entries above. Version counts are not independent experience counts. Repeated cross-language descriptions were merged by topic; conditional differences remain in applicability conditions, counterexamples and verification. Distinct requirements for finishing before exit versus continuing scheduling, and save notification versus subscription removal ordering, remain separate rather than being replaced by one policy. All 12 original summaries remain in the general mechanisms category.

Each entry includes a stable ID, English title, labels, applicability conditions, recommendation, preservation requirements, counterexamples and verification. Inline `review` records store reviewer, decision and time, under this session's authorization for Iris to accept experience. New entries without `review` appear as pending and are excluded from default retrieval. Content acceptance does not establish success in new transfer experiments.

New training candidates are published centrally to `library/candidates.json` as needed, appear directly in the review page as pending, and are excluded from default retrieval without changing existing approved snapshots. Their `proposal` records addition, revision or merging and the relevant experience IDs; publishing does not overwrite or delete original entries. Detailed reflections remain in the task's original `candidate-pool/`, without copying legacy source, version or decision files. Evidence-only additions with unchanged experience content retain the original candidate rather than creating duplicates.

Double-click `launch-experience-review.command` at the repository root to open review. Filter by category and review state together. Decisions are written only to the entry's category file, without separate decision files, case copies or source archives. Direct file editing is also supported; IDs must be unique across files. New topics can use additional files in the same format, discovered automatically by the page.

```bash
python3 -B -m temporal_contract_analyzer experience-memory review --store experience-memory/library
python3 -B -m temporal_contract_analyzer experience-memory freeze --store experience-memory/library
```

Old `records/`, `sources/` and similar directories are historical material, excluded from current categorized-library reads. The old single-file `experiences.json` was removed to avoid competing current entry points.

## Preserving training candidates in Git

Pending, rejected and evidence-only candidates must also be committed to Git. External experiment directories are outside this repository's Git management and cannot be the sole preservation location. At the end of each training round, archive temporary experience, candidate reflections and evidence proposals unchanged under `training-runs/<run-id>/`, with file hashes and provenance manifests, and commit them. Publish content revisions separately as pending entries in `library/candidates.json`. Archive directories are not category libraries or default retrieval inputs. A Git commit is not review approval and must not change frozen snapshots or automatically activate experience.
