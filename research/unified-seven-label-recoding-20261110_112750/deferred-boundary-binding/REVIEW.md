# Expert review: deferred-boundary-binding

Status: AI-assisted label recoding, pending real expert acceptance.

Parent: `59da0bba42a06a38123d9f2ed3fda2a7a1724a9e63e74aafe733940d8d09aad1`

Candidate: `c511b37c5e36aae818d0bde18ae780b3260b93f17a5efcc9f2b4831d397ef196`

Candidate labels: O, B, L, I, A. Rule text and applicability are unchanged.

Check both each rule and its proposed labels against the actual source; a valid quotation is not automatic semantic support. No new repair replay has occurred.

## R01

Apply this guidance where edits are deferred, accepted text must be durable before a departure or submission returns, accepted actions retain entry values, synchronous callbacks may reenter, and durable results have a different lifetime from visible feedback.

**O / source_fact**: Applicability includes synchronous storage/queue callbacks that can reenter.

- [workflow.py:29](/home/sribd/Downloads/wangshu/temporal-contract-analyzer/research/review-confirmation-lowpass-train-test-20261109_225210/training/inputs/source/src/workflow.py:29) —                 listener(event)
- [README.md:5](/home/sribd/Downloads/wangshu/temporal-contract-analyzer/research/review-confirmation-lowpass-train-test-20261109_225210/training/inputs/source/README.md:5) — The public API is synchronous: open(id), edit(text), close(), submit(), dispose().

**B / preservation_inference**: Boundary durability is the inherited preservation inference from synchronous APIs, restored persisted text and original immediate writes.

- [task.md:1](/home/sribd/Downloads/wangshu/temporal-contract-analyzer/research/review-confirmation-lowpass-train-test-20261109_225210/training/inputs/task.md:1) — Preserve other supported behavior and the synchronous public interfaces.
- [README.md:5](/home/sribd/Downloads/wangshu/temporal-contract-analyzer/research/review-confirmation-lowpass-train-test-20261109_225210/training/inputs/source/README.md:5) — The public API is synchronous: open(id), edit(text), close(), submit(), dispose().
- [README.md:6](/home/sribd/Downloads/wangshu/temporal-contract-analyzer/research/review-confirmation-lowpass-train-test-20261109_225210/training/inputs/source/README.md:6) — Returning to a document creates a fresh editor visit and restores persisted text.
- [workflow.py:122](/home/sribd/Downloads/wangshu/temporal-contract-analyzer/research/review-confirmation-lowpass-train-test-20261109_225210/training/inputs/source/src/workflow.py:122) —             self.env.write(self.current.id, text)

**L / documented_requirement**: Durable results and the visit-scoped confirmation have different valid lifetimes.

- [README.md:21](/home/sribd/Downloads/wangshu/temporal-contract-analyzer/research/review-confirmation-lowpass-train-test-20261109_225210/training/inputs/source/README.md:21) — An outlet acquires the visit active when binding is called; it cannot infer an earlier action from a receipt.
- [workflow.py:85](/home/sribd/Downloads/wangshu/temporal-contract-analyzer/research/review-confirmation-lowpass-train-test-20261109_225210/training/inputs/source/src/workflow.py:85) —     def active(self):return self.owner is not None and self.owner is self.current()

**I / documented_requirement**: Accepted actions bind their original selection/text and the outlet captures an exact visit.

- [workflow.py:134](/home/sribd/Downloads/wangshu/temporal-contract-analyzer/research/review-confirmation-lowpass-train-test-20261109_225210/training/inputs/source/src/workflow.py:134) —         snapshot = dict(id=visit.id, text=visit.text)
- [README.md:21](/home/sribd/Downloads/wangshu/temporal-contract-analyzer/research/review-confirmation-lowpass-train-test-20261109_225210/training/inputs/source/README.md:21) — An outlet acquires the visit active when binding is called; it cannot infer an earlier action from a receipt.

Review boundary: B is not claimed as a literal README deadline. The multi-source preservation inference remains open to expert scrutiny.

## R02

For each editing burst, retain only its latest value until the quiet interval expires. When accepted deferred text must settle at a departure boundary, bind the write to the departing document, consume that batch before invoking synchronous work, and let any nested navigation or later edit remain authoritative.

**O / source_fact**: Consume the old deferred batch before synchronous callbacks so reentrant input/navigation retains authority.

