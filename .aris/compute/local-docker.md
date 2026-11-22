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

GPT5.6train70 replay launched:one non-denied actualgpt-5.6-sol Contract request,medium fixed,one activeglobaljob,max3Actions,emptybank in firstarm;with-experience61arm queued after70. Proof /home/sribd/Downloads/wangshu/tempoevo-gpt56-sol-medium-train70-twoarms-worker1-20261118_002327/launch-verification.json. Runtime/banks frozen until completion.

## Train70 explicit split recovery (unchanged runtime/images)
Recovery root: /home/sribd/Downloads/wangshu/tempoevo-gpt56-sol-medium-train70-twoarms-worker1-20261118_002327-split-recovery
Confirmed setup defect: replay configs omitted final cohort split registry and12 known train70 IDs hit old default testing reservations. Bind the EXISTING final incremental70/30 split explicitly; do not disable guards/reclassify cases/change global registry.24 never-started tasks only (12IDsx2arms),identical model/banks/originalsources/budgets, no prior model scores reused or overwritten. Preserve source parent frozen inputs/runtime. Zero-model preparation reuses existing72 valid Gold/public controls;24 new protocol bindings. Recovery execution acquires SAME parent queue.lock,waiting until original140jobs finish,GLOBAL1worker preserved. Prior valid scores untouched;2 tool-policy failures remain unscored.
Documented zero-model command: execute the single line in /home/sribd/Downloads/wangshu/tempoevo-gpt56-sol-medium-train70-twoarms-worker1-20261118_002327-split-recovery/prepare-command.sh VERBATIM from /home/sribd/Downloads/wangshu/temporal-contract-analyzer. Fresh independent agent-follows-doc READY required before scheduling recovery.

## Train70 switch to8workers (same immutable runtime/images/model)
Root /home/sribd/Downloads/wangshu/tempoevo-gpt56-sol-medium-train70-twoarms-worker1-20261118_002327-workers8-20261118_101523
User explicitly authorizes8threads. Old original scheduler PID2627886 paused with SIGSTOP ONLY; active modelCLI3046769 continues unaffected. Old recovery waiter PID2992086 stopped before models. Retain108completed model runs (105validscores+3executioninvalid);32remainingjobs comprise24neverstarted splitrecoveries +7originalunstarted +1observer of liveCLI. NewThreadPoolExecutor8 has observerFIRST occupying1slot until existingCLI completes,so7new+1existing initially,then8newmax. Never rerun scored/invalid/started tasks. Same0/61banks,max3Actions,V8sourcebound,budgets. All newconfigs bind unchanged final70/30split;no globalregistry/runtime changes. Shared prior controls reused afterhashvalidation. Oldscheduler remainspaused until existingCLI finishes; no schedulingrace/duplicate.
Documented zero-model command: execute single line in /home/sribd/Downloads/wangshu/tempoevo-gpt56-sol-medium-train70-twoarms-worker1-20261118_002327-workers8-20261118_101523/prepare-command.sh VERBATIM from /home/sribd/Downloads/wangshu/temporal-contract-analyzer. Fresh independent agent-follows-doc READY required:140totaluniquejobkeys=108retained+32remaining,31freshbindings+1existingactive protocol,source/model/bank/controls unchanged,8slotglobalbound. No paidnewmodelcalls in preparation.

Train70 handoff8workers launched:8 distinct non-denied realgpt-5.6-sol Contract requests,medium frozen;executor peak8;old coordinator remainspaused,oldwaiterstopped,already-completed CLIobservedwithoutreplay. Proof /home/sribd/Downloads/wangshu/tempoevo-gpt56-sol-medium-train70-twoarms-worker1-20261118_002327-workers8-20261118_101523/launch-verification.json. Original105validscores+3invalid retained.

