# Local Docker experiment environment

Spec hash: 4c36c76c
Spec: /home/sribd/Downloads/wangshu/tempoevo-paired10-sol6-training-20261116_092532/env-spec.json
Existing immutable solver: sha256:06e8aefa92fe3b031af8d52938059ce3f4b99db0489c445cb1d5095f2487d50c
Existing immutable grader: sha256:00b97937eb4e3c9db1ef6f071dde20629034910bbbfdd9a8b4a34b1ecf102da7
No rebuild; no local GPU workload. GPU availability checked: both 32768MiB devices have 5MiB used.
Runtime validation: pending exact selected original/reference/negative control calibration.
Agent-follows-doc command: execute the one line in /home/sribd/Downloads/wangshu/tempoevo-paired10-sol6-training-20261116_092532/prepare-command.sh verbatim from /home/sribd/Downloads/wangshu/temporal-contract-analyzer.
Model execution is excluded from this validation command.

## Corrected evaluator environment 9efc2228
Spec: /home/sribd/Downloads/wangshu/tempoevo-paired10-sol6-training-20261116_092532/env-spec-v2.json
Image IDs unchanged; disposable mounts narrowed to builds/go-cache/native-launch-receipts to avoid hiding node_modules.
First batch has no model calls and is retained; do not execute it after runtime changes.
Documented validation invocation: execute the one line in /home/sribd/Downloads/wangshu/tempoevo-paired10-sol6-training-20261116_092532/prepare-v2-command.sh verbatim from /home/sribd/Downloads/wangshu/temporal-contract-analyzer.
Calibration status: pending all 30 controls; preparation now exits nonzero if any case fails.

Corrected environment validated: 10/10 prepared, all 30 original/reference/negative controls valid and correct. Frozen protocols and disjoint selected IDs verified before launch.
Training launched with independent empty approved store and fresh online provisional pool. See /home/sribd/Downloads/wangshu/tempoevo-paired10-sol6-training-20261116_092532/launch.json.
