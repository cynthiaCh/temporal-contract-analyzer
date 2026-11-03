# Failure-feedback memory and adaptive review

Target: automatically extract candidate review lessons from calibrated failed experiments; use their inspection recipes and source context in an explicit development-only learned_review condition.

Base commit: af78281209bef2e318119842f445a123bd01cbca.

Inputs: saved evaluation and oracle JSON; original candidate inventory; verified archived source snapshot. Outputs: separate append-only lesson JSON, source-grounded review Markdown, frozen lesson IDs and exact prompt bytes in new experimental jobs; CLI and browser controls.

Success: `/usr/bin/python3 -B -m unittest discover -s tests -p test_failure_learning.py` and existing experiment/browser checks.

Scope: deterministic failure-family classification, candidate experience memory, same-case/same-input retrieval, bounded source-context selection. No model call to create lessons, automatic analyzer-rule mutation, weight training, cross-project generalization or independent effectiveness claim. Candidate lessons and feedback-aided reruns are explicitly exposed development conditions. Original scores, frozen layers and existing A/D prompts retain their meanings.
