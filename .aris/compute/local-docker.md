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

## Reviewed paired test10 08ac9f2d
Spec: /home/sribd/Downloads/wangshu/tempoevo-v8-reviewed-paired10-test-20261116_212739/env-spec.json
Same immutable Docker images and CPU toolchains, no rebuild or GPU allocation. New testing source-bound router; A16 approved historical entries and B16+2 exact Cassie-reviewed compact records, independently audited stores, immutable combined snapshot. Single Action24requests/600seconds, total48; no training feedback/online pool/extraction.
Documented zero-model validation invocation: execute the single line in /home/sribd/Downloads/wangshu/tempoevo-v8-reviewed-paired10-test-20261116_212739/prepare-command.sh verbatim from /home/sribd/Downloads/wangshu/temporal-contract-analyzer. It compares selected files with grader, calibrates30 original/reference/negative Gold controls, and prepares both arms20 trajectories. Fresh-agent binding validation required before model launch.

Reviewed paired testing validated:728 selected files match grader;30 controls valid/expected;20 prepared protocols have verified frozen bindings, A16/B18 real approvals from Cassie, single Action and final-onlyGold. Fresh-agent report /home/sribd/Downloads/wangshu/tempoevo-v8-reviewed-paired10-test-20261116_212739/agent-follows-doc.json. Ready to launch both arms; immutable images reused.

## V12 full-approved test10, four workers 395e4127
Spec: /home/sribd/Downloads/wangshu/tempoevo-v12-full39-test10-workers4-20261116_230915/env-spec.json
Single testing condition, all39 approved categorized experiences frozen; no A/B. Source-bound retrieval selects at most5 eligible experiences per case. V12 advisory preparation validation shares original budgets; one Action and final-onlyGold, no learning. User requested4 concurrent workers. Same immutable solver/grader images; reuse CPU toolchains, no image rebuild or local GPU workload.
Documented zero-model validation invocation: execute the single line in /home/sribd/Downloads/wangshu/tempoevo-v12-full39-test10-workers4-20261116_230915/prepare-command.sh verbatim from /home/sribd/Downloads/wangshu/temporal-contract-analyzer. It verifies selected case/image identity, calibrates30 controls and prepares10 trajectories. Independent agent-follows-doc binding validation required before launch.

V12 full39 test10 preflight passed:728 selected files match pinned grader;30 controls valid/expected;10 protocol bindings verified, all39 actual approvals validated. Independent report /home/sribd/Downloads/wangshu/tempoevo-v12-full39-test10-workers4-20261116_230915/agent-follows-doc.json. Four-worker queue tested with synthetic jobs; no models called before this checkpoint.

V12 full39 single-group test10 launched with4 workers. Launch /home/sribd/Downloads/wangshu/tempoevo-v12-full39-test10-workers4-20261116_230915/launch.json; all first4 cases produced non-denied gpt-6.1-sol PreModelRequest receipts. Model processes run in Docker, no local GPU allocation. Source/runtime bindings must remain unchanged until this queue completes.

## Business applicability full39 test10 75e2c0ba
Spec: /home/sribd/Downloads/wangshu/tempoevo-business-full39-test10-workers4-20261117_001331/env-spec.json
Reuse immutable images and CPU toolchains; no GPU workload or rebuild. All39 approved guidance unchanged, one group,4 workers. Selection12 + Contract12 + Action24 =48 requests, one Action and final-only Gold. No generic routing or extra Contract review.
Documented zero-model validation invocation: execute the single line in /home/sribd/Downloads/wangshu/tempoevo-business-full39-test10-workers4-20261117_001331/prepare-command.sh verbatim from /home/sribd/Downloads/wangshu/temporal-contract-analyzer. Verify728 source files, all30 original/reference/negative controls,10 frozen protocol bindings, profile business-source-v1 and null contract_review_policy. No model execution allowed.

Business applicability environment validated:728 image file matches,30 controls valid/expected,10 frozen bindings and39 approvals independently verified. Report /home/sribd/Downloads/wangshu/tempoevo-business-full39-test10-workers4-20261117_001331/agent-follows-doc.json. Launch /home/sribd/Downloads/wangshu/tempoevo-business-full39-test10-workers4-20261117_001331/launch.json. Runtime bytes must remain unchanged until queue completion.

