# GPT-6.1-sol medium: Latent + experience only, fixed test30, eight workers

Authorized testing on the fixed30 cases. One Action24requests/600seconds, final independent Gold only, no Auto-Contract, no new selector call, no learning or experience extraction. The61-entry bank and exact per-case experience deliveries come from the historical GPT-6.1 medium27/30 full-library test:28nonempty deliveries and2empty. No choices are based on new test outcomes.

Warm reuse of the original immutable CPU Docker images and exact Codex c3dea068 (0.167.0-alpha.4.1), gpt-6.1-sol/medium/priority, bounded transport retries2. No local GPU workload or model-parameter training. Current merged runtime/guard and grader diagnostic changes relative to the historical parent are disclosed; this does not claim byte-identical historical runtime. The immediately preceding GPT-5.6 latent-experience run uses the same current execution stack.

The90 scorer-control results from that preceding run are reused only after verifying original task/source parity, immutable image identities and current evaluator hashes. All90 raw expected-valid original/reference/negative control results and their SHA256s are retained. All1905 benchmark files are checked again against the grader image, and30fresh trajectories must bind the original GPT-6.1 tasks,sources,model,bank,images,budgets and exact historical deliveries.

Documented zero-model validation (safe only before launch), from the analyzer repository:

```sh
python3 -B "/home/sribd/Downloads/wangshu/tempoevo-gpt61-sol-medium-latent-experience-test30-workers8-20261122_041732/validate.py"
```

The validator must return valid:true before launch. Inspect calibration-reuse.json and its raw receipts alongside preflight.json. A fresh independent agent follows this documented command before the supervisor starts the public run_testing.py with workers8. No model requests are made by the validator. The supervisor archives final results and does not retry valid behavioral failures; infrastructure-invalid outcomes remain separate.
