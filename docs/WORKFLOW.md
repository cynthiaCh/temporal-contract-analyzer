# Experience construction and testing

Use this guide to choose a research condition and interpret its results. For
commands and environment setup, see [Docker execution](DOCKER_TRAINING.md).
The current protocol is `tempoevo-trajectory-v13`; model weights do not change.
Construction updates external experience, not the common repair prompt.

## Configuration and conditions

`tempoevo prepare` freezes a fresh trajectory without calling a model;
`tempoevo run --execute` explicitly starts execution. Select model settings with
`--model-config` / `--model-profile`; the built-in default is `sol61-medium`.
Resolved settings, limits and memory bindings live in `protocol.json`. Do not
infer a historical run's model or library size from current defaults.

| Condition | Experience | Auto-Contract | Availability |
|---|---|---|---|
| `structured` | Business applicability selection | Draft; learning may revise | Learning/testing |
| `fixed_contract` | Select once | Draft; no behavioral revisions | Core trajectory API |
| `contract` | None | Draft | Learning/testing |
| `baseline` | None | None | Learning/testing |
| `latent_experience` | Replay explicit frozen selection | None | Frozen testing only |

Batch `prepare_selected.py` exposes all listed conditions except `fixed_contract`.
No condition automatically launches A/B or no-memory groups. AST is disabled by
default; `ast_policy=enabled` or batch `--with-ast` opts in. Full public sources
remain available without AST.

## Experience construction

Standard `mode=learning`, `condition=structured`:

```text
Public task/source -> reviewed Abstract recall + business applicability selection
  -> Auto-Contract -> bounded Action -> training Oracle acceptance
  -> failure: diagnosis + task-local reflection -> next Action
  -> failure then success: reusable-correction extraction -> candidate review
  -> three unsuccessful Actions: real expert-summary request
```

Learning defaults to three Actions; preparation may lower the limit. Public checks
are optional advisory feedback; only the training Oracle decides acceptance.
Hidden assertions and reference repairs never reach the solver. An acceptance
verdict or observation is not a new business requirement or proof of a cause.
Implementation-only diagnoses keep behavioral Contract obligations unchanged.
Supported Contract revisions reselect from the same frozen bank; `fixed_contract`
selects once. Cumulative task-local reflections are fallible, not approved memory.

First-Action success skips extraction. Confirmed failure followed by success can
produce a reusable correction; routine implementation-only fixes add no guidance.
Extraction can fail or yield no publishable experience. Three unsuccessful Actions
request a real expert summary; a smaller Action budget does not reach that branch.

Prefer in-place updates under stable IDs; content and Abstract changes need renewed
review. Explicit merges retire other IDs only after acceptance. Publication leaves
candidates unapproved until a named human accepts their exact content. Online
construction collects proposals in a separate pool; unreviewed proposals never
guide later tasks, and testing cannot access the pool. See
[experience review/storage](../experience-memory/README.md).

## Frozen testing and evaluation

Standard `mode=testing`, `condition=structured`:

```text
Task + public source -> business selection from a frozen approved bank
  -> Auto-Contract -> one Action + final submission -> one independent Gold score
```

The Action can inspect source, run available public tests and revise code inside
its budget. Gold runs once after submission; neither its verdict nor failure
details return to solving, select a candidate or trigger another Action. Testing
performs no diagnosis, extraction, expert-summary request or memory update.
`latent_experience` revalidates/replays a frozen selection, skips a new selection
model call and Contract draft, and runs only Action and final Gold.

No public behavioral suite is generated or required. An optional `visible_evaluator`
can provide auxiliary feedback; no evaluator means unverified, not PASS. Testing
ends as `scored` with a separate `gold_result`; inspect the score rather than
interpreting process completion as behavioral success. Infrastructure errors are
execution failures, not behavioral failures.

Source-read proofs are optional audit (`observed`, `not_observed`, `unavailable`),
not an acceptance gate or evidence of model understanding. Candidate validity,
protected files, frozen bindings, usage accounting and evaluator isolation remain
required. Historical Gold-guided tests are not relabeled as blind testing.

## Retrieval, Contract and recovery limits

Business-source retrieval requires current reviewed Abstracts. It recalls at most
six candidates and delivers at most three entries / 8,000 characters, considering
applicability, exclusions, supported obligations, coverage and redundancy. Unknown
premises do not satisfy conditions; no eligible guidance permits repair without
experience. Labels alone do not authorize delivery. Current task/source evidence,
not experience, supplies requirements.

Auto-Contract describes the requested change and relevant preservation, with
triggers, observable outcomes and source evidence. Separate explicit requirements
from inferred preservation; put unsupported policies/conflicts in unknowns.
Existing behavior is not normative when the task asks to change it. Quotations
being present does not establish semantic entailment.

| Stage | Default maximum requests | Maximum seconds |
|---|---:|---:|
| Selection, Contract, diagnosis, extraction (each) | 12 | 600 |
| Action | 24 | 600 |

Default structured caps are 156 requests for three-Action learning and 48 for
single-Action testing; these are ceilings, not guaranteed usage. Limits can be
lowered at preparation. The initial Contract separately defaults to 8,000 canonical
JSON characters, not tokens; this cap does not cover later diagnosis revisions.

Preparation validation checks structure and source quotations. Invalid output gets
at most one correction within its original stage budget, then guidance is discarded
or the prior valid Contract retained. An unusable initial draft permits Action
without Contract; it is never silently truncated. This is not Contract Review.
Selection validates candidates independently: malformed/conflicting rows reject
affected entries; valid independent entries survive with warnings in
`retrieval/selection-*-validation.json`. An unusable envelope or no valid assessments
uses the bounded correction/fallback. Transient transport restarts share original
caps; partial started stages are not blindly replayed.

Use new roots after implementation changes; preserve old results and approvals.
The [case split](../cases/README.md) reserves testing from learning but contains
historical exposure and shared source families. Scores do not establish unseen-source
generalization or causal benefit of individual guidance. Everyday
[MCP use](PERSONAL_MCP.md) is a separate workflow without this runner or Gold.
