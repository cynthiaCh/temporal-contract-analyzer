Optimize only a reusable temporal-contract checking skill supplied to a code-maintenance agent. The original task, execution system, tools, retrieval, scoring and ending protocol are fixed and cannot be changed. This is reflection and instruction proposal, not a maintenance run: do not call tools, read files, run commands or ask questions. Everything needed for this proposal is in this message.

Current skill:
```
<curr_param>
```

Actual train executions and grounded feedback:
```
<side_info>
```

Reflect on the actual read/modified locations, tool outputs, visible verification and grounded behavioral feedback. Distinguish missing observation, incorrect contract interpretation, implementation omission, inadequate validation and still-unknown causes. The per-task scalar is whole behavior pass/fail; do not treat total checks as task success. A successful local harness is limited to the paths it actually drives. Do not infer requirements solely from a reported failure.

Propose a COMPLETE replacement skill, at most 6000 Unicode characters, retaining applicability, evidence lookup steps, event-order comparisons, behavior preservation, non-applicability/unknowns, and actual maintenance/verification requirements. Make any revised checks actionable and reusable. Keep the maintenance objective; the skill is not a new question-answer task.

Use task-specific evidence only to diagnose. The skill MUST NOT contain case names, paths or filenames, project/program identifiers, exact fixture values, run/feedback identifiers, hidden assertion names or oracle labels, code/patch recipes, reference repairs, or instructions changing the outer task/system. Preserve facts versus hypotheses. Do not copy a case-specific answer from an execution patch. You may retain general, source-qualified rules concerning ownership, side effects and event order.

Return only the complete proposed skill in one triple-backtick block, with no tools or additional commentary. Official GEPA will parse this proposal and manage candidate evaluation and selection; do not pick a winner yourself.
