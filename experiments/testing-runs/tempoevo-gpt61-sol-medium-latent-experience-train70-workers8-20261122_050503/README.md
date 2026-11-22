# GPT-6.1-sol medium: frozen Latent+Experience training-cohort replay

All original70 training IDs, original70/30 split preserved, evaluation_purpose=training_replay. This is evaluation on exposed training cases, not new training or an independent holdout. One Action24requests/600seconds and final Gold per case, no Contract, training-feedback, diagnosis, reflection, extraction, or memory updates. Previous train70 final65/70 allowed3Actions and evolving experience; this new one-Action fixed61 replay is a different protocol.

Same immutable Docker images, exact Codex c3dea068, model medium/priority and frozen61bank as latest test30. Historical control reuse was rejected because gold.py has changed;210 fresh original/reference/negative Gold controls are executed before launch. Benchmark files verified against immutable grader. New split guard permits explicit frozen training replay while retaining training role; legacy independent-test rejection remains.

Historical training used source-bound-v8 retrieval, not current business-source-v1. Therefore8workers first run public-source selection only on70 structured seed trajectories. No seed Contract or Action is invoked. All resulting deliveries (including valid empty deliveries) are frozen without score-based changes; fresh latent_experience trajectories replay them and run8workers. Selector calls/costs remain separately archived. No gold feedback supplied to selectors or solvers. Infrastructure errors remain unscored, never behavior failures.

Documented zero-model prelaunch invocation from /home/sribd/Downloads/wangshu/temporal-contract-analyzer:

```sh
python3 -B "/home/sribd/Downloads/wangshu/tempoevo-gpt61-sol-medium-latent-experience-train70-workers8-20261122_050503/validate.py"
```

It checks70seed protocols, exact train70 membership, unchanged split, frozen bank/model/binary/images/budgets, controls and absence of executed stages. Fresh agent must execute it before paid launch. After selection supervisor verifies every fresh latent binding and frozen replay before Actions. A detached supervisor records progress and auto-commits final evidence. Executed roots must not be relaunched.

Calibration helper correction: python-pilot-0.1 uses the same python_gold.py adapter as prepare_selected.py. The first invalid generic-adapter control receipt is retained; no model was called. All210valid final controls must pass.
