# V4 implementation sequence and decisions

Repository inspected: README, V3 Workflow/Development/FrozenEvaluation, native runner,
review API, immutable memory and approval adapters; architecture read from
figures/TempoEvo-Architecture-EN.pdf. No applicable AGENTS.md exists in this checkout
or its parent chain. The /Volumes paths are unavailable here; use this checkout.

1. New independent protocol and append-only stage journal; historical dispatch unchanged.
2. Three-Action trajectory, feedback projection, contract diagnosis, deterministic evaluation.
3. Learning candidate staging and real-human failure summary, export to existing reviewable memory.
4. Isolated native model adapter and CLI; offline synthetic verification, examples and docs.

Decisions made before implementation:
- Visible and gold evaluators are separate trusted host commands, outside candidate root.
  They receive a candidate path and return JSON. Only declared observation fields enter prompts.
- A trajectory ends on first visible PASS; gold never feeds the repair loop.
- Structured retrieval before initial Contract uses supplied source-bound routing_analysis.
  It is required for the structured conditions, not guessed from hidden test outcomes.
- Original Contract obligations are append-only by identity/text. Other dimensions may be
  revised with source citations. This deterministic restriction cannot prove semantic validity.
- New C records are staged outside published memory. Human summary/review submission is
  explicit; only an immutable published candidate accepted through existing named review
  becomes retrievable. No model can submit a human summary.
- Independent repeats are distinct new roots with the same original inventory and frozen bank.

Refinement before final delivery: requiring precomputed routing metadata would leave
raw-task structured runs incomplete. Add a separately archived, budgeted 12-request
routing-analysis stage when structured/fixed conditions omit routing_analysis. It
uses only raw public inputs/AST, produces retrieval facts, not the structured final
Auto-Contract. Retrieve from the frozen bank, then generate the initial Contract.
All stages retain the same gpt-6.1-sol/medium identity. Supplied grounded metadata
can still be frozen to avoid that extra analysis call. Budget upper bounds must
include this conditional stage (132 learning / 120 testing).

Post-implementation retirement: V1–V3 execution engines were subsequently removed. Shared NativeBackend moved to execution_backend.py; old roots are inspected through data-only history_cli.py. Earlier references above describe the implementation sequence, not remaining legacy execution support.
