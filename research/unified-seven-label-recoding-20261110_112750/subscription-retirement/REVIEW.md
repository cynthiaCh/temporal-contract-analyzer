# Expert review: subscription-retirement

Status: AI-assisted label recoding, pending real expert acceptance.

Parent: `bbd83db94e985da0e1ae126ab2c1b038474c8fac1ee6e2cbacbe1271df5d52e2`

Candidate: `5cabe14e287df04ac1a70a99662b41827c452fb8c62c846efc895d5585b0a17e`

Candidate labels: O, L, I, A. Rule text and applicability are unchanged.

Check both each rule and its proposed labels against the actual source; a valid quotation is not automatic semantic support. No new repair replay has occurred.

## R01

Applies when a shared source can be reused across visits, each attempt has an independent subscription, and visible feedback can synchronously reenter navigation. The same data object does not imply the same visit identity.

**O / documented_requirement**: Applicability includes synchronous feedback reentry, requiring consistency across that boundary.

- [README.md:58](/home/sribd/Downloads/wangshu/temporal-contract-analyzer/research/transfer-progress-evolution-locked-applicability-20261109_102520/training/inputs/source/README.md:58) — new visits remain live. `showProgress` may synchronously select or hide through

**L / documented_requirement**: Shared source reuse and per-attempt subscriptions have visit-scoped effect permission.

- [README.md:50](/home/sribd/Downloads/wangshu/temporal-contract-analyzer/research/transfer-progress-evolution-locked-applicability-20261109_102520/training/inputs/source/README.md:50) — by multiple panel visits. Each selected or retried attempt starts one subscription.
- [README.md:57](/home/sribd/Downloads/wangshu/temporal-contract-analyzer/research/transfer-progress-evolution-locked-applicability-20261109_102520/training/inputs/source/README.md:57) — that already started. Closing or replacing the visit stops visible progress;

Review boundary: Same-object contrast alone is not used as I evidence; later rules establish effect binding.

## R02

For a source that may synchronously emit cached events during startup, establish the attempt's admission eligibility before starting it. Subsequent streaming events remain subject to that attempt's eligibility.

**O / documented_requirement**: Initial reception must be established before startup can synchronously emit; current start-before-listen is the defect, not policy.

- [task.md:2](/home/sribd/Downloads/wangshu/temporal-contract-analyzer/research/transfer-progress-evolution-locked-applicability-20261109_102520/training/inputs/task.md:2) — packet arrives. Restore the initial progress update without changing the public
- [README.md:47](/home/sribd/Downloads/wangshu/temporal-contract-analyzer/research/transfer-progress-evolution-locked-applicability-20261109_102520/training/inputs/source/README.md:47) — emit its cached progress event; further progress events arrive on the same target.
- [progress.js:9](/home/sribd/Downloads/wangshu/temporal-contract-analyzer/research/transfer-progress-evolution-locked-applicability-20261109_102520/training/inputs/source/src/progress.js:9) —   feed.start();
- [progress.js:10](/home/sribd/Downloads/wangshu/temporal-contract-analyzer/research/transfer-progress-evolution-locked-applicability-20261109_102520/training/inputs/source/src/progress.js:10) —   feed.target.addEventListener("progress", listener);

**L / documented_requirement**: Subsequent events retain the subscription/visit admission boundary.

- [README.md:56](/home/sribd/Downloads/wangshu/temporal-contract-analyzer/research/transfer-progress-evolution-locked-applicability-20261109_102520/training/inputs/source/README.md:56) — accepts no new progress events. Removing a listener does not retract a decode
- [README.md:50](/home/sribd/Downloads/wangshu/temporal-contract-analyzer/research/transfer-progress-evolution-locked-applicability-20261109_102520/training/inputs/source/README.md:50) — by multiple panel visits. Each selected or retried attempt starts one subscription.

Review boundary: Not R: listener-before-start ordering is explicitly excluded from extra readiness labeling.

## R03

Once a visit retires, stop admitting subsequent events even if the cleanup or removal capability has not yet returned. This restriction must not depend on deferred physical cleanup.

**O / preservation_inference**: Reentrant startup can retire a visit before the cleanup capability is returned; physical cleanup cannot supply the earlier logical boundary.