## GPT5.6 medium fixed30 library-size20 ablation 78340abe
Spec /home/sribd/Downloads/wangshu/tempoevo-gpt56-sol-medium-memory20-test30-workers8-20261118_131744/env-spec.json
Warm reuse immutable CPU Docker images/runtime, noGPU/rebuild. User chose library-size ablation0/20/61,NOT historical training checkpoints. Same original30testingcases/gpt5.6medium/priority/Action24req600sec/final-onlyGold as old61arm;only20eligible entries via frozen snapshot,full61auditlibrary preserved outsidemodelcontainer,hidden41neverrecalled. Sample20 by Random(20261118) permutation of sorted61bundlehashes,freeze before modelruns,no score-based selection. OneAction,Selection12+Contract12+Action24=48cap,8workers,capacityfallback8/6/4,no learning,errors excluded fromvaliddenominator. Explicit split registry binds originaltraining70 and these fixedtest30;all30permissionchecks pass. Reuse90 trusted controls after exactsource/image/evaluatorhash checks;0/61oldmodeloutcomes reused separately forcurve,never used toselect20.
Documented zero-model command: execute single line in /home/sribd/Downloads/wangshu/tempoevo-gpt56-sol-medium-memory20-test30-workers8-20261118_131744/prepare-command.sh VERBATIM from /home/sribd/Downloads/wangshu/temporal-contract-analyzer. Independent fresh agent-follows-doc READY required:30bindings,20entrysnapshot subsetofparent61,all auditbundle/decision bytes preserved,fulloriginalbank unchanged,1905image-source hashes,90expectedcontrols,newtestroles explicit,all originalinputs/model/runtime/budgets equalparent61. Confirmmodelpayload cannot accesshidden41.

Memory20preflight correction BEFORE MODELS: defaultPATH pointed to newerCodex c147ac3b than paired0/61arms. Rejectedzero-modelbatch retained in /home/sribd/Downloads/wangshu/tempoevo-gpt56-sol-medium-memory20-test30-workers8-20261118_131744/preflight-rejected-cli. Wrapper now prepends originalCodexdirectory to childPATH and asserts EXACToldbinarypath+SHA c3dea068c8794f1764051c1fd182ff0524352bbddf2f2638e72386b9b7b74368. Updatedspec /home/sribd/Downloads/wangshu/tempoevo-gpt56-sol-medium-memory20-test30-workers8-20261118_131744/env-spec.json. ImmutableDocker/core/model/cases/bank20unchanged,0models/newGold. Documented command remains single line in /home/sribd/Downloads/wangshu/tempoevo-gpt56-sol-medium-memory20-test30-workers8-20261118_131744/prepare-command.sh; rerunVERBATIM. Fresh independent follow-doc must certify30bindings plus binary/evaluatorhash parity beforelaunch.

Memory20 READY:30freshbindings,exactoldCodex c3dea068 pinned,parent runtime/images/model/action budgets retained;1905imagefiles/90controls verified,20unmodified approvedbundles selectedseed20261118,hidden41neverrecalled. Independent /home/sribd/Downloads/wangshu/tempoevo-gpt56-sol-medium-memory20-test30-workers8-20261118_131744/agent-follows-doc.json.0/61oldarms only reused forcurve. No paidmodelsbeforecheckpoint.

Memory20 launched:8 distinct non-deniedgpt5.6sol PreModelRequests,allselectionpayloads showexact20subset,hidden41absent,medium+oldCLI c3dea068pinned. Proof /home/sribd/Downloads/wangshu/tempoevo-gpt56-sol-medium-memory20-test30-workers8-20261118_131744/launch-verification.json. Full61bank unchanged;post-scorecurve0/20/61uses commonvalidintersection.


