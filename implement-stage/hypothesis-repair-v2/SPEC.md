# Hypothesis-driven repair and matched D control

Base commit: 3a8fd7868128a8c5b7b93bd24666d3f5a92cc62b.

Target: turn a calibrated, scored failed patch into a matched pair of continued repairs: current D report alone versus D plus failure-specific, falsifiable hypotheses and bounded source relations. Both jobs start from the exact scored candidate, inherit its model/effort/timeout, and preserve the original task. Compare gained checks and lost previously passing required/forbidden checks after trusted evaluation. Never replace the parent patch automatically.

Inputs: archived experiment/job/evaluation, scored candidate snapshot, public task, candidate source. Outputs: new experiment with `retry-source.json`, `hypotheses.json`, independently frozen prompts, normal evaluations plus regression/acceptance records. Entry points: Workbench API, reports CLI, experiment page.

Success commands: `python3 -m unittest discover -s tests -p 'test_hypothesis_repair.py'`; existing workbench/learning/context tests; browser check. Run live paired follow-ups on the prior matrix's 11 D failures after deterministic checks pass.

Scope: candidate explanations, bounded lexical/import/caller evidence, development-only feedback exposure. No claim of proven causes, full dataflow, hidden-reference access by agents, token-equal budgets, or statistically established benefit.