- [README.md:58](/home/sribd/Downloads/wangshu/temporal-contract-analyzer/research/transfer-progress-evolution-locked-applicability-20261109_102520/training/inputs/source/README.md:58) — new visits remain live. `showProgress` may synchronously select or hide through
- [transfer.js:5](/home/sribd/Downloads/wangshu/temporal-contract-analyzer/research/transfer-progress-evolution-locked-applicability-20261109_102520/training/inputs/source/src/transfer.js:5) —   let stopProgress = () => {};
- [transfer.js:12](/home/sribd/Downloads/wangshu/temporal-contract-analyzer/research/transfer-progress-evolution-locked-applicability-20261109_102520/training/inputs/source/src/transfer.js:12) —     stopProgress = watchTransferProgress(file.progressFeed, progress.receive, progress.record);

**L / documented_requirement**: Retirement ends new-event admission even while physical cleanup is unavailable.

- [README.md:56](/home/sribd/Downloads/wangshu/temporal-contract-analyzer/research/transfer-progress-evolution-locked-applicability-20261109_102520/training/inputs/source/README.md:56) — accepts no new progress events. Removing a listener does not retract a decode
- [README.md:55](/home/sribd/Downloads/wangshu/temporal-contract-analyzer/research/transfer-progress-evolution-locked-applicability-20261109_102520/training/inputs/source/README.md:55) — finishes, including work accepted before the visit closes. A retired visit
- [transfer.js:5](/home/sribd/Downloads/wangshu/temporal-contract-analyzer/research/transfer-progress-evolution-locked-applicability-20261109_102520/training/inputs/source/src/transfer.js:5) —   let stopProgress = () => {};

Review boundary: No B deadline for finishing accepted decoding or audit is introduced.

## R04

For an event admitted before retirement, retain its audit exactly once when decoding settles. That settlement must not authorize the retired visit to admit new events or produce visible progress.

**L / documented_requirement**: Accepted decode may finish after retirement while visible output and new admission remain invalid.

- [README.md:55](/home/sribd/Downloads/wangshu/temporal-contract-analyzer/research/transfer-progress-evolution-locked-applicability-20261109_102520/training/inputs/source/README.md:55) — finishes, including work accepted before the visit closes. A retired visit
- [README.md:56](/home/sribd/Downloads/wangshu/temporal-contract-analyzer/research/transfer-progress-evolution-locked-applicability-20261109_102520/training/inputs/source/README.md:56) — accepts no new progress events. Removing a listener does not retract a decode
- [README.md:57](/home/sribd/Downloads/wangshu/temporal-contract-analyzer/research/transfer-progress-evolution-locked-applicability-20261109_102520/training/inputs/source/README.md:57) — that already started. Closing or replacing the visit stops visible progress;

**I / source_fact**: The retained audit callback binds file and attempt before later decoding completes across retirement.

- [queue.js:12](/home/sribd/Downloads/wangshu/temporal-contract-analyzer/research/transfer-progress-evolution-locked-applicability-20261109_102520/training/inputs/source/src/queue.js:12) — record(frame) { state.recordProgress({ fileId: visit.file.id, attemptId, frame }); },
- [README.md:55](/home/sribd/Downloads/wangshu/temporal-contract-analyzer/research/transfer-progress-evolution-locked-applicability-20261109_102520/training/inputs/source/README.md:55) — finishes, including work accepted before the visit closes. A retired visit

**A / documented_requirement**: Each already accepted event has an explicit exactly-once retained audit obligation.

- [README.md:54](/home/sribd/Downloads/wangshu/temporal-contract-analyzer/research/transfer-progress-evolution-locked-applicability-20261109_102520/training/inputs/source/README.md:54) — sink. Every accepted progress event is recorded exactly once when decoding
- [README.md:55](/home/sribd/Downloads/wangshu/temporal-contract-analyzer/research/transfer-progress-evolution-locked-applicability-20261109_102520/training/inputs/source/README.md:55) — finishes, including work accepted before the visit closes. A retired visit
- [README.md:62](/home/sribd/Downloads/wangshu/temporal-contract-analyzer/research/transfer-progress-evolution-locked-applicability-20261109_102520/training/inputs/source/README.md:62) — for audit remains retained. Preserve these adapter interfaces.

## R05

