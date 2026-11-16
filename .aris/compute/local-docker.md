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

## Diagnosis fix retraining 3291baac
Spec: /home/sribd/Downloads/wangshu/tempoevo-paired10-sol6-retrain-20261116_111621/env-spec.json
Immutable images and toolchain spec unchanged; controller diagnosis-validation binding updated. No image rebuild.
Fresh memory, same case order, model, reasoning and budget; test cases excluded.
Validation command: execute the single line in /home/sribd/Downloads/wangshu/tempoevo-paired10-sol6-retrain-20261116_111621/prepare-command.sh verbatim from /home/sribd/Downloads/wangshu/temporal-contract-analyzer.
This command has zero model calls and calibrates all 30 controls; readiness pending fresh-agent validation.

Retraining validation: 10/10 prepared, all 30 controls valid and correct; fresh-agent report /home/sribd/Downloads/wangshu/tempoevo-paired10-sol6-retrain-20261116_111621/agent-follows-doc.json. Frozen protocols and same ordered training selection verified. Launch receipt: /home/sribd/Downloads/wangshu/tempoevo-paired10-sol6-retrain-20261116_111621/launch.json.

## Evidence and read-gate fix retraining 53ffb402
Spec: /home/sribd/Downloads/wangshu/tempoevo-paired10-sol6-retrain2-20261116_134902/env-spec.json
Images/toolchains unchanged; controller, adapter error attribution and read grammar updated. Their hashes match the verified 67-test fix; no image rebuild.
GPU availability checked, no local GPU workload. Fresh empty memory, original ten-case order and budgets.
Validation invocation: execute the single line in /home/sribd/Downloads/wangshu/tempoevo-paired10-sol6-retrain2-20261116_134902/prepare-command.sh verbatim from /home/sribd/Downloads/wangshu/temporal-contract-analyzer.
Zero-model calibration of all 30 controls; fresh-agent validation pending.

Latest retraining: 10/10 prepared, all 30 controls valid/correct, selected IDs and frozen runtime/model bindings verified. Launch: /home/sribd/Downloads/wangshu/tempoevo-paired10-sol6-retrain2-20261116_134902/launch.json.

## Contract correction training d38b4b29
Spec: /home/sribd/Downloads/wangshu/tempoevo-paired10-sol6-retrain3-20261116_152500/env-spec.json
Same immutable Docker images; controller recovery and retry accounting bindings updated and match the tested fix. No image rebuild.
Fresh empty memory and original ten-case order, model and total budgets. Contract write denial gets one correction within the original stage cap.
Validation invocation: execute the single line in /home/sribd/Downloads/wangshu/tempoevo-paired10-sol6-retrain3-20261116_152500/prepare-command.sh verbatim from /home/sribd/Downloads/wangshu/temporal-contract-analyzer.
Zero model calls; validate all 30 controls. Fresh-agent validation pending.

Contract correction retraining validated: 10/10 prepared, 30 controls valid and correct, same selected IDs and frozen models/runtime verified. Launch: /home/sribd/Downloads/wangshu/tempoevo-paired10-sol6-retrain3-20261116_152500/launch.json.

## V8 compatible train10
Spec: /home/sribd/Downloads/wangshu/tempoevo-v8-compatible-train10-20261116_172034/env-spec.json
Reuse immutable images; controller recipe and public adapters changed. No rebuild. Restore audited original 16-entry snapshot and fresh online provisional pool.
Validation invocation: execute the one line in /home/sribd/Downloads/wangshu/tempoevo-v8-compatible-train10-20261116_172034/prepare-command.sh verbatim from /home/sribd/Downloads/wangshu/temporal-contract-analyzer. Zero model calls. All 30 Gold controls and 30 public controls must be valid; references must pass both.

V8 calibration correction: composition-only ordering example is replaced by a source-supported lifecycle/audit example for maintenance. Failed first batch is retained and must not execute. Spec /home/sribd/Downloads/wangshu/tempoevo-v8-compatible-train10-20261116_172034/env-spec-v2.json.
Validation invocation: execute single line in /home/sribd/Downloads/wangshu/tempoevo-v8-compatible-train10-20261116_172034/prepare-v2-command.sh verbatim from /home/sribd/Downloads/wangshu/temporal-contract-analyzer. Fresh batch-v2, zero model calls; all 60 controls required.

V8 compatible environment 85600070 validated:10/10 prepared,60/60 controls valid/expected, selected648 files match grader, all10 frozen protocol bindings verified. Fresh-agent report /home/sribd/Downloads/wangshu/tempoevo-v8-compatible-train10-20261116_172034/agent-follows-doc-v2.json. Training launch /home/sribd/Downloads/wangshu/tempoevo-v8-compatible-train10-20261116_172034/launch.json; tests not launched.
