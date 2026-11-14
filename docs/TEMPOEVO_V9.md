# V9: cumulative within-task reflection delivery

New roots use `tempoevo-trajectory-v9`. V1–V8 trajectories remain readable and
cannot silently resume or have their recorded model inputs rewritten.

V8's online pool handles **cross-task provisional knowledge**. That is distinct
from **within-task working memory**. Historical V8 Action inputs included the
current Contract and the last controlled check feedback, but omitted the separate
diagnosis explanation and open questions. An unchanged Contract could therefore
lose the diagnostic reasoning on the path to the next Action.

V9 adds explicit `within_task_reflections` to every Action:

- Action 1: empty, because no attempt has failed yet.
- Action 2: diagnosis of actual failed attempt 1, its controlled observations,
  explanation, public supporting evidence, Contract delta and remaining unknowns.
- Action 3: cumulative reflections for attempts 1 and 2, each tied to its source
  attempt and intended correction Action.

The working memory is always passed in Auto-Contract trajectories after a valid
failed evaluation, even with zero cross-task matches, unchanged Contract, or an
`unknown` diagnosis. Records are marked `unverified_task_local_reflection`;
explanations remain hypotheses, not new business requirements. The current code
still comes from the last real candidate. Contract obligation protection remains.

No additional model call or approval is needed: this forwards the already budgeted
diagnosis outputs. Stage request/time caps and the three-Action limit are unchanged.
A failed diagnostic execution still stops explicitly; the runner cannot invent a
reflection. The baseline condition retains its existing public-feedback repair
budget and does not add a Contract/diagnosis stage just for this field.

Frozen Auto-Contract experiments also receive task-local reflections; their ban is
on cross-task provisional memory. Held-out testing uses only public observations
and diagnosis for repairs, with Gold still executed independently at the end. No
raw Gold assertion, hidden path or scorer output is added to working memory.

The [V8 online policy](TEMPOEVO_V8.md) still controls cross-task candidates. The
reported count of tasks receiving provisional pool guidance is not the count of
Actions receiving within-task reflection. Their metrics must not be conflated.

Offline tests verify Action 2/3 inputs with unchanged Contract, zero experience
matches, unknown hypotheses, cumulative attempt links, previous candidate identity,
unchanged model-call counts and testing Gold isolation. No real model calls or
retraining are started by this implementation.