- [workflow.py:73](/home/sribd/Downloads/wangshu/temporal-contract-analyzer/research/review-confirmation-lowpass-train-test-20261109_225210/training/inputs/source/src/workflow.py:73) —         self.handle = self.pending = None
- [workflow.py:75](/home/sribd/Downloads/wangshu/temporal-contract-analyzer/research/review-confirmation-lowpass-train-test-20261109_225210/training/inputs/source/src/workflow.py:75) —             self.work(value)
- [workflow.py:29](/home/sribd/Downloads/wangshu/temporal-contract-analyzer/research/review-confirmation-lowpass-train-test-20261109_225210/training/inputs/source/src/workflow.py:29) —                 listener(event)

**B / preservation_inference**: Accepted deferred text must preserve original durability across the synchronous departure boundary.

- [task.md:1](/home/sribd/Downloads/wangshu/temporal-contract-analyzer/research/review-confirmation-lowpass-train-test-20261109_225210/training/inputs/task.md:1) — Preserve other supported behavior and the synchronous public interfaces.
- [README.md:5](/home/sribd/Downloads/wangshu/temporal-contract-analyzer/research/review-confirmation-lowpass-train-test-20261109_225210/training/inputs/source/README.md:5) — The public API is synchronous: open(id), edit(text), close(), submit(), dispose().
- [README.md:6](/home/sribd/Downloads/wangshu/temporal-contract-analyzer/research/review-confirmation-lowpass-train-test-20261109_225210/training/inputs/source/README.md:6) — Returning to a document creates a fresh editor visit and restores persisted text.
- [workflow.py:122](/home/sribd/Downloads/wangshu/temporal-contract-analyzer/research/review-confirmation-lowpass-train-test-20261109_225210/training/inputs/source/src/workflow.py:122) —             self.env.write(self.current.id, text)

**I / preservation_inference**: A departing batch retains its original document binding across handoff/reentry.

- [workflow.py:115](/home/sribd/Downloads/wangshu/temporal-contract-analyzer/research/review-confirmation-lowpass-train-test-20261109_225210/training/inputs/source/src/workflow.py:115) —         task = Trailing(self.env, 120, lambda text: self.env.write(key, text))
- [README.md:6](/home/sribd/Downloads/wangshu/temporal-contract-analyzer/research/review-confirmation-lowpass-train-test-20261109_225210/training/inputs/source/README.md:6) — Returning to a document creates a fresh editor visit and restores persisted text.

**A / documented_requirement**: Each editing burst explicitly retains only its latest value while later bursts remain usable.

- [task.md:1](/home/sribd/Downloads/wangshu/temporal-contract-analyzer/research/review-confirmation-lowpass-train-test-20261109_225210/training/inputs/task.md:1) — after a 120 ms quiet interval write only the latest text in that editing burst.
- [task.md:1](/home/sribd/Downloads/wangshu/temporal-contract-analyzer/research/review-confirmation-lowpass-train-test-20261109_225210/training/inputs/task.md:1) — Preserve other supported behavior and the synchronous public interfaces.

## R03

On an accepted submission, fix the selected document and text at action entry. Ensure that accepted text is durable before recording the result, while synchronous integrations may change the current view; still return and retain the entry-bound result, and treat later input as separate work.

**O / preservation_inference**: Submission proceeds across synchronous integrations without retargeting accepted work.

- [workflow.py:29](/home/sribd/Downloads/wangshu/temporal-contract-analyzer/research/review-confirmation-lowpass-train-test-20261109_225210/training/inputs/source/src/workflow.py:29) —                 listener(event)
- [workflow.py:134](/home/sribd/Downloads/wangshu/temporal-contract-analyzer/research/review-confirmation-lowpass-train-test-20261109_225210/training/inputs/source/src/workflow.py:134) —         snapshot = dict(id=visit.id, text=visit.text)
- [task.md:1](/home/sribd/Downloads/wangshu/temporal-contract-analyzer/research/review-confirmation-lowpass-train-test-20261109_225210/training/inputs/task.md:1) — Preserve other supported behavior and the synchronous public interfaces.

**B / preservation_inference**: Persist-before-result is inherited preservation reasoning from original immediate writes, synchronous commands and durable capture.

- [task.md:1](/home/sribd/Downloads/wangshu/temporal-contract-analyzer/research/review-confirmation-lowpass-train-test-20261109_225210/training/inputs/task.md:1) — Preserve other supported behavior and the synchronous public interfaces.
- [README.md:5](/home/sribd/Downloads/wangshu/temporal-contract-analyzer/research/review-confirmation-lowpass-train-test-20261109_225210/training/inputs/source/README.md:5) — The public API is synchronous: open(id), edit(text), close(), submit(), dispose().
- [workflow.py:122](/home/sribd/Downloads/wangshu/temporal-contract-analyzer/research/review-confirmation-lowpass-train-test-20261109_225210/training/inputs/source/src/workflow.py:122) —             self.env.write(self.current.id, text)
- [workflow.py:44](/home/sribd/Downloads/wangshu/temporal-contract-analyzer/research/review-confirmation-lowpass-train-test-20261109_225210/training/inputs/source/src/workflow.py:44) —         receipt = Receipt(value['id'], value['text'])

