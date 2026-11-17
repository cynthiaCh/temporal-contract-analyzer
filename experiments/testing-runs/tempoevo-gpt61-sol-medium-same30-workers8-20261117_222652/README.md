# GPT6.1-sol medium same30 full-experience test

User requested the same30 cases tested on GPT6.1-sol medium with8workers. Use the
normal full-experience testing pipeline (explicitly disclosed), not Auto-only.
Reuse the exact original GPT5.6-low30 selection CSV; do not rank/filter cases using
new GPT6.1 or experience-assisted outcomes. All selected cases are retained,
including the two execution-invalid cases in the older memory arm.

Freeze the exact same61-approved-experience snapshot/library from the GPT5.6 arm.
Same original tasks/source/case.json/images/runtime/evaluators and request/time
budgets. Only execution model/profile changes to gpt-6.1-sol/medium/priority.
Source-applicability selection12requests,Contract12,Action24requests600seconds,
total48,one Action,final-onlyGold. No diagnosis,Contract review,AB,extraction,
online learning,experience changes or Gold feedback. No old model outputs or
partial patches are reused.

Headline success is passed/30; execution errors count as failures per explicit
user policy. Raw Gold and infrastructure categories remain separate for diagnosis.
Historical GPT6.1latent has valid scores for21/30cases(17case passes,18/22trial
passes);9 are CONTAMINATED historical results, not trusted baseline observations.
This is a historical development/within-cluster transfer comparison, not a new
independent holdout. The same30 were selected for low GPT5.6, not low GPT6.1.

Preflight reuses90trusted calibration controls only after same source/image/evaluator
verification. No model or new Gold calls before independent fresh-agent READY.
All30 new binding hashes and paired original input checks are archived. CPU Docker
images reused, no GPU. Launch8workers; reduce future concurrency6/4 only for explicit
provider capacity errors without replaying requests. Results and all-selected model
comparison are archived/committed automatically on completion.