## Incremental100 train70 plus new20 and retained10 207d8d8c
Spec: /home/sribd/Downloads/wangshu/tempoevo-incremental100-workers4-20261117_011424/env-spec.json
Reuse immutable Docker images and CPU toolchains; no local GPU workload. User authorizes4 worker training then user-authorized automatic Silas acceptance then test20. Historical10 results retained unchanged and explicitly separated.39 approved initial entries;26 training records reused,44 executed. New cases use public syntax/build smoke plus original training Oracle, V8 three-Action semantics.
Documented zero-model command: execute the single line in /home/sribd/Downloads/wangshu/tempoevo-incremental100-workers4-20261117_011424/prepare-command.sh VERBATIM from /home/sribd/Downloads/wangshu/temporal-contract-analyzer. Validate100 selected image file identities,44 training original/reference/negative public+Gold controls and20 test original/reference/negative Gold controls;64 prepared bindings. All references must pass; originals/negatives must fail Gold. Fresh independent agent must verify before model launch. No model execution in this command.

Incremental100 preflight-only adapter correction: Python-pilot manifests use public prompt/reference fields and unchanged Python probe, not JS diagnostic_tasks/probe.cjs. Added dedicated python_gold.py using unchanged benchmark classification; JS Gold adapter untouched. Resume documented prepare-only invocation after first attempt drains; successful zero-model controls reused only after verifying current bindings; failed preparation roots retained. Updated spec /home/sribd/Downloads/wangshu/tempoevo-incremental100-workers4-20261117_011424/env-spec.json. Model calls remain zero.

Incremental100 second preflight correction: unchanged RxJS probe writes trusted receipts into results/multi-family-expansion-20261005/rxjs-executions, previously read-only. Mount ONLY that disposable log directory writable; rxjs-cache/node_modules and all benchmark/probe source stay immutable. Runtime binding changed before any model call; all affected prepared trajectories require new roots and controls. Re-execute same documented zero-model command once previous attempt drains; old preparation/control directories retained.

Incremental100 public-input size correction (zero models): derived RxJS frozen public base has1448 files/18MB and exceeds existing1000-file safety cap. Added explicit frozen_base_public_projection_v1: all original native/RxJS product src plus named original public tests/root docs (~274files/864KB). Dedicated projected_gold.py restores unprojected ORIGINAL base, applies actual submitted modifications/deletions, then runs/classifies unchanged probe. This differs from full-repository baseline input and is recorded in protocol. Model never sees trusted tests or reference patches; dependencies remain grader-only. Updated spec includes adapter source hashes. Re-execute documented prep-only command after drain if projected cases failed; current valid bindings/controls can be reused.

Incremental100 fully validated before model calls:64 current bindings,324 controls (132train Gold+132public+60newtest Gold),15444 source image files,39 actual approvals,26 reused source-matched accepted records; retained10 unchanged. Independent report /home/sribd/Downloads/wangshu/tempoevo-incremental100-workers4-20261117_011424/agent-follows-doc.json. Four-worker authorized train->Silas automatic acceptance->test20 chain launched: /home/sribd/Downloads/wangshu/tempoevo-incremental100-workers4-20261117_011424/launch.json. Runtime bytes must remain frozen while workers run.

## Incremental100 bounded-prompt recovery tempoevo-incremental100-workers4-20261117_011424-resume1
Spec: /home/sribd/Downloads/wangshu/tempoevo-incremental100-workers4-20261117_011424-resume1/env-spec.json
Images/evaluators unchanged and source controls reused after exact evaluator/source hash checks. No local GPU workload. Confirmed tool bug: duplicate/source-heavy stage input exceeded Codex1048576 character ingress; new bounded prompt leaves full public workspace intact and indexes omitted inline text. Old four pre-model request-count errors remain unknown in historical records. One accepted repair has failed extraction with opaque provider400; recovery imports its completed Action/Gold and gives ONLY11 remaining extraction requests; never reruns accepted repair.39 other completed valid results imported with sealed provenance,4 pre-Action failures get fresh roots.
Documented zero-model recovery invocation: execute the single line in /home/sribd/Downloads/wangshu/tempoevo-incremental100-workers4-20261117_011424-resume1/prepare-command.sh VERBATIM from /home/sribd/Downloads/wangshu/temporal-contract-analyzer. Independently verify44 new bindings, original protocol/state/result/candidate hashes,40 sealed imports,4 pending fresh repairs, listener extraction11 requests and no extra Action/Gold, full source preservation and wire bounds; no model calls in preparation. Validate old score roots unchanged. Full initial324 controls remain valid because evaluator bytes unchanged.