**I / documented_requirement**: Submission fixes the entry document/text before later transitions.

- [workflow.py:134](/home/sribd/Downloads/wangshu/temporal-contract-analyzer/research/review-confirmation-lowpass-train-test-20261109_225210/training/inputs/source/src/workflow.py:134) —         snapshot = dict(id=visit.id, text=visit.text)
- [workflow.py:44](/home/sribd/Downloads/wangshu/temporal-contract-analyzer/research/review-confirmation-lowpass-train-test-20261109_225210/training/inputs/source/src/workflow.py:44) —         receipt = Receipt(value['id'], value['text'])

**A / preservation_inference**: Accepted results are returned and retained as distinct durable receipts.

- [README.md:16](/home/sribd/Downloads/wangshu/temporal-contract-analyzer/research/review-confirmation-lowpass-train-test-20261109_225210/training/inputs/source/README.md:16) — injected interfaces. A submission returns the queue receipt, or null when no
- [workflow.py:45](/home/sribd/Downloads/wangshu/temporal-contract-analyzer/research/review-confirmation-lowpass-train-test-20261109_225210/training/inputs/source/src/workflow.py:45) —         self.receipts.append(receipt)

## R04

Keep visible confirmation separate from the durable accepted result: show it only while the exact accepting visit remains current. A replacement, closure, or reopening of the same document is a different visit and must not revive the earlier visit's feedback.

**L / documented_requirement**: Visible confirmation is valid only for the exact still-current visit, while the durable result remains independent.

- [README.md:21](/home/sribd/Downloads/wangshu/temporal-contract-analyzer/research/review-confirmation-lowpass-train-test-20261109_225210/training/inputs/source/README.md:21) — An outlet acquires the visit active when binding is called; it cannot infer an earlier action from a receipt.
- [workflow.py:85](/home/sribd/Downloads/wangshu/temporal-contract-analyzer/research/review-confirmation-lowpass-train-test-20261109_225210/training/inputs/source/src/workflow.py:85) —     def active(self):return self.owner is not None and self.owner is self.current()

**I / documented_requirement**: Same-document reopening has a new identity and cannot inherit an earlier outlet.

- [README.md:21](/home/sribd/Downloads/wangshu/temporal-contract-analyzer/research/review-confirmation-lowpass-train-test-20261109_225210/training/inputs/source/README.md:21) — Each opening creates a new identity.
- [README.md:21](/home/sribd/Downloads/wangshu/temporal-contract-analyzer/research/review-confirmation-lowpass-train-test-20261109_225210/training/inputs/source/README.md:21) — An outlet acquires the visit active when binding is called; it cannot infer an earlier action from a receipt.
- [workflow.py:85](/home/sribd/Downloads/wangshu/temporal-contract-analyzer/research/review-confirmation-lowpass-train-test-20261109_225210/training/inputs/source/src/workflow.py:85) —     def active(self):return self.owner is not None and self.owner is self.current()

Review boundary: This is not F: eligibility is lost through visit replacement, not a revision race in a retained visit.

## R05

Do not extend this editor maintenance into the adjacent preview: retain its existing quiet interval, discard unpublished preview work when hidden, and allow later preview input to schedule normally. Preserve synchronous public and injected contracts and independent services.

**L / documented_requirement**: The adjacent preview has a separate hide/discard/reuse lifecycle that the persistence fix must preserve.

- [README.md:8](/home/sribd/Downloads/wangshu/temporal-contract-analyzer/research/review-confirmation-lowpass-train-test-20261109_225210/training/inputs/source/README.md:8) — cancels unpublished work and later queries remain usable.
- [task.md:1](/home/sribd/Downloads/wangshu/temporal-contract-analyzer/research/review-confirmation-lowpass-train-test-20261109_225210/training/inputs/task.md:1) — Preserve other supported behavior and the synchronous public interfaces.

Review boundary: Generic interface preservation is not an extra barrier, readiness or freshness label.

## R06

Verify the candidate across quiet bursts, boundary departures, nested navigation, nested editing, submission, confirmation validity, disposal, and preview reuse. Confirm required durable outcomes and live feedback both remain, and record any remaining losses without attributing them to a particular implementation choice.

**O / preservation_inference**: Verification includes nested navigation and editing across synchronous callbacks.