After synchronous reentry, the new visit retains its own UI and cancellation resources. Subsequent settlement or cleanup of the old visit must not take ownership from the new one. Preserve existing retry, cancellation and entry-bound record semantics.

**O / documented_requirement**: Older continuations must respect navigation performed synchronously by cancellation/feedback.

- [README.md:19](/home/sribd/Downloads/wangshu/temporal-contract-analyzer/research/transfer-progress-evolution-locked-applicability-20261109_102520/training/inputs/source/README.md:19) — host's `onCancel` observer before returning. That observer may select another
- [README.md:21](/home/sribd/Downloads/wangshu/temporal-contract-analyzer/research/transfer-progress-evolution-locked-applicability-20261109_102520/training/inputs/source/README.md:21) — immediately starts its own transfer. The newer visit must retain its view and

**L / documented_requirement**: Old cleanup must not invalidate the new visit or its resource permissions.

- [README.md:21](/home/sribd/Downloads/wangshu/temporal-contract-analyzer/research/transfer-progress-evolution-locked-applicability-20261109_102520/training/inputs/source/README.md:21) — immediately starts its own transfer. The newer visit must retain its view and
- [README.md:57](/home/sribd/Downloads/wangshu/temporal-contract-analyzer/research/transfer-progress-evolution-locked-applicability-20261109_102520/training/inputs/source/README.md:57) — that already started. Closing or replacing the visit stops visible progress;

**I / documented_requirement**: Entry-bound retry/audit effects and exact current-visit checks keep old and new effects attached to their owners.

- [README.md:12](/home/sribd/Downloads/wangshu/temporal-contract-analyzer/research/transfer-progress-evolution-locked-applicability-20261109_102520/training/inputs/source/README.md:12) — An accepted retry always belongs to the file and visit present at entry, creates
- [queue.js:12](/home/sribd/Downloads/wangshu/temporal-contract-analyzer/research/transfer-progress-evolution-locked-applicability-20261109_102520/training/inputs/source/src/queue.js:12) — record(frame) { state.recordProgress({ fileId: visit.file.id, attemptId, frame }); },
- [queue.js:14](/home/sribd/Downloads/wangshu/temporal-contract-analyzer/research/transfer-progress-evolution-locked-applicability-20261109_102520/training/inputs/source/src/queue.js:14) — if (state.current === visit) state.showProgress({ fileId: visit.file.id, attemptId, frame });

## R06

Test subsequent events from the same source after synchronous navigation and before the outer startup call returns. Cover hiding, switching and reopening the same source separately. Independently check rejection by the retired visit, delayed audit of previously admitted events, and valid visible progress for the current visit. Cleanup tests performed only after return do not cover this window.

**O / documented_requirement**: Verify emissions inside the outer synchronous startup/reentry window, not merely after return.

- [README.md:47](/home/sribd/Downloads/wangshu/temporal-contract-analyzer/research/transfer-progress-evolution-locked-applicability-20261109_102520/training/inputs/source/README.md:47) — emit its cached progress event; further progress events arrive on the same target.
- [README.md:58](/home/sribd/Downloads/wangshu/temporal-contract-analyzer/research/transfer-progress-evolution-locked-applicability-20261109_102520/training/inputs/source/README.md:58) — new visits remain live. `showProgress` may synchronously select or hide through
- [transfer.js:12](/home/sribd/Downloads/wangshu/temporal-contract-analyzer/research/transfer-progress-evolution-locked-applicability-20261109_102520/training/inputs/source/src/transfer.js:12) —     stopProgress = watchTransferProgress(file.progressFeed, progress.receive, progress.record);

**L / documented_requirement**: Separately verify rejection by retired visits and live current display.

- [README.md:56](/home/sribd/Downloads/wangshu/temporal-contract-analyzer/research/transfer-progress-evolution-locked-applicability-20261109_102520/training/inputs/source/README.md:56) — accepts no new progress events. Removing a listener does not retract a decode
- [README.md:57](/home/sribd/Downloads/wangshu/temporal-contract-analyzer/research/transfer-progress-evolution-locked-applicability-20261109_102520/training/inputs/source/README.md:57) — that already started. Closing or replacing the visit stops visible progress;

**I / documented_requirement**: Reopening identical data creates a different visit; audit remains bound to the original attempt.

