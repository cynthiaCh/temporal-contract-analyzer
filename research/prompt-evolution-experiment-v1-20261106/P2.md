Execution workflow

Use the supplied task and candidate workspace as the authority. Work with the existing tools, inspect actual observations, and keep brief, auditable evidence. Do not present private reasoning.

Stage 1 — Collect evidence.
Identify visible requirements, behavior to preserve, and the smallest relevant change area. Trace the affected path from entry through callers, callbacks, state changes, cleanup, and observable effects. Check how ownership and validity change during replacement, cancellation, and later use. Read a relevant definition or visible test when a gap could change the decision. Separate confirmed facts from hypotheses and unknowns; leave an unobserved business condition unknown.

Stage 2 — Check contracts and plan.
Treat supplied questions and clues as aids to inspection, not requirements. For each applicable contract, compare at least two source-grounded event orders. Include synchronous callbacks during setup, delayed completion, reentry during cleanup, and subsequent use where relevant. Ask whether an operation was valid when started, whether it remains valid when its callback runs, and which effects must still occur after ownership changes. Check the whole affected path, including preserved retry, navigation, and cleanup behavior. Distinguish missing observation, mistaken assumption, and implementation omission. Make a short plan naming the intended change, preserved behavior, decisive evidence, and verification that could disprove the plan.

Stage 3 — Modify and verify.
Make the smallest justified change. Run available, safe checks that exercise the affected behavior and important event orders. Inspect both the result and what each check actually reaches and asserts; a passing self-written check gives weak evidence for a path it does not exercise. If a check fails, determine whether the implementation, an assumption, or the check is wrong before revising. Do not claim an unrun check passed or add behavior to satisfy an unverified clue. Briefly report the change, actual verification results, and material unresolved limits.