Recovery validated independently:44 bindings,40 sealed imports,484 normative field comparisons,324 unchanged controls,20323 original file hashes. Four wire prompts179031–179090 chars with full workspaces intact. Listener extraction11 requests, no added Action/Gold. Authorized continuation launched /home/sribd/Downloads/wangshu/tempoevo-incremental100-workers4-20261117_011424-resume1/launch.json; source bytes frozen until queue drain.

## GPT6 medium low20 eight-worker testing tempoevo-gpt6-medium-low20-workers8-20261117_112828
Spec: /home/sribd/Downloads/wangshu/tempoevo-gpt6-medium-low20-workers8-20261117_112828/env-spec.json
Reuse immutable solver/grader and CPU toolchains; no local GPU workload. Host40CPU/229GiB available RAM supports8 solver sessions; queue cap expanded and tested8,explicit provider capacity errors lower future concurrency8->6->4,never replay started calls. Current73 entries incl36candidate entries all already accepted; no reviews need changing.20 non-trained exact IDs ranked by gpt-6-sol/medium historical L:5/54validtrials;19<=50%,one next-lowest2/3;all have development exposure. One Action,48request cap,final-onlyGold,noA/B,no learning.
Documented zero-model validation invocation: execute single line in /home/sribd/Downloads/wangshu/tempoevo-gpt6-medium-low20-workers8-20261117_112828/prepare-command.sh VERBATIM from /home/sribd/Downloads/wangshu/temporal-contract-analyzer. Verify selected case/image identity,60 original/reference/negative Gold controls,20 current frozen protocol bindings with gpt-6-sol/medium and73 actual approvals. No model calls until independent validation passes.

GPT6low20 independently validated:20 frozen bindings,60 controls,1214 image files,73 actual approvals. Eight-worker adaptive queue launched: /home/sribd/Downloads/wangshu/tempoevo-gpt6-medium-low20-workers8-20261117_112828/launch.json. Exact modelgpt-6-sol/medium; retain all started-request usage. Source/runtime bytes frozen until queue completion.

## GPT6 low20 one-case read-guard correction tempoevo-gpt6-medium-low20-workers8-20261117_112828-readfix1
Spec: /home/sribd/Downloads/wangshu/tempoevo-gpt6-medium-low20-workers8-20261117_112828-readfix1/env-spec.json
Same immutable images/source/evaluators/73bank/model. Permit ONLY literal workspace file existence guards with existing read-only command bodies; writes,externalpaths,substitutions remain rejected. Original case had0Actions/0Gold,selection1request,contract2requests;newroot retains spent usage and selection,remainingContract10requests/oneAction24. Other19 valid scores never replayed.
Documented zero-model validation invocation: execute single line in /home/sribd/Downloads/wangshu/tempoevo-gpt6-medium-low20-workers8-20261117_112828-readfix1/prepare-command.sh VERBATIM from /home/sribd/Downloads/wangshu/temporal-contract-analyzer. Verify newbinding,oldsource/controls hashidentity,budget10/oneAction/onefinalGold,modelgpt-6-sol/medium,oldrawcaseunchanged. No model or newGold calls duringpreparation.

Read-guard validation clarification/fix: malformed shell punctuation such as &; is explicitly rejected as well as normal background commands. First readfix1 preparation had no model/Gold calls and is retained. Reprepare same case under current byte bindings via EXACT singleline /home/sribd/Downloads/wangshu/tempoevo-gpt6-medium-low20-workers8-20261117_112828-readfix2/prepare-command.sh from /home/sribd/Downloads/wangshu/temporal-contract-analyzer; all source/model/73bank/budget10/24/scorer controls unchanged. This invocation has zero models/Gold. Independent agent revalidation required before execution.

## GPT6.1 medium hardest50 ranks26-46 retest 8bb8cd7d
Spec: /home/sribd/Downloads/wangshu/tempoevo-sol61-medium-ranks26-46-workers8-20261117_155257/env-spec.json
Reuse pinned immutable solver/grader images and CPU toolchains; no GPU allocation or rebuild. New current61 experience snapshot and fixed GPT6.1medium.21development retests,8workers; single Action and final-onlyGold, nolearning or AB.
Documented zero-model command: execute the single line in /home/sribd/Downloads/wangshu/tempoevo-sol61-medium-ranks26-46-workers8-20261117_155257/prepare-command.sh VERBATIM from /home/sribd/Downloads/wangshu/temporal-contract-analyzer. Verify selected source/image hashes,63 original/reference/negative controls,21 prepared bindings,61 approvals and exactgpt-6.1-sol/medium profile. Fresh agent follows-doc verification required before model launch.

