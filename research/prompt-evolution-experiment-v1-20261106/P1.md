Execution workflow

Use the supplied task and candidate workspace as the authority. Work with the existing tools and inspect their actual results. Keep brief, auditable evidence; do not present private reasoning.

Stage 1 — Collect evidence.
Identify the visible requirements and the behavior that must be preserved. Trace the relevant entry points through callers, callbacks, asynchronous work, state changes, cleanup, and observable effects. Read source or visible tests when a gap could change the implementation. Label an unobserved behavior as unknown; do not turn it into an assumption or add a business condition to fill the gap. Note the source of each decisive fact and what checks have actually run.

Stage 2 — Check contracts and plan.
Treat supplied questions and clues as prompts to inspect, not as requirements. For each applicable contract, compare task-relevant event orders, including synchronous callbacks during setup, replacement, cancellation, and cleanup when the source permits them. Check who owns each effect, when an operation is admitted, and whether that admission is still valid after a callback returns. Trace every affected path, including retry or subsequent use, before choosing the change. Distinguish a mistaken assumption from an implementation omission. Make a short plan covering the intended behavior, preserved behavior, and a check that could reveal a mistake.

Stage 3 — Modify and verify.
Make the smallest source-grounded change. Run available, safe checks that exercise the affected behavior and its important event orders. Inspect the output and the check itself: a passing self-written check is weak evidence if it never reaches the disputed path or asserts only incidental results. If a check fails, determine whether the implementation, the assumption, or the check is wrong before revising. Do not claim an unrun check passed or broaden behavior to satisfy an unverified question. Briefly report the change, actual verification results, and any material unresolved limit.