# Temporal contract skill: result ownership and effect validity

Purpose: complete the original maintenance task when asynchronous work, callbacks, retries, or changing consumers affect when a result may be used. This skill guides investigation and repair; it does not add product requirements. The original task and visible project evidence determine the contract.

## 1. Decide applicability

Look for work that can finish after its initiating access, operation, or consumer changes; callbacks that can change ownership while another call is running; or multiple effects that may have different validity rules. Examples include history and current display, durable work and transient UI, or a scheduled retry and an in-flight request.

If none apply, briefly record the evidence for non-applicability and continue the maintenance task.

## 2. Establish the contract from source

Read the task, entry point, real producer or dependency, decoder or completion callback, ownership transitions, cancellation and cleanup paths, and every affected effect consumer. Inspect adjacent consumers of any shared helper. Retrieval excerpts are leads, not proof that the relevant path is complete.

For each conclusion, distinguish:

- **Requirement:** what the task explicitly asks to change or preserve.
- **Source fact:** what visible code or documentation establishes, with file and line.
- **Hypothesis:** a possible behavior to test or investigate.
- **Unknown:** a guarantee or outcome the available evidence cannot establish.

Do not derive a guarantee from a function name, a similar component, or an expected test result. Similar code can reveal an API or a behavior to investigate without making its whole lifecycle contract authoritative.

## 3. Map identities, events, and effects

Identify only the identities the project actually distinguishes: resource, access or visit, physical operation or attempt, scheduled callback, and accepted result or work. Trace where each is captured, replaced, retired, and checked. Determine whether cancellation stops future inputs, cancels scheduled work, aborts work already started, or merely hides a consumer. Check whether a callback can run synchronously during registration, startup, scheduling, cancellation, or listener removal.

Make a compact event-order table before editing. Include the initiating event, any callback or completion, ownership changes, and each resulting effect. For each effect, state its source-supported validity rule independently. A result may remain valid for one effect after it becomes invalid for another. Do not apply a single cancellation or freshness guard to all effects without evidence.

Where full results can complete out of order, distinguish input order from completion order and identify which order governs each effect. Keep ordering state scoped to the owner or stream established by the source. Do not invent a result schema or treat a partial delta as a full replacement unless the source does.

## 4. Compare concrete orders

Use controllable APIs visible in the project to examine applicable sequences:

- Ordinary startup and later input, including any synchronous initial callback.
- Completion before and after close, switch, replacement, retry, or disposal.
- Reuse of the same resource under a new access or operation.
- Normal and reversed completion order for independently pending results.
- Synchronous reentry from startup, scheduling, cancellation, or cleanup callbacks when supported.

For every sequence, observe durable or recorded effects, current or visible effects, notices, scheduled work, and cleanup separately where they exist. Check the identities attached to each effect, not just the final snapshot. Preserve normal streaming and adjacent consumers of shared APIs.

## 5. Repair the supported behavior

Implement the smallest change that satisfies the task and the established contract. Keep public interfaces and unrelated behavior intact. Treat a change to registration or callback timing as a possible source of reentry: after any external call, reassess whether the original owner still controls subsequent work. Likewise, when a pending result settles, decide each effect’s validity at the point it is applied.

Do not impose persistence after cancellation, suppress all late results, or cancel an access merely because those rules would simplify the code. Background obligations, rollback, permission withdrawal, and dependencies that truly suppress completion can require different behavior. Establish such rules from evidence or leave them unresolved.

## 6. Verify the whole task

Run relevant candidate-visible checks and inspect their actual output. Add focused checks for the event orders and separate effects identified above when the project permits it. Test the preserved behaviors named in the task, including adjacent consumers and lifecycle combinations, rather than only the newly repaired happy path. A passing local harness establishes only the paths it drove.

If a check fails, determine whether it exposes a code defect, a mistaken contract assumption, an invalid expectation, or an environment limitation. Revise the repair or the check accordingly and rerun the affected path. Do not discard a failure merely because a later, narrower check passes. Report failed, unavailable, and unrun checks accurately. Avoid relying on a repository or runtime tool that the environment does not provide.

Finish with the maintenance change, or explain with source evidence why no change is needed or why the task remains incomplete. A contract discussion, a successful smoke check, or a syntactic check alone does not complete the original repair.