# TempoEvo V4: A → B → C

V4 is `tempoevo-trajectory-v4`, independent of historical V1–V3 budgets and files.
Use `tempoevo prepare/run`; historical batches are inspected with `history status/report`.
Old execution engines and the `experience-evolution` command have been removed. No old starting-repair/corrective slots are reused in V4.

A freezes original task/code/docs, deterministic AST evidence, approved memory,
model settings, executable/evaluator hashes, feedback policy and budgets. Structured
retrieval uses optional frozen `routing_analysis` grounded in the original public source.
If absent, a separately budgeted source/AST analysis stage supplies retrieval facts
before retrieving experience and generating the structured initial Contract.
BM25 indexes the same frozen approved bank; baseline/contract never read its text.
Both retrieval strategies have the existing five-record default cap.

B starts with one candidate from the original. An Action with valid deterministic
visible assessment is one attempt. Failed visible assessments trigger a separate
source-grounded diagnosis (`implementation_gap`, `contract_gap`, `both`, `unknown`)
and optional Contract revision. There are at most three Actions and two diagnoses,
with first visible PASS stopping immediately. Every correction uses the actual
previous candidate. Independent repeats must be separate roots prepared from the
same original and memory snapshot: they are never extra attempts in one trajectory.

Contract obligations have immutable IDs/text; revision can add obligations and
change ordering, barriers, lifecycle, scope and checkpoints with public citations.
The deterministic monotonic check prevents obligation deletion, but does not prove
semantic correctness. Correcting a mistaken protected obligation requires a new
reviewed trajectory rather than silently weakening it. Structured Contract changes
require a new `routing_analysis` in the diagnostic response, validated against
original public source, and reroute only within the same frozen bank.

C stages success proposals in `candidate-pool/success.json`. Three valid failures
create `expert-summary-task.json`, status `awaiting_expert_summary`, with no invented
human response. Only explicit named-human submission creates an expert candidate;
it remains a failed trajectory, with effectiveness unverified. Use
`publish-candidate success|expert` to materialize an **unapproved** immutable record
in the existing unified store for its review page. This command is not acceptance:
the long-term retrieval view remains `approval.freeze`, containing accepted versions
only. Existing review/edit/version/evidence interfaces apply; editing never inherits
acceptance. The page marks success vs expert-failure origin. Reject/revise/accept
are real operator actions, not model stages. No source is auto-approved.

## CLI

```
python3 -m temporal_contract_analyzer tempoevo prepare learning.json --root /new/trajectory
python3 -m temporal_contract_analyzer tempoevo run --root /new/trajectory --execute
python3 -m temporal_contract_analyzer tempoevo status --root /new/trajectory
python3 -m temporal_contract_analyzer tempoevo cancel --root /new/trajectory
python3 -m temporal_contract_analyzer tempoevo expert-summary summary.json --root /failed/trajectory
python3 -m temporal_contract_analyzer tempoevo publish-candidate success --root /passing/trajectory
python3 -m temporal_contract_analyzer experience-memory review --store /path/to/memory
```

Preparation, status and publication never launch a model. `run --execute` uses the
shared isolated native CLI runner (`execution_backend.py`). Every LLM stage uses gpt-6.1-sol/medium;
diagnosis and extraction use read-only analysis sessions with independent schemas,
and their JSON results are archived without requiring routing's Markdown `contract`
field. Task evidence accepts `TASK` and `original task` with the same exact-content
matching. Experience extraction uses the review library's R/O/B/L/I/F/A labels,
registered mechanism predicates and rule categories; prose applicability and
exclusions belong in rule bodies. Action uses a writable isolated candidate workspace. No gold/referee directories
are mounted into it. Requires Linux native isolation provisioning (`bwrap`, Codex,
authentication and Node); this change does not provide a macOS native sandbox or a
new Docker deployment adapter. No real model runs were performed for this change.

## Evaluation boundary and fairness

Visible and gold evaluators are separate deterministic host argv commands, outside
the candidate. Each receives the candidate directory as its final argument and
returns JSON. Its working directory is its stage archive, so relative evaluator
artifacts do not modify the frozen candidate. Visible output requires `passed` (boolean), `observations`,
`regressions`, `unknowns`. Only those three feedback fields reach diagnosis/Action;
other output remains archived, never fed back. Gold executes only after repair,
with its independent result stored separately. Visible PASS is never gold PASS.
The evaluator author must ensure visible observations contain only predeclared
public checks; arbitrary nested secret strings cannot be semantically detected by
a field-name filter. Evaluators are trusted, hash-bound host programs.

Conditions: `baseline`, `contract`, `bm25`, `structured`, `fixed_contract`.
All use the same three-Action limits and evaluation commands. `fixed_contract` is
the structured condition with Contract revision forbidden but identical Action
opportunities. Baseline repairs using visible feedback with no Contract/experience.
Testing requires an explicitly supplied frozen approved snapshot; no extraction,
expert task, candidate publication or memory writes occur. Learning feedback also
uses the same declared public field allowlist; reference/gold patches are excluded.

## Budgets, recovery and outputs

With defaults: Contract 12 requests, each Action 24, each diagnosis 12, success
extraction 12; each stage ≤600 seconds. Contract-enabled learning upper bound:
12 + 3×24 + 2×12 + 12 = **120 requests**. Testing omits extraction: **108**.
Structured/fixed conditions without supplied routing metadata add one 12-request
routing analysis: **132 learning / 120 testing**. Baseline learning: **84**; baseline testing: **72**. Conditions have equal Action
budgets, not artificially equal total calls despite different analysis stages.
Visible/gold evaluation timeouts are separately frozen (default 60 seconds each).

`state.json` and `stages/*/{input,result}.json` journal each stage before invocation.
Completed stages can be reused, started/incomplete stages cannot silently replay.
Invalid output, host errors, timeout and behavior failure are distinct: invalid
execution ends `execution_invalid`, never “three failures”. Cancellation prevents
later dispatch. Already-started native work has its own bounded timeout and may
finish before cancellation is observed (no cross-process native interrupt bridge).

`attempts/N/candidate`, original/previous diffs, `revisions/N.json` (before/after,
diagnosis, structured delta, citations, unknowns), delivery and independent gold
results are retained. `summary.json` distinguishes cumulative visible success,
first-pass attempt, final gold, requests/tokens/time, diagnoses, invalid/incomplete
stages and actual delivery. Unstarted later attempts are not separate cases.

## Remaining architecture limitations

- Retrieval uses a frozen source-analysis stage or supplied grounded metadata,
  not a trained retriever. No weight updates or learned ranking are implemented.
- Contract semantic correctness and true human identity remain external judgments;
  deterministic citation/monotonic checks cannot certify them.
- The generic host-command evaluator adapter does not automatically split existing
  SWE-TempoC gold scorers into safe visible checks. Configure vetted public checks
  explicitly; never wire hidden details into a visible evaluator.
- Expert summaries and publication are explicit local CLI operations; the existing
  browser reviews materialized records, not an automatic expert-authoring agent.
- No production campaign, 100-case run, paid experiment or cross-task effectiveness
  claim was performed. All new tests use synthetic models and offline evaluators.

Offline demo (zero provider/model calls): `python3 examples/tempoevo-v4/offline_demo.py /new/demo-root`. Its deterministic public evaluator verifies second-attempt success; synthetic model responses are explicitly labeled.

See [local verification results](TEMPOEVO_V4_TEST_RESULTS.md) for test counts and assurance limits.