Ranks26-46 preflight READY:1274 source/image files,63 expected controls,21 frozen bindings,current61bank/all6evidence attachments. Independent report /home/sribd/Downloads/wangshu/tempoevo-sol61-medium-ranks26-46-workers8-20261117_155257/agent-follows-doc.json. No models called before this checkpoint.

Ranks26-46 launched:8 concurrent cases each produced non-denied PreModelRequest for gpt-6.1-sol; medium is frozen in all21protocols. Launch proof /home/sribd/Downloads/wangshu/tempoevo-sol61-medium-ranks26-46-workers8-20261117_155257/launch-verification.json. Runtime and bank remain frozen until queue completes.

## GPT6 medium same-training-core hard10 285fab58
Spec: /home/sribd/Downloads/wangshu/tempoevo-gpt6-medium-trainclusters-hard10-workers8-20261117_171557/env-spec.json
Reuse pinned immutable images/CPU toolchains; no GPU allocation or rebuild.10 non-trained cases in6 training70cores,all0/3 originalLatent;prior-test-exposed retest,61 currentapprovedbank,8 initialworkers.
Documented zero-model command: execute the single line in /home/sribd/Downloads/wangshu/tempoevo-gpt6-medium-trainclusters-hard10-workers8-20261117_171557/prepare-command.sh VERBATIM from /home/sribd/Downloads/wangshu/temporal-contract-analyzer. Verify selectedcase/image identity,30 original/reference/negative controls,10 protocol bindings,61 approved experiences plus all6evidence appendices,exactgpt-6-sol/medium. No model execution. Independent fresh agent-follows-doc READY required before launch.

Same-training-core hard10 READY:30 expected controls,10 frozen bindings,all selected cores covered by training70,zero known exact-source overlap,61 accepted bank/all6 appendices verified. Independent report /home/sribd/Downloads/wangshu/tempoevo-gpt6-medium-trainclusters-hard10-workers8-20261117_171557/agent-follows-doc.json. No model calls before this checkpoint.

Same-core hard10 launched:8 real concurrent case PreModelRequest hooks,all non-denied gpt-6-sol;medium frozen in all10protocols. Proof /home/sribd/Downloads/wangshu/tempoevo-gpt6-medium-trainclusters-hard10-workers8-20261117_171557/launch-verification.json. Runtime and61bank frozen until completion.

## GPT5.6sol medium untrained low30 716ef0f3
Spec: /home/sribd/Downloads/wangshu/tempoevo-gpt56-sol-medium-low30-untrained-workers8-20261117_180752/env-spec.json
Reuse pinned immutable CPU Docker images;no GPU/rebuild.30 known-nontraining IDs(25zero-pass1trial,5all-pass supplements),61approvedbank,8workers,exactgpt-5.6-sol/medium,priority.
Documented zero-model command: execute the single line in /home/sribd/Downloads/wangshu/tempoevo-gpt56-sol-medium-low30-untrained-workers8-20261117_180752/prepare-command.sh VERBATIM from /home/sribd/Downloads/wangshu/temporal-contract-analyzer. Verify selected source/image hashes,90 original/reference/negative controls,30 frozen testing bindings,61 approved entries/all6 evidence appendices,correcttargetmodel and budgets. Independent fresh agent-follows-doc READY before launch.

GPT5.6 low30 READY:30 independently verified bindings,90 expected controls,1905 matching source/image files,61 active approvals/all6 evidence appendices,74 known training/source IDs excluded,no divergences. Exactgpt-5.6-sol/medium/priority verified. Report /home/sribd/Downloads/wangshu/tempoevo-gpt56-sol-medium-low30-untrained-workers8-20261117_180752/agent-follows-doc.json. No models before readiness.

GPT5.6 low30 launched:8 actual concurrent case PreModelRequest hooks,all non-denied gpt-5.6-sol;medium frozen in all30protocols. Proof /home/sribd/Downloads/wangshu/tempoevo-gpt56-sol-medium-low30-untrained-workers8-20261117_180752/launch-verification.json. Runtime and61bank frozen until completion.

