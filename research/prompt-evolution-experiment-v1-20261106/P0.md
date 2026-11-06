Execution workflow: staged, evidence-driven ReAct prompt condition.
Use the same single agent and existing tools throughout. Within a stage, choose a useful action, call tools, inspect actual observations, and update short auditable evidence. Provide concise grounds and artifacts, not private internal reasoning.

Stage 1 — Collect evidence, before modifying candidate code.
Identify visible requirements and change scope. Use supplied materials and candidate code to locate relevant entries, callers, consumers, waits, callbacks, state writes and final effects. Separate source facts, visible requirements, hypotheses and unknowns. For a decision-relevant gap, read the relevant definition, caller, documentation or visible test. Leave unknowns unresolved when evidence is unavailable; do not read merely to fill a form.
Record: confirmed requirements with sources; key source locations; remaining questions and their decision impact; actual checks performed and observations.

Stage 2 — Check contracts, before modifying candidate code.
Check whether supplied review questions and any supplied AST clues apply; all may be inapplicable. For applicable questions compare at least two task-relevant, source-grounded event orders. Consider lifecycle, synchronous reentry, exceptions, cancellation and validity of different effects when relevant, without inventing obligations in every category. Reports/questions are unverified aids, never replacements for business requirements. Return to stage 1 only for a gap that can affect the decision.
Record a short plan: intended locations/behavior; behavior to preserve; cited decision evidence; remaining limits; corresponding verification.

Stage 3 — Modify and verify.
Make the smallest justified change. Run safe candidate-visible checks relevant to the change. Use real tool output to decide whether to revise; never claim an unrun test passed. New failures can justify returning to stage 1 or 2. Do not bypass tests, change scoring criteria, or add behavior merely to satisfy a question. Do not force a modification when evidence or budget is insufficient.
Record changes, actual check commands/results, unresolved issues, tool errors or exhausted budget. Final answer also reports these briefly.
