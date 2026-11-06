```text
# Temporal contract skill: ownership, completion, and effects

Purpose: Complete the original maintenance task. Use this skill to check whether asynchronous work, synchronous callbacks, or changing ownership affect the requested behavior. It is an aid to the repair, not a separate task or a new specification. Let the task and visible project evidence determine the contract.

## 1. Decide whether it applies

Look for work that can finish after its initiating access, operation, or consumer changes; a callback that can change ownership while a call is still running; a source that can emit during setup; or several effects produced from one result. If none applies, briefly record why and continue the maintenance task.

## 2. Gather the contract before editing

Inspect the task, entry point, producer or decoder, subscription and completion paths, ownership transitions, cancellation or release behavior, and every affected consumer. Follow calls far enough to see what happens before and after a callback returns. Check adjacent consumers of shared helpers and the public interface. Cite source locations for consequential claims.

Keep four kinds of statements distinct: task requirements, observed source behavior, hypotheses to test, and evidence that is unavailable. Do not infer a guarantee from a function name, an apparent intention, or a passing check. Do not add formats or behaviors that the task and source do not support.

## 3. Trace identities and effects separately

Where the code distinguishes them, identify the resource, access or visit, physical attempt, emitted input, decoded result, and accepted work. Note when each identity is created, captured, replaced, retired, and compared.

List each effect separately, such as history, audit, queue record, notice, current display, or background work. For each, determine:

- Which event or result produces it?
- Which identity owns it?
- Must it survive a later close, switch, retry, or replacement?
- Is its order based on input arrival, completion, or another source rule?
- Can a callback reenter the system before the surrounding operation finishes?

A guard that is right for the current display may wrongly suppress a durable record. Conversely, a result that remains valid for history may no longer be valid for the current consumer. Treat these as project-specific conclusions, not universal rules.

Determine what cancellation actually does: stop future inputs, stop work already started, suppress a consumer, or some combination. Check the implementation and its call order, including synchronous callbacks triggered by cleanup. Do not equate release of a listener with cancellation of a pending decode or other in-flight work without evidence.

## 4. Compare concrete event orders

Before settling on a change, write down the expected effects for relevant orders supported by visible APIs:

- Ordinary start and completion, including an immediate or cached input.
- A later input during continued use.
- Close, switch, or disposal before an in-flight result completes.
- Reuse of the same resource under a new access.
- Retry or replacement that changes the attempt while retaining an access.
- Synchronous reentry during startup, cancellation, release, or an effect callback.
- Two ordered full results completing in arrival order and in reverse order.

Track stored effects and current visible effects independently. Include records and notices around ownership changes when the task says to preserve them. If a source emits during setup, examine whether registration timing both receives that input and remains safe when the input or cleanup callback reenters. Do not invent a frame schema or assume every result has an intrinsic sequence number.

## 5. Repair within the supported scope

Implement the smallest change that satisfies the original task and the observed contracts. Preserve unrelated public interfaces, other consumers of shared helpers, and existing queue, audit, navigation, retry, and cleanup behavior where the task requires it. Avoid broad guards, cancellation, deduplication, or ordering rules unless each affected effect warrants them.

Background obligations, rollback, permission withdrawal, or a dependency that truly suppresses completion can change the conclusion. Seek visible evidence; otherwise mark the point unresolved. Do not impose persistence after cancellation or access-based invalidation on every project.

## 6. Verify the actual behavior

Use available project checks and focused tests or controlled probes for the relevant event orders above. Assert each effect independently, including its owner and timing. Exercise reentry and replacement when supported by the source; a normal completion test does not cover them. Check adjacent consumers and public behavior touched by a shared helper. Inspect real output, investigate failures, and revise the repair when warranted.

Choose validation commands that fit the workspace. A syntax check proves only syntax; a successful self-written harness proves only the paths it drove. A failed check remains failed until its cause is understood and an appropriate rerun passes. Record checks that could not run and why. Complete the maintenance change, or explain with evidence why no change is needed or what prevents completion. A contract discussion alone is not completion.
```