- [workflow.py:29](/home/sribd/Downloads/wangshu/temporal-contract-analyzer/research/review-confirmation-lowpass-train-test-20261109_225210/training/inputs/source/src/workflow.py:29) —                 listener(event)
- [README.md:5](/home/sribd/Downloads/wangshu/temporal-contract-analyzer/research/review-confirmation-lowpass-train-test-20261109_225210/training/inputs/source/README.md:5) — The public API is synchronous: open(id), edit(text), close(), submit(), dispose().
- [task.md:1](/home/sribd/Downloads/wangshu/temporal-contract-analyzer/research/review-confirmation-lowpass-train-test-20261109_225210/training/inputs/task.md:1) — Preserve other supported behavior and the synchronous public interfaces.

**B / preservation_inference**: Verify inherited durable outcomes at departure/submission boundaries, without requiring a unique flush implementation.

- [task.md:1](/home/sribd/Downloads/wangshu/temporal-contract-analyzer/research/review-confirmation-lowpass-train-test-20261109_225210/training/inputs/task.md:1) — Preserve other supported behavior and the synchronous public interfaces.
- [README.md:5](/home/sribd/Downloads/wangshu/temporal-contract-analyzer/research/review-confirmation-lowpass-train-test-20261109_225210/training/inputs/source/README.md:5) — The public API is synchronous: open(id), edit(text), close(), submit(), dispose().
- [README.md:6](/home/sribd/Downloads/wangshu/temporal-contract-analyzer/research/review-confirmation-lowpass-train-test-20261109_225210/training/inputs/source/README.md:6) — Returning to a document creates a fresh editor visit and restores persisted text.
- [workflow.py:122](/home/sribd/Downloads/wangshu/temporal-contract-analyzer/research/review-confirmation-lowpass-train-test-20261109_225210/training/inputs/source/src/workflow.py:122) —             self.env.write(self.current.id, text)

**L / documented_requirement**: Check confirmation and preview validity across closure/disposal/reuse.

- [README.md:8](/home/sribd/Downloads/wangshu/temporal-contract-analyzer/research/review-confirmation-lowpass-train-test-20261109_225210/training/inputs/source/README.md:8) — cancels unpublished work and later queries remain usable.
- [README.md:21](/home/sribd/Downloads/wangshu/temporal-contract-analyzer/research/review-confirmation-lowpass-train-test-20261109_225210/training/inputs/source/README.md:21) — An outlet acquires the visit active when binding is called; it cannot infer an earlier action from a receipt.
- [workflow.py:85](/home/sribd/Downloads/wangshu/temporal-contract-analyzer/research/review-confirmation-lowpass-train-test-20261109_225210/training/inputs/source/src/workflow.py:85) —     def active(self):return self.owner is not None and self.owner is self.current()

**I / documented_requirement**: Check entry-bound accepted data independently of the current visit.

- [workflow.py:134](/home/sribd/Downloads/wangshu/temporal-contract-analyzer/research/review-confirmation-lowpass-train-test-20261109_225210/training/inputs/source/src/workflow.py:134) —         snapshot = dict(id=visit.id, text=visit.text)
- [README.md:21](/home/sribd/Downloads/wangshu/temporal-contract-analyzer/research/review-confirmation-lowpass-train-test-20261109_225210/training/inputs/source/README.md:21) — An outlet acquires the visit active when binding is called; it cannot infer an earlier action from a receipt.

**A / preservation_inference**: Verify latest-only bursts and retained accepted receipts without hiding losses.

- [task.md:1](/home/sribd/Downloads/wangshu/temporal-contract-analyzer/research/review-confirmation-lowpass-train-test-20261109_225210/training/inputs/task.md:1) — after a 120 ms quiet interval write only the latest text in that editing burst.
- [workflow.py:45](/home/sribd/Downloads/wangshu/temporal-contract-analyzer/research/review-confirmation-lowpass-train-test-20261109_225210/training/inputs/source/src/workflow.py:45) —         self.receipts.append(receipt)
- [task.md:1](/home/sribd/Downloads/wangshu/temporal-contract-analyzer/research/review-confirmation-lowpass-train-test-20261109_225210/training/inputs/task.md:1) — Preserve other supported behavior and the synchronous public interfaces.

## Labels not established here

- R: Quiet batching does not establish a separate readiness handshake; the repair also permits required boundary settlement.
- F: No independently supported within-owner competing-result/revision policy is inferred from a field named revision or from visit replacement.

## Decision

The separate `expert-decision-template.json` has no name or approval. Fill it only after a real review, including labels and applicability, then submit the exact candidate digest through `experience-memory expert-review`. Do not approve on behalf of another person.

No whole-task result, gain, loss or classifier accuracy is claimed for this taxonomy migration. Historical outcomes retain their original conditions.
