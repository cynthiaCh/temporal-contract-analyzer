# V10: reserved testing and final-only Gold

Historical protocol. New execution uses [V11 semantic selection](TEMPOEVO_V11.md); V10 roots are read-only.

`experiments/evaluation-splits.json` pins the source CSV digest and declares ranks
1–25 training, 26–50 testing. `experiments/testing-cases.json` registers only public
case identities and source manifests for the latter. Reserved test IDs are rejected
in learning mode at both preparation and execution. Training IDs cannot be relabeled
as independent tests. New runs use `tempoevo-trajectory-v10`; historical batches stay
read-only and are not replayed, rescored or relabeled.

Testing reads frozen approved memory only. Online pools, training evaluators and
training-feedback mappings are forbidden. Contract/Action/diagnosis receive public
observations only. Public checks and source-visible obligations must be declared
before execution, with the same fixed maximum of three Actions. Candidate selection
and stopping use public feedback; after repair ends the chosen candidate receives
one independent Gold invocation. Its score, PASS/FAIL and failures cannot feed back
to another Action, Contract, candidate selection or extra attempt. Testing creates
no experience candidate or expert-summary task. Visible PASS and final Gold PASS
are reported separately.

The batch preparer supports `--mode testing --start-rank 26 --limit 25`.
The default reviewed store is `experience-memory/library`; `--store` selects an
explicit alternative. The legacy archive directory is not the current library.
Unlike learning preparation, this branch evaluates only the original public candidate with
its public checker. It never executes Gold, opens a reference implementation or
builds reference/Gold controls before testing. New task families require an explicit
`--visible-evaluators /path/public-evaluators.json` mapping case IDs to frozen public
evaluator configurations. Missing or broken public adapters fail preparation before
any model call; do not substitute Gold as a convenient public checker. The built-in adapters now cover all 25 reserved IDs and have been checked against original public code and synthetic API fixtures; see [public adapters](PUBLIC_TEST_ADAPTERS.md). Adapter completion does not launch a paid test batch.

Example configuration: `examples/tempoevo-v4/reserved-testing.json` (replace absolute
paths and the placeholder frozen approved snapshot before use). Existing trusted
Docker isolation keeps scorer/reference files out of the solver workspace; only the
final trusted evaluator can access the original Gold probe. No Gold or reference
content was read to create this split. Verification used synthetic scores only.

## Independence limits

This is a reservation from now on, not proof that these are wholly unseen cases.
The list was selected using historical failure rates and shares source task families
with ranks 1–25. A protocol-identity-only scan of the repository's research directory
and sibling TempoEvo trajectory directories found no direct training `task_id` matches
for ranks 26–50; it did not inspect historical Gold outcomes and is not an exhaustive
exposure audit. Accordingly `held_out_eligible` remains false and the split metadata
says `reserved_test_not_certified_unexposed`. Do not present scores as unseen-family
generalization without a separate split/exposure audit.
