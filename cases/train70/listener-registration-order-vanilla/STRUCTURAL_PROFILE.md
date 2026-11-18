# Author structural assessment — revision 2

Status: development hypothesis, no independent recoverability review. The
ratings below derive from code and deterministic schedules; model outcomes are
not their input. Revision 1 and revision 2 are the same independent incident.

## Evidence and proposed ablations

| Necessary fact proposed by author | Candidate-visible location | What is lost if the fact is unavailable |
| --- | --- | --- |
| Bootstrap can occur before connect returns | `base/src/channel.js`, `connect` | Reason to install the receiver before connecting |
| A decoder retains its continuation after reception detaches | `base/src/subscription.js`, listener | Reason to fence delivery after disposal |
| Show and close share a mutable subscription disposer | `base/src/presence-panel.js`, `createPresencePanel` | Location where nested calls can overwrite cleanup |
| Publication may reenter navigation; a transport may be revisited | `base/src/workspace-navigation.js` | Evidence for nested ownership and distinct visit identity |
| Metrics excludes bootstrap | `base/src/metrics-consumer.js` | Evidence against a global consumer-policy migration |

These are proposed evidence-ablation claims, not completed independent human
ablation results. Comments expose individual platform and product facts; no
single candidate artifact states the complete repair. Opacity remains O1,
not O2: the local facts are deliberately recoverable.

## Contract interaction graph

Atomic nodes: P (bootstrap precedence), V (current-visit delivery), R (reentrant
ownership and cleanup), M (metrics policy).

- P `precedes` synchronous publication, which can invoke R before outer show returns.
- R `invalidates` V for a previous visit, including one on the same channel.
- V `binds-to-generation` every pending decoder continuation.
- P and M have a consumer `ownership-conflict`: a shared policy cannot uniformly
  include bootstrap without authorization.

The order-only and channel-identity mutants show that satisfying a proper subset
still violates the complete contract. This is interacting composition, not just
four unrelated assertions.

## Coupling and cohesion interpretation

- E2: five proposed necessary facts across navigation, state ownership,
  subscription/decoding, transport, and policy roles; two dependency hops.
- O1: relevant facts are explicit locally; their composition is not.
- W2: navigation changes subscription ownership, while asynchronous decoder
  continuations can publish without passing a common validity arbiter.
- H2 under the temporal-modularity protocol: presence needs bootstrap while the
  ungranted metrics consumer must exclude it. The legacy count-based JSON rates
  consumer heterogeneity 1 because there are two policies; these definitions
  are intentionally not equated.
- C2: interacting precedence, invalidation, generation-binding, and consumer
  policy obligations, with targeted partial-correctness witnesses.

Author modularity class: `partially_modularized`. The panel is the explicit
subscription owner, but decoder publication and callback-induced ownership
changes are not mediated correctly by that owner. Do not infer low cohesion
merely from the number of files or label the entire repository low quality.

Hypothesis: local bootstrap repair often leaves visit-bound delivery or nested
cleanup incorrect. Evidence for that hypothesis requires actual valid model
runs and effect-level failure inspection; mutant failures alone do not establish
LLM failure probability.