- [README.md:7](/home/sribd/Downloads/wangshu/temporal-contract-analyzer/research/transfer-progress-evolution-locked-applicability-20261109_102520/training/inputs/source/README.md:7) — opens a new visit, including when the exact same file object is selected again.
- [queue.js:12](/home/sribd/Downloads/wangshu/temporal-contract-analyzer/research/transfer-progress-evolution-locked-applicability-20261109_102520/training/inputs/source/src/queue.js:12) — record(frame) { state.recordProgress({ fileId: visit.file.id, attemptId, frame }); },
- [queue.js:14](/home/sribd/Downloads/wangshu/temporal-contract-analyzer/research/transfer-progress-evolution-locked-applicability-20261109_102520/training/inputs/source/src/queue.js:14) — if (state.current === visit) state.showProgress({ fileId: visit.file.id, attemptId, frame });

**A / documented_requirement**: Validation must retain audit for events accepted before the transition.

- [README.md:54](/home/sribd/Downloads/wangshu/temporal-contract-analyzer/research/transfer-progress-evolution-locked-applicability-20261109_102520/training/inputs/source/README.md:54) — sink. Every accepted progress event is recorded exactly once when decoding
- [README.md:55](/home/sribd/Downloads/wangshu/temporal-contract-analyzer/research/transfer-progress-evolution-locked-applicability-20261109_102520/training/inputs/source/README.md:55) — finishes, including work accepted before the visit closes. A retired visit

## R07

Limit this repair to progress-admission timing and lifecycle boundaries. Do not expand records or public interfaces, or change shared-source reuse, independent workspaces, retry, cancellation, navigation, resource ownership or the audit policy for already-admitted events.

**L / documented_requirement**: Scope preserves source reuse, cancellation and independent lifecycle ownership.

- [README.md:50](/home/sribd/Downloads/wangshu/temporal-contract-analyzer/research/transfer-progress-evolution-locked-applicability-20261109_102520/training/inputs/source/README.md:50) — by multiple panel visits. Each selected or retried attempt starts one subscription.
- [README.md:21](/home/sribd/Downloads/wangshu/temporal-contract-analyzer/research/transfer-progress-evolution-locked-applicability-20261109_102520/training/inputs/source/README.md:21) — immediately starts its own transfer. The newer visit must retain its view and

**I / documented_requirement**: Preserve the original entry-bound record/attempt attribution rather than retarget it.

- [README.md:12](/home/sribd/Downloads/wangshu/temporal-contract-analyzer/research/transfer-progress-evolution-locked-applicability-20261109_102520/training/inputs/source/README.md:12) — An accepted retry always belongs to the file and visit present at entry, creates
- [queue.js:12](/home/sribd/Downloads/wangshu/temporal-contract-analyzer/research/transfer-progress-evolution-locked-applicability-20261109_102520/training/inputs/source/src/queue.js:12) — record(frame) { state.recordProgress({ fileId: visit.file.id, attemptId, frame }); },

**A / documented_requirement**: The exclusion explicitly preserves the audit policy for already admitted events.

- [README.md:54](/home/sribd/Downloads/wangshu/temporal-contract-analyzer/research/transfer-progress-evolution-locked-applicability-20261109_102520/training/inputs/source/README.md:54) — sink. Every accepted progress event is recorded exactly once when decoding
- [README.md:62](/home/sribd/Downloads/wangshu/temporal-contract-analyzer/research/transfer-progress-evolution-locked-applicability-20261109_102520/training/inputs/source/README.md:62) — for audit remains retained. Preserve these adapter interfaces.

Review boundary: Generic interface preservation is not counted as an additional temporal label.

## Labels not established here

- R: No separate data/API/connectivity readiness prerequisite; initial listener order is O.
- B: Accepted decoding/audit may complete after retirement; no required completion barrier is asserted.
- F: Suppression concerns visit/attempt retirement and identity, not competing revisions within a retained owner.

## Decision

The separate `expert-decision-template.json` has no name or approval. Fill it only after a real review, including labels and applicability, then submit the exact candidate digest through `experience-memory expert-review`. Do not approve on behalf of another person.

No whole-task result, gain, loss or classifier accuracy is claimed for this taxonomy migration. Historical outcomes retain their original conditions.