## Completed library-size ablation — 2026-11-18
Final repository summary: experiments/testing-runs/gpt56-library-size-ablation-20261118/README.md.
Warm reuse: original immutable CPU solver/grader images, gpt-5.6-sol medium/priority, pinned Codex SHA256 c3dea068c8794f1764051c1fd182ff0524352bbddf2f2638e72386b9b7b74368; no GPU workload or model-weight training. Selection12 + Contract12 + Action24 =48 request cap, one Action600seconds, final-onlyGold, frozen memory.
40-entry snapshot is the first40 of the seed20261118 permutation, includes20, hides21 of61. Original attempt at /home/sribd/Downloads/wangshu/tempoevo-gpt56-sol-medium-memory40-test30-workers8-20261118_152316 retained2scores and28routing failures; /home/sribd/Downloads/wangshu/tempoevo-gpt56-sol-medium-memory40-recovery28-20261118_1703 retained8routing failures and20unstarted jobs.
Old CLI removed by editor update was restored from official26.51106.51428 package with exact original SHA256; restoration receipt: /home/sribd/Downloads/wangshu/tempoevo-gpt56-sol-medium-memory40-recovery28-20261118_175505/cli-restoration.json.
Successful40 recovery: /home/sribd/Downloads/wangshu/tempoevo-gpt56-sol-medium-memory40-recovery28-20261118_175505; independent preflight READY, one real pilot before8workers; completed18:24Asia/Shanghai,24/28new plus1/2retained =25/30. Frozen sources/model/bank/runtime/budgets retained.
Successful61 recovery: /home/sribd/Downloads/wangshu/tempoevo-gpt56-sol-medium-memory61-recovery2-20261118_203713; independent preflight READY,2workers, exactlytwooriginal execution-invalid IDs,28old scored outcomes unchanged; completed20:46Asia/Shanghai,2/2new plus23/28retained =25/30.
Current raw0/20/40/61:10/29,18/30,25/30,25/30. All-four shared29:10/29,17/29,24/29,24/29. Unknown historical usage remains unknown.
Documented zero-model checks (prepared trajectories only): each recovery's prepare.py --validate or manage.py verify; executed run roots are immutable and must not be relaunched in place. Validation reports and all original paid attempts remain at their external roots; recovery scripts create new trajectories and never retry valid behavioral scores.
Repository duplicate projections and obsolete plots were removed only after exact matching external copies; provenance and file hashes are retained with the compact summary.

## GPT5.6train70 retry5 execution errors (fixed61bank)
Root /home/sribd/Downloads/wangshu/tempoevo-gpt56-sol-medium-train70-error5-retry-20261118_221111
User requests only5unscored with-memory cases rerun; original52pass/13fail/5invalid. Fresh originalpublicsources,same61approvedbank/model/binaryc147ac/servicepriority, V8frozen sourcebound,max3Actions24req600sec,total132;5cases parallel(max8limit),no memorypublication. Fixread-command grammar: allowstdout-onlysort withrestrictedflags, preserveunquotednewlines/comments/continuations asstatementboundaries;continue denyingwrites/outsidepaths.48targetedtests passed. Parentlibrary and65validscores untouched;original5errorreceipts retained. Priorusercommit e02efbe0 relocatedcasecatalog/defaultsplit; ownrun-local registry binds original70/30 members using its local100CSV, avoiding deletedlegacyselectionpaths. Expectedruntime delta vsoldcases: ONLYread_policy.py andpreexisting defaultregistrydata change; no businessprompt/model/scorechange. Reuse30 expectedvalid calibrationcontrols afterhashcheck, verifyselectedbenchmarkfilehashes.
Documented zero-model command: execute single line in /home/sribd/Downloads/wangshu/tempoevo-gpt56-sol-medium-train70-error5-retry-20261118_221111/prepare-command.sh VERBATIM from /home/sribd/Downloads/wangshu/temporal-contract-analyzer. Fresh independent agent-follows-doc READY required:5freshbindings,unmodifiedtask/source/bank/model/binary/evaluator/budgets,all5trainingroles,no staged oldcandidate reuse,no changesother65scores.

Retry5 READY:5freshbindings and30reusedcontrolresults independentlyverified, same61bank/CLIc147/model/source/scorer/budgets, isolatedreadonlygrammarfix48tests. Original65validscores andall5olderrorsretained. Independentreport /home/sribd/Downloads/wangshu/tempoevo-gpt56-sol-medium-train70-error5-retry-20261118_221111/agent-follows-doc.json. No paidmodelsbeforethischeckpoint.

Train70error5 launched:5actual parallelgpt5.6sol non-denied PreModelRequest hooks;workerlimit8,5casesonly. Fixed61bank,medium,max3Action;65previousscores retained. Proof /home/sribd/Downloads/wangshu/tempoevo-gpt56-sol-medium-train70-error5-retry-20261118_221111/launch-verification.json.

