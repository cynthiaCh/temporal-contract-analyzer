# Transfer progress composition v4: startup-window cue

This is a controlled-information arm of `transfer-progress-composition-v4-vanilla`, not a new engineering incident.
It does not remove telemetry or weaken the v4 oracle. Both retain the same executable source, ten schedules,
eight obligations, reference, mutants, and acceptance rules.

The only experimental difference is in the candidate-visible `base/README.md`, combining facts already present separately in v4
into a startup-window cue: `start()` can synchronously emit multiple packets; the first
`showProgress` callback can switch visits before `start()` returns and hands its cleanup handle to the caller.
The cue does not specify the admission predicate, guard location, or differing audit/UI completion policies.

This arm was designed after observing repeated Astra omissions of `start-switch-admission` on v4.
It is therefore an outcome-informed exploratory intervention, not an outcome-blind difficulty sample. Its inputs were separately
frozen after construction; subsequent runs count only toward this ID. Historical v4 results are neither transferred nor included in this arm's success-rate denominator.

The intended use fixes the model, reasoning effort, CLI, timeout, and authorization condition and interleaves repeated runs of:

- v4 latent: reconstruct the window from distributed code relations;
- this arm: window facts are localized, but guard rules must still be inferred;
- contract-provided: admission and all other contracts are explicitly supplied.

Local verification:

```bash
node case-clusters/transfer-retry-handoff/arms/transfer-progress-composition-v4-window-cued/oracle/demo.cjs
```