## GPT5.6medium Auto-Contract-only30 bf54d1db
Spec: /home/sribd/Downloads/wangshu/tempoevo-gpt56-sol-medium-autocontract30-workers8-20261117_211340/env-spec.json
Same30cases/model/images/publicsources/evaluator/Action24requests600sec as parent experience arm;no memory/selection/routing,Contract12+Action24=36 total.8workers,oneAction/finalGold,no learning. Reuse parent90 trusted controls only after exact source/image/evaluator verification;no extra Gold/model calls during preflight.
Documented zero-model command: execute the single line in /home/sribd/Downloads/wangshu/tempoevo-gpt56-sol-medium-autocontract30-workers8-20261117_211340/prepare-command.sh VERBATIM from /home/sribd/Downloads/wangshu/temporal-contract-analyzer. Independent fresh agent-follows-doc READY required,30bindings/emptybank/no-selection and paired-input identity checked before launch.

Auto-Contract-only30 READY:30 frozen bindings verified;1905 image/source files equal,parent90controls reused,no new Gold/models;empty approved snapshot/store,no selection/routing,exactgpt-5.6-sol/medium/priority,Contract12+Action24=36total. Source/runtime/model/evaluator/Action budgets match parent;parent bindings unchanged. Independent report /home/sribd/Downloads/wangshu/tempoevo-gpt56-sol-medium-autocontract30-workers8-20261117_211340/agent-follows-doc.json.

Auto-Contract-only30 launched:8 concurrent non-denied gpt-5.6-sol PreModelRequest hooks in Contract stage;all checked inputs experience=null,business_obligations=[],no routing/selection stages. Medium frozen in30protocols. Proof /home/sribd/Downloads/wangshu/tempoevo-gpt56-sol-medium-autocontract30-workers8-20261117_211340/launch-verification.json. Runtime unchanged from parent.

## GPT6.1medium same30 with61 experiences 382c6c75
Spec: /home/sribd/Downloads/wangshu/tempoevo-gpt61-sol-medium-same30-workers8-20261117_222652/env-spec.json
Same30cases as GPT5.6with-memory arm;only executionmodel/profile becomesgpt-6.1-sol/medium. Same61bank,source/images/runtime/evaluator/budgets,8workers,oneAction24requests600sec,total48,final-onlyGold. No learning/AB. Execution errors count as failures in headlinepass/30,raw error categories preserved.
Documented zero-model command: execute the single line in /home/sribd/Downloads/wangshu/tempoevo-gpt61-sol-medium-same30-workers8-20261117_222652/prepare-command.sh VERBATIM from /home/sribd/Downloads/wangshu/temporal-contract-analyzer. Reuse parent90trustedcontrols only after source/image/evaluator identity checks;no new Gold/modelcalls. Independent fresh agent-follows-doc READY required for30bindings,bank/model and paired original input equality.

GPT6.1same30 READY:30 fresh verified bindings,1905 matching source/image files,90 parent controls reused withidentity checks;61 accepted current experiences/six evidence appendices intact;10180 parentfiles unchanged. Onlymodel/profile andrequiredoutputpaths differ. No newmodels/Gold preflight. Report /home/sribd/Downloads/wangshu/tempoevo-gpt61-sol-medium-same30-workers8-20261117_222652/agent-follows-doc.json.

GPT6.1same30 launched:8 actual concurrent case PreModelRequest hooks,all non-denied gpt-6.1-sol;medium frozen in30protocols,61bank unchanged. Proof /home/sribd/Downloads/wangshu/tempoevo-gpt61-sol-medium-same30-workers8-20261117_222652/launch-verification.json. Headline success pass/30,execution errors counted failures;runtime frozen until completion.

## GPT6.1medium fresh Latent30 747055e9
Spec: /home/sribd/Downloads/wangshu/tempoevo-gpt61-sol-medium-latent30-workers8-20261117_231922/env-spec.json
Reuse pinned CPU Docker images, no GPU or rebuild. Same30 originals; new independent outputs, gpt-6.1-sol/medium,8 workers, no memory/Contract/routing/selection, oneAction24requests600sec and final-onlyGold. Execution errors excluded from valid denominator. Reuse90 source/evaluator-verified controls only, never previous solver outputs. Helper CLI now exposes existing baseline engine mode.
Documented zero-model command: execute the single line in /home/sribd/Downloads/wangshu/tempoevo-gpt61-sol-medium-latent30-workers8-20261117_231922/prepare-command.sh VERBATIM from /home/sribd/Downloads/wangshu/temporal-contract-analyzer. Independent fresh agent-follows-doc READY required: verify30 bindings, emptybank/store,total24, original-source equality and fresh states.