## GPT6.1sol low fixed30 full61 worker1 961f7664
Root /home/sribd/Downloads/wangshu/tempoevo-gpt61-sol-low-same30-worker1-20261119_001852
Spec /home/sribd/Downloads/wangshu/tempoevo-gpt61-sol-low-same30-worker1-20261119_001852/env-spec.json
User requests same30fixedtestcases,gpt-6.1-sol withreasoning_effort=low,GLOBAL1worker. WarmCPU Docker reuse,noGPU/rebuild. Samefull61snapshot and originalpublicinputs/evaluator/budgets as pairedmedium27/30arm. ExactoldCLI c3dea068 pinned viaPATH in zero-model wrapper;parent61guidance unmodified. Businesssource selection12+Contract12+Action24req600sec=48cap,oneAction/finalGold,no learning/noAB. Explicit run-owned100CSV and70/30registry,all30testingroles verified. Reuse90prior expectedtrustedcontrols only aftersource/image/evaluator identity checks. Currentreadonlygrammarfix/defaultregistry differ from historicalmedium;recorded as infrastructure deltas,not silently claimed identicalruntime. Modelprofile changesonlyeffort+profileID. Executioninvalid excluded from valid-score denominator.
Documented zero-model command: execute single line in /home/sribd/Downloads/wangshu/tempoevo-gpt61-sol-low-same30-worker1-20261119_001852/prepare-command.sh VERBATIM from /home/sribd/Downloads/wangshu/temporal-contract-analyzer. Fresh independentagent-follows-doc READY required for30freshbindings,lowmodelsettings,oldbinaryhash/full61bank/source/scorerparity,1905imagehashes,90controlreceipts;onlydeclaredinfrastructure runtime deltas allowed.

GPT6.1LOWfixed30 READY:30freshbindings,full61bank/source/task/scorer/images/budgets unchanged,lowprofile andexactCLI0.167c3dea068 pinned,1905imagehashes/90controls reused,explicit30testroles,oneAction/finalGold,oneworker. Independent /home/sribd/Downloads/wangshu/tempoevo-gpt61-sol-low-same30-worker1-20261119_001852/agent-follows-doc.json. No modelsbeforecheckpoint.

GPT6.1LOW serial queue started:real non-deniedmodelrequest andactualCLI lowflag verified;peakactive1,full61snapshot. First response completion pending atstartup checkpoint (not a behavioral outcome). Proof /home/sribd/Downloads/wangshu/tempoevo-gpt61-sol-low-same30-worker1-20261119_001852/launch-verification.json.

GPT6.1LOWfixed30 launched:real non-deniedgpt6.1sol request ANDcompletedresponse,actualCLIflag model_reasoning_effort=low verified,peakactive1. Proof /home/sribd/Downloads/wangshu/tempoevo-gpt61-sol-low-same30-worker1-20261119_001852/launch-verification.json. Full61snapshot frozen,nolearning.


## GPT5.6 Latent+experience fixed30 workers8 df6547ec
Root /home/sribd/Downloads/wangshu/tempoevo-gpt56-sol-medium-latent-experience-test30-workers8-20261122_024039
Warm reuse of original immutable solver/grader images and exact Codex c3dea068; no rebuild or local GPU allocation. Frozen61 bank,29 nonempty and1 empty historical GPT5.6 deliveries; no new selection or Contract. One Action24requests/600seconds, final-onlyGold, no learning. Current merged runtime/guard/scorer diagnostic deltas are disclosed in README.
Zero-model preflight:90 fresh valid/expected calibration controls,1905 matching image files,all30 fixed test source/model/bank/delivery/budget bindings. Documented invocation: python3 -B /home/sribd/Downloads/wangshu/tempoevo-gpt56-sol-medium-latent-experience-test30-workers8-20261122_024039/validate.py (before launch only). Fresh independent agent report ready:true at independent-validation.json.
Launched with8workers;8 real non-deniedgpt5.6 model request cases,mediumflag verified in actual CLI commands,at least1 completed response. Launch proof /home/sribd/Downloads/wangshu/tempoevo-gpt56-sol-medium-latent-experience-test30-workers8-20261122_024039/launch-verification.json. Background supervisor archives final results and does not retry valid behavioral failures.
