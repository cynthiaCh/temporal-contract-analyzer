# GPT-5.6-sol medium: Latent + experience only, fixed test30, eight workers

Authorized test: the fixed 30 testing cases, one Action (24 model requests / 600 seconds), independent final Gold, no Auto-Contract, no learning or candidate extraction. The approved 61-entry bank and exact per-case deliveries are reused from the completed GPT-5.6 full-library test (25/30). Historical selector calls are retained in retrieval-provenance.json and are not newly executed. Twenty-nine cases have nonempty experience; one has none. No choices are made using this run's outcomes.

Warm reuse of the original immutable CPU Docker solver/grader images and exact Codex c3dea068 (0.167.0-alpha.4.1), model gpt-5.6-sol / medium / priority, including its bounded two transport retries. No GPU is allocated or local model trained. Current repository runtime includes the new latent_experience replay condition, guard/adapter updates and scorer diagnostics; those implementation differences mean this is a paired input ablation with disclosed runtime drift, not an assertion of byte-identical historical runtime.

Before any model request, prepare.py verifies exact source/task/experience parity with each retained parent, checks benchmark files against the immutable grader image, reruns all 90 original/reference/negative scorer controls, and prepares 30 new bound trajectories. The reference/scorer controls remain outside actor input. Original valid failures are never retried automatically. Infrastructure errors remain separate from behavioral scores.

Zero-model validation, from the analyzer repository (safe only before launch):

```sh
python3 -B "/home/sribd/Downloads/wangshu/tempoevo-gpt56-sol-medium-latent-experience-test30-workers8-20261122_024039/validate.py"
```

The validator checks all 30 source/runtime bindings, unchanged model/binary/bank/images/limits, exact deliveries and test split, null Contract and no started stages. It must return valid:true before the supervisor starts run_testing.py with workers8. Launch and completion evidence are archived under experiments/testing-runs/ with the same run name. No experiment or model request is started by the validator.