Fresh Latent30 READY: independent report /home/sribd/Downloads/wangshu/tempoevo-gpt61-sol-medium-latent30-workers8-20261117_231922/agent-follows-doc.json;30 baseline bindings,emptybank/store,1905 image/source matches,90 verified reused controls,no newpreflightGold/models.39 synthetic state-machine tests passed.

Fresh Latent30 launched:8 distinct non-denied GPT6.1-sol PreModelRequest hooks in Action stage;medium fixed,emptybank,nullContract/nullExperience. Proof /home/sribd/Downloads/wangshu/tempoevo-gpt61-sol-medium-latent30-workers8-20261117_231922/launch-verification.json. Runtime frozen until completion.

## GPT6.1medium Auto-Contract-only30 cb7d8c26
Spec: /home/sribd/Downloads/wangshu/tempoevo-gpt61-sol-medium-autocontract30-workers8-20261117_234344/env-spec.json
Warm reuse pinned immutable CPU Docker images; no GPU/rebuild. Same30 originals/model/evaluator/Action24requests600sec as Latent and memory arms. No memory/routing/selection. Contract12+Action24=36 requests total;oneAction and final-onlyGold;8workers,explicit-capacity fallback8/6/4,no test learning. Execution errors excluded from valid denominator. Trusted90 calibration controls reused only after source/evaluator/image identity checks;no solver outputs reused.
Documented zero-model command: execute the single line in /home/sribd/Downloads/wangshu/tempoevo-gpt61-sol-medium-autocontract30-workers8-20261117_234344/prepare-command.sh VERBATIM from /home/sribd/Downloads/wangshu/temporal-contract-analyzer. Independent fresh agent-follows-doc READY required before launch:30 verified fresh testing bindings,emptybank/store,exactgpt-6.1-sol/medium/priority,Contract12/Action24,total36 and source equality.

Auto-Contract-only30 READY: independent report /home/sribd/Downloads/wangshu/tempoevo-gpt61-sol-medium-autocontract30-workers8-20261117_234344/agent-follows-doc.json;30 Auto-Contract-only bindings,emptybank/store,1905 image/source matches,90 verified reused controls,no newpreflightGold/models.Contract12+Action24=36 total; final-only Gold.

Auto-Contract-only30 launched:8 distinct non-denied GPT6.1-sol PreModelRequest hooks in Contract stage;medium fixed,emptybank,no experience/selection/routing. Proof /home/sribd/Downloads/wangshu/tempoevo-gpt61-sol-medium-autocontract30-workers8-20261117_234344/launch-verification.json. Runtime frozen until completion.

## GPT5.6medium train70 two-arm replay worker1 9eb3ff65
Spec: /home/sribd/Downloads/wangshu/tempoevo-gpt56-sol-medium-train70-twoarms-worker1-20261118_002327/env-spec.json
Reuse pinned CPU Docker images, no GPU/rebuild. Same fixed70 training IDs/24cores,140 jobs,GLOBAL1worker including calibration. Auto-Contract70 then with-experience70; V8-compatible up to3Actions24requests600sec each;public syntax plus trainingGold acceptance,verdict-only feedback;source-bound-v8 retrieval. Banks fixed0/61 from current approved library;contains training sources,training-set replay not independent test or reconstruction of old online run. Candidate extractions archived only,no publication/approval/online reuse. Execution errors excluded from final valid denominator;post-acceptance extraction errors preserve valid repair acceptance.
Documented zero-model command: execute the single line in /home/sribd/Downloads/wangshu/tempoevo-gpt56-sol-medium-train70-twoarms-worker1-20261118_002327/prepare-command.sh VERBATIM from /home/sribd/Downloads/wangshu/temporal-contract-analyzer. Verify140 frozen configs/public inventories and bothbanks,70case manifest/image hashes,6 first-case original/reference/negative public+Gold controls and2 fresh paired protocols. Remaining69 case controls/shared across arms and remaining138 trajectories are intentionally prepared serially just in time; no overlap with model work. Fresh independent agent-follows-doc READY required before execution.

GPT5.6 train70 replay READY:140 frozen configs,70IDs/24cores,9397image hashes,6 shared first-case controls,2 paired first-case protocols;independent /home/sribd/Downloads/wangshu/tempoevo-gpt56-sol-medium-train70-twoarms-worker1-20261118_002327/agent-follows-doc.json. Remaining preparation/calibration serial just-in-time;no paid models before this checkpoint.3 accounting regression tests passed.
