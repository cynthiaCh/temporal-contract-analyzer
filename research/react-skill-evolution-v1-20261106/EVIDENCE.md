# 实际工具、控制事件、补丁与可信评分

只依据实际输出和差异复核；controller机械完成门与语义成功分开。

## development/transfer-progress-composition-v4-vanilla/B/K0/1

[prompt](trials/reports-experiments/e-0cf46cd354254413/jobs/j-001/prompt.md) · [events](trials/reports-experiments/e-0cf46cd354254413/jobs/j-001/events.jsonl) · [patch](trials/reports-experiments/e-0cf46cd354254413/jobs/j-001/patch.diff) · [control](trials/reports-experiments/e-0cf46cd354254413/jobs/j-001/control/hook-events.jsonl) · [result/usage](trials/reports-experiments/e-0cf46cd354254413/jobs/j-001/result.json)

原断言显式失败：[]；未发出/不可逐项比较：[]。保留原机械缺项按损失的字段，不将其等同实际失败。

[可信原始评分](trials/reports-experiments/e-0cf46cd354254413/evaluations/v-7c02822eed2e4ce2/j-001/oracle/stdout.json)；UNDERREACH 8/10；原通过检查丢失 []，断言丢失 []。

|events行|工具|退出/状态|实际命令或文件|
|---:|---|---|---|
|7|command_execution|0|/usr/bin/bash -lc "rg --files -g '"'!node_modules'"'"|
|9|command_execution|0|/usr/bin/bash -lc 'for f in src/progress.js src/transfer.js src/queue.js src/panel.js src/progress-source.js src/telemetry.js src/retry.js src/notice.js package.json; do echo "$f"; nl -ba "$f"; done'|
|12|command_execution|0|/usr/bin/bash -lc "cat > /stage/checkpoint.json <<'EOF' ↵ {\"state\":\"inspect\",\"action_basis\":\"Restore warm panel progress and prevent older decoded full frames from repainting; preserve queue, history, telemetry and lifecycle behavior.\",\"applicability\":\"applicable\",\"evidence\":[\"src/progress.js:3\",\"src/progress.js:9\",\"src/progress-source.js:26\",\"src/progress-source.js:28\",\"src/transfer.js:11\",\"|
|14|file_change|completed|[{'path': '/workspace/src/progress.js', 'kind': 'update'}]|
|16|file_change|completed|[{'path': '/workspace/src/queue.js', 'kind': 'update'}]|
|18|file_change|completed|[{'path': '/workspace/src/queue.js', 'kind': 'update'}]|
|21|command_execution|0|/usr/bin/bash -lc "node --input-type=module <<'EOF' ↵ import assert from 'node:assert/strict'; ↵ import { createTransferWorkspace, createProgressFeed, collectProgressTelemetry } from './src/workspace.js'; ↵ const history=[], shown=[], queued=[], records=[], cancels=[]; ↵ const pending=new Map(); ↵ const feed=createProgressFeed({initialPacket:'warm',decode:p=>pending.has(p)?pending.get(p).promise:p}); ↵ const workspac|
|23|command_execution|128|/usr/bin/bash -lc 'git diff -- src/progress.js src/queue.js; git status --short'|
|25|command_execution|0|/usr/bin/bash -lc "cat > /stage/checkpoint.json <<'EOF' ↵ {\"state\":\"repair_validate\",\"action_basis\":\"Warm start emits synchronously before old panel subscription; decoded frames may settle out of arrival order.\",\"evidence\":[\"src/progress.js:3\",\"src/progress.js:9\",\"src/progress-source.js:26\",\"src/progress-source.js:28\",\"src/queue.js:12\",\"src/queue.js:14\",\"src/telemetry.js:9\",\"src/transfer.js:1|

控制决定：{'observe': 36, 'continue-with-observation': 5, 'deny-edit-for-evidence': 1, 'allow-stop': 1}；同session=True；底层请求11。

## development/download-polling-restoration-low-cue-react18/B/K0/1

[prompt](trials/reports-experiments/e-1ea2e07039b0494b/jobs/j-001/prompt.md) · [events](trials/reports-experiments/e-1ea2e07039b0494b/jobs/j-001/events.jsonl) · [patch](trials/reports-experiments/e-1ea2e07039b0494b/jobs/j-001/patch.diff) · [control](trials/reports-experiments/e-1ea2e07039b0494b/jobs/j-001/control/hook-events.jsonl) · [result/usage](trials/reports-experiments/e-1ea2e07039b0494b/jobs/j-001/result.json)

原断言显式失败：[]；未发出/不可逐项比较：[]。保留原机械缺项按损失的字段，不将其等同实际失败。

[可信原始评分](trials/reports-experiments/e-1ea2e07039b0494b/evaluations/v-fc40cb6f2b754d16/j-001/oracle/stdout.json)；PASS 8/8；原通过检查丢失 []，断言丢失 []。

|events行|工具|退出/状态|实际命令或文件|
|---:|---|---|---|
|7|command_execution|0|/usr/bin/bash -lc "rg --files -g '"'!node_modules'"' -g '"'!package-lock.json'"'"|
|9|command_execution|0|/usr/bin/bash -lc "rg -n \"usePreparation\|DownloadDialog\|schedulePreparationRetry\|pending\|ready\|completed\" . -g '"'!node_modules'"'"|
|11|command_execution|0|/usr/bin/bash -lc 'nl -ba src/BackgroundExportPanel.jsx'|
|13|command_execution|0|/usr/bin/bash -lc 'nl -ba package.json'|
|15|command_execution|0|/usr/bin/bash -lc 'nl -ba src/usePreparation.js'|
|17|command_execution|0|/usr/bin/bash -lc 'nl -ba src/preparation-api.js'|
|19|command_execution|0|/usr/bin/bash -lc 'nl -ba src/DownloadDialog.jsx'|
|22|command_execution|0|/usr/bin/bash -lc "cat > /stage/checkpoint.json <<'EOF' ↵ {\"state\":\"inspect\",\"action_basis\":\"Pending preparation must be checked again and completion recorded only when ready.\",\"evidence\":[\"/workspace/src/usePreparation.js:18\",\"/workspace/src/usePreparation.js:23\",\"/workspace/src/usePreparation.js:32\",\"/workspace/src/preparation-api.js:10\",\"/workspace/src/BackgroundExportPanel.jsx:22\"],\"observati|
|24|command_execution|0|/usr/bin/bash -lc "cat > src/usePreparation.js <<'EOF' ↵ \"use strict\"; ↵  ↵ const React = require(\"react\"); ↵ const api = require(\"./preparation-api.js\"); ↵  ↵ function usePreparation(initialToken) { ↵   const state = React.useRef({ ↵     visible: true, ↵     loading: false, ↵     retryScheduled: false, ↵     checkCount: 0, ↵     completed: [], ↵     token: [REDACTED_SECRET] ↵   }); ↵   const visit = React.useR|
|26|command_execution|129|/usr/bin/bash -lc 'git diff -- src/usePreparation.js'|
|28|command_execution|129|/usr/bin/bash -lc 'git diff --check'|
|30|command_execution|0|/usr/bin/bash -lc "node -e \"for(const x of ['react-test-renderer','jsdom','react-dom/client']) {try {console.log(x,require.resolve(x))} catch {console.log(x,'unavailable')}}\""|
|33|command_execution|0|/usr/bin/bash -lc "cat > /tmp/check-preparation.js <<'EOF' ↵ const assert = require('node:assert/strict'); ↵ const Module = require('node:module'); ↵ const original = Module._load; ↵ let slots = [], cursor = 0, cleanup; ↵ const fakeReact = { ↵   useRef(value) { return slots[cursor++] \|\|= { current: value }; }, ↵   useReducer() { cursor++; return [0, () => {}]; }, ↵   useEffect(effect) { cursor++; if ("'!cleanup) cl|
|35|command_execution|0|/usr/bin/bash -lc "cat > /stage/checkpoint.json <<'EOF' ↵ {\"state\":\"repair_validate\",\"action_basis\":\"Dialog preparation now polls pending results and records completion only for ready results.\",\"evidence\":[\"/workspace/src/usePreparation.js:18\",\"/workspace/src/usePreparation.js:34\",\"/workspace/src/usePreparation.js:42\",\"/workspace/src/usePreparation.js:68\",\"/workspace/src/preparation-api.js:10\"],\"|
|39|command_execution|0|/usr/bin/bash -lc 'cat /stage/checkpoint.json'|
|41|command_execution|0|/usr/bin/bash -lc 'nl -ba src/usePreparation.js'|
|44|command_execution|0|/usr/bin/bash -lc 'node --check src/usePreparation.js'|
|45|command_execution|0|/usr/bin/bash -lc 'node /tmp/check-preparation.js'|
|47|command_execution|0|/usr/bin/bash -lc "mkdir -p test ↵ cp /tmp/check-preparation.js test/preparation.test.js ↵ python3 - <<'PY' ↵ p='test/preparation.test.js' ↵ s=open(p).read().replace(\"require('/workspace/src/usePreparation.js')\", \"require('../src/usePreparation.js')\") ↵ open(p,'w').write(s) ↵ PY ↵ node test/preparation.test.js"|
|49|command_execution|0|/usr/bin/bash -lc 'nl -ba test/preparation.test.js \| tail -n 35'|
|51|command_execution|0|/usr/bin/bash -lc "cat > /stage/checkpoint.json <<'EOF' ↵ {\"state\":\"repair_validate\",\"action_basis\":\"Pending dialog preparation must be retried and completion delivered only after ready.\",\"evidence\":[\"/workspace/src/usePreparation.js:42\",\"/workspace/src/usePreparation.js:44\",\"/workspace/src/usePreparation.js:51\",\"/workspace/src/usePreparation.js:54\",\"/workspace/src/usePreparation.js:76\",\"/workspa|
|55|command_execution|0|/usr/bin/bash -lc 'ls -l /stage/checkpoint.json src/usePreparation.js test/preparation.test.js'|
|57|command_execution|0|/usr/bin/bash -lc 'rg -n "maintenance_status\|validation_commands\|changed_paths\|reason" /stage/checkpoint.json'|
|59|command_execution|0|/usr/bin/bash -lc 'node --check src/usePreparation.js && node --check test/preparation.test.js && node test/preparation.test.js'|
|61|command_execution|0|/usr/bin/bash -lc "python3 - <<'PY' ↵ import json ↵ p='/stage/checkpoint.json' ↵ d=json.load(open(p)) ↵ d['observations']='After both workspace changes: node --check src/usePreparation.js && node --check test/preparation.test.js && node test/preparation.test.js exited 0; output: PASS pending retry, ready completion, close/reopen cancellation, stale result.' ↵ d['validation_commands']=['node --check src/usePreparation|

控制决定：{'observe': 79, 'continue-with-observation': 4, 'continue-same-session': 2, 'allow-stop-with-unresolved-limit': 1}；同session=True；底层请求16。

## development/download-polling-restoration-low-cue-react18/B/K1/1

[prompt](trials/reports-experiments/e-a2a7d797860949bb/jobs/j-001/prompt.md) · [events](trials/reports-experiments/e-a2a7d797860949bb/jobs/j-001/events.jsonl) · [patch](trials/reports-experiments/e-a2a7d797860949bb/jobs/j-001/patch.diff) · [control](trials/reports-experiments/e-a2a7d797860949bb/jobs/j-001/control/hook-events.jsonl) · [result/usage](trials/reports-experiments/e-a2a7d797860949bb/jobs/j-001/result.json)

原断言显式失败：[]；未发出/不可逐项比较：[]。保留原机械缺项按损失的字段，不将其等同实际失败。

[可信原始评分](trials/reports-experiments/e-a2a7d797860949bb/evaluations/v-a87725d459514b6c/j-001/oracle/stdout.json)；UNDERREACH 7/8；原通过检查丢失 []，断言丢失 []。

|events行|工具|退出/状态|实际命令或文件|
|---:|---|---|---|
|7|command_execution|0|/usr/bin/bash -lc "pwd && rg --files -g '"'!node_modules'"' -g '"'!*.lock'"' && rg -n \"usePreparation\|DownloadDialog\|schedulePreparationRetry\|checkPreparation\" . -g '"'!node_modules'"'"|
|9|command_execution|0|/usr/bin/bash -lc 'nl -ba src/usePreparation.js && nl -ba src/BackgroundExportPanel.jsx && nl -ba src/preparation-api.js && cat package.json && ls -la'|
|12|command_execution|0|/usr/bin/bash -lc "cat > /stage/checkpoint.json <<'EOF' ↵ {\"state\":\"inspect\",\"action_basis\":\"Download dialog must poll pending preparation until ready; hook currently stops on pending.\",\"evidence\":[\"src/DownloadDialog.jsx:7\",\"src/usePreparation.js:18\",\"src/usePreparation.js:23\",\"src/usePreparation.js:32\",\"src/usePreparation.js:36\",\"src/preparation-api.js:10\",\"src/BackgroundExportPanel.jsx:22\"]|
|14|file_change|completed|[{'path': '/workspace/src/usePreparation.js', 'kind': 'update'}]|
|16|command_execution|129|/usr/bin/bash -lc "node -e \"for(const x of ['react','react-dom','react-dom/test-utils','jsdom']) {try {console.log(x,require.resolve(x))} catch(e) {console.log(x,'missing')}}\" && node --check src/usePreparation.js && git diff -- src/usePreparation.js"|
|19|command_execution|0|/usr/bin/bash -lc "cat > /tmp/verify-preparation.js <<'EOF' ↵ const assert = require('node:assert/strict'); ↵ const Module = require('node:module'); ↵ const originalLoad = Module._load; ↵ let cleanup; ↵ Module._load = function (name, parent, main) { ↵   if (name === 'react') return { ↵     useRef(value) { return { current: value }; }, ↵     useReducer() { return [0, () => {}]; }, ↵     useEffect(effect) { cleanup = e|
|21|command_execution|0|/usr/bin/bash -lc "node --check src/usePreparation.js && node /tmp/verify-preparation.js && nl -ba src/usePreparation.js \| sed -n '1,110p'"|
|23|command_execution|0|/usr/bin/bash -lc "cat > /stage/checkpoint.json <<'EOF' ↵ {\"state\":\"repair_validate\",\"action_basis\":\"Hook must retry pending preparation and complete only on ready.\",\"evidence\":[\"src/usePreparation.js:4\",\"src/usePreparation.js:36\",\"src/usePreparation.js:43\",\"src/usePreparation.js:53\",\"src/usePreparation.js:74\",\"src/preparation-api.js:10\",\"src/DownloadDialog.jsx:7\"],\"observations\":\"node --ch|
|27|command_execution|0|/usr/bin/bash -lc "cat /stage/checkpoint.json && node --check src/usePreparation.js && node /tmp/verify-preparation.js && stat -c '%n %s bytes' src/usePreparation.js /stage/checkpoint.json"|
|29|command_execution|0|/usr/bin/bash -lc "python3 - <<'PY' ↵ import json ↵ p='/stage/checkpoint.json' ↵ with open(p) as f: data=json.load(f) ↵ data['observations']='Post-edit rerun: node --check src/usePreparation.js exited 0; node /tmp/verify-preparation.js exited 0 with PASS pending-to-ready, visit reuse, stale completion, unmount cleanup. src/usePreparation.js and checkpoint both exist.' ↵ data['next_action']='Maintenance complete; repo|

控制决定：{'observe': 44, 'continue-with-observation': 3, 'continue-same-session': 1, 'allow-stop': 1}；同session=True；底层请求13。

## development/transfer-progress-composition-v4-vanilla/B/K1/1

[prompt](trials/reports-experiments/e-8938c63d82ca4548/jobs/j-001/prompt.md) · [events](trials/reports-experiments/e-8938c63d82ca4548/jobs/j-001/events.jsonl) · [patch](trials/reports-experiments/e-8938c63d82ca4548/jobs/j-001/patch.diff) · [control](trials/reports-experiments/e-8938c63d82ca4548/jobs/j-001/control/hook-events.jsonl) · [result/usage](trials/reports-experiments/e-8938c63d82ca4548/jobs/j-001/result.json)

原断言显式失败：[]；未发出/不可逐项比较：[]。保留原机械缺项按损失的字段，不将其等同实际失败。

[可信原始评分](trials/reports-experiments/e-8938c63d82ca4548/evaluations/v-e2c4bae606b84ea2/j-001/oracle/stdout.json)；UNDERREACH 8/10；原通过检查丢失 []，断言丢失 []。

|events行|工具|退出/状态|实际命令或文件|
|---:|---|---|---|
|7|command_execution|2|/usr/bin/bash -lc "cat src/transfer.js && cat package.json && rg -n 'watchTransferProgress\|progress\|telemetry' test* src README.md"|
|9|command_execution|0|/usr/bin/bash -lc "rg --files -g '"'!node_modules'"' -g '"'!stage/**'"'"|
|11|file_change|completed|[{'path': '/stage/checkpoint.json', 'kind': 'add'}]|
|14|file_change|completed|[{'path': '/workspace/src/progress.js', 'kind': 'update'}]|
|16|command_execution|1|/usr/bin/bash -lc "node --input-type=module <<'EOF' ↵ import assert from 'node:assert/strict'; ↵ import {createTransferWorkspace, createProgressFeed, collectProgressTelemetry} from './src/workspace.js'; ↵ const deferred = () => { let resolve; const promise = new Promise(r => resolve = r); return {promise, resolve}; }; ↵ const old = deferred(); ↵ const history = [], shown = [], queues = [], notices = [], cancelled = [|
|19|command_execution|0|/usr/bin/bash -lc "node --input-type=module <<'EOF' ↵ import assert from 'node:assert/strict'; ↵ import {createTransferWorkspace, createProgressFeed, collectProgressTelemetry} from './src/workspace.js'; ↵ const deferred = () => { let resolve; const promise = new Promise(r => resolve = r); return {promise, resolve}; }; ↵ const old = deferred(), history = [], shown = [], queues = [], notices = [], cancelled = []; ↵ let|
|21|command_execution|0|/usr/bin/bash -lc 'nl -ba src/progress.js'|
|23|command_execution|129|/usr/bin/bash -lc 'git diff -- src/progress.js && git status --short'|
|25|command_execution|0|/usr/bin/bash -lc 'cat /stage/checkpoint.json'|
|27|command_execution|0|/usr/bin/bash -lc "node --input-type=module <<'EOF' ↵ import assert from 'node:assert/strict'; ↵ import {createTransferWorkspace, createProgressFeed} from './src/workspace.js'; ↵ let resolve; const pending = new Promise(r => resolve = r); ↵ const shown = [], history = []; ↵ const feed = createProgressFeed({decode:p => p === 'late' ? pending : p}); ↵ const ws = createTransferWorkspace({transport:() => {}, onCancel:() |
|29|command_execution|0|/usr/bin/bash -lc "cat > /stage/checkpoint.json <<'EOF' ↵ {\"state\":\"repair_validate\",\"action_basis\":\"Panel listener attaches before synchronous feed start; receipt sequence gates display after recording.\",\"applicability\":\"applicable\",\"evidence\":[\"src/progress.js:3\",\"src/progress.js:8\",\"src/progress.js:18\",\"src/queue.js:12\",\"src/transfer.js:12\",\"src/telemetry.js:9\"],\"event_orders\":[\"cached|

控制决定：{'observe': 43, 'continue-with-observation': 3, 'allow-stop': 1}；同session=True；底层请求11。

## holdout/feature-flag-readiness-vue3/B/K0/1

[prompt](trials/reports-experiments/e-cf72133c77a142e4/jobs/j-001/prompt.md) · [events](trials/reports-experiments/e-cf72133c77a142e4/jobs/j-001/events.jsonl) · [patch](trials/reports-experiments/e-cf72133c77a142e4/jobs/j-001/patch.diff) · [control](trials/reports-experiments/e-cf72133c77a142e4/jobs/j-001/control/hook-events.jsonl) · [result/usage](trials/reports-experiments/e-cf72133c77a142e4/jobs/j-001/result.json)

原断言显式失败：[]；未发出/不可逐项比较：[]。保留原机械缺项按损失的字段，不将其等同实际失败。

[可信原始评分](trials/reports-experiments/e-cf72133c77a142e4/evaluations/v-0ffdad19badf4bfc/j-001/oracle/stdout.json)；PASS 4/4；原通过检查丢失 []，断言丢失 []。

|events行|工具|退出/状态|实际命令或文件|
|---:|---|---|---|
|7|command_execution|0|/usr/bin/bash -lc "pwd && rg --files -g '"'!node_modules'"' -g '"'!vendor'"' -g '"'!dist'"' \| head -80 && find . -name AGENTS.md -print"|
|9|command_execution|0|/usr/bin/bash -lc 'for f in package.json src/TargetView.vue src/AdjacentView.vue src/temporal-flow.js; do echo "$f"; nl -ba "$f"; done'|
|11|file_change|completed|[{'path': '/stage/checkpoint.json', 'kind': 'add'}]|
|14|file_change|completed|[{'path': '/workspace/src/temporal-flow.js', 'kind': 'update'}]|
|16|command_execution|129|/usr/bin/bash -lc "node - <<'NODE' ↵ const assert = require('node:assert/strict'); ↵ const { runTarget, runAdjacent } = require('./src/temporal-flow'); ↵ (async () => { ↵   for (const clickBeforeReady of [true, false]) { ↵     assert.deepEqual(await runTarget({ clickBeforeReady, loadedFlag: true }), { value: 'premium-action', events: ['premium-action'] }); ↵     assert.deepEqual(await runTarget({ clickBeforeReady, lo|
|18|command_execution|0|/usr/bin/bash -lc 'node --check src/temporal-flow.js && nl -ba src/temporal-flow.js'|
|20|file_change|completed|[{'path': '/stage/checkpoint.json', 'kind': 'update'}]|

控制决定：{'observe': 28, 'continue-with-observation': 3, 'allow-stop': 1}；同session=True；底层请求8。

## holdout/feature-flag-readiness-vue3/A/K0/1

[prompt](trials/reports-experiments/e-a1dbe5bfe82e4cb8/jobs/j-001/prompt.md) · [events](trials/reports-experiments/e-a1dbe5bfe82e4cb8/jobs/j-001/events.jsonl) · [patch](trials/reports-experiments/e-a1dbe5bfe82e4cb8/jobs/j-001/patch.diff) · [control](trials/reports-experiments/e-a1dbe5bfe82e4cb8/jobs/j-001/control/hook-events.jsonl) · [result/usage](trials/reports-experiments/e-a1dbe5bfe82e4cb8/jobs/j-001/result.json)

原断言显式失败：[]；未发出/不可逐项比较：[]。保留原机械缺项按损失的字段，不将其等同实际失败。

[可信原始评分](trials/reports-experiments/e-a1dbe5bfe82e4cb8/evaluations/v-073efe16e4d14a13/j-001/oracle/stdout.json)；PASS 4/4；原通过检查丢失 []，断言丢失 []。

|events行|工具|退出/状态|实际命令或文件|
|---:|---|---|---|
|7|command_execution|0|/usr/bin/bash -lc "pwd && rg --files -g '"'!node_modules'"' -g '"'!vendor'"' \| head -80 && find . -name AGENTS.md -print"|
|9|command_execution|0|/usr/bin/bash -lc 'cat package.json src/TargetView.vue src/AdjacentView.vue src/temporal-flow.js'|
|11|file_change|completed|[{'path': '/workspace/src/temporal-flow.js', 'kind': 'update'}]|
|13|file_change|completed|[{'path': '/workspace/src/temporal-flow.js', 'kind': 'update'}]|
|15|command_execution|129|/usr/bin/bash -lc "node - <<'NODE' ↵ const assert = require('node:assert/strict'); ↵ const {runTarget, runAdjacent} = require('./src/temporal-flow'); ↵ (async () => { ↵   for (const clickBeforeReady of [true, false]) { ↵     for (const loadedFlag of [true, false]) { ↵       const result = await runTarget({clickBeforeReady, loadedFlag}); ↵       const value = loadedFlag ? 'premium-action' : 'none'; ↵       assert.deep|

控制决定：{'observe': 24}；同session=True；底层请求6。

## holdout/document-submit-snapshot-vanilla/A/K0/1

[prompt](trials/reports-experiments/e-61aac3cdc265429c/jobs/j-001/prompt.md) · [events](trials/reports-experiments/e-61aac3cdc265429c/jobs/j-001/events.jsonl) · [patch](trials/reports-experiments/e-61aac3cdc265429c/jobs/j-001/patch.diff) · [control](trials/reports-experiments/e-61aac3cdc265429c/jobs/j-001/control/hook-events.jsonl) · [result/usage](trials/reports-experiments/e-61aac3cdc265429c/jobs/j-001/result.json)

原断言显式失败：[]；未发出/不可逐项比较：['submit-close-on-flush/submission-notice-visit-valid-at-emission']。保留原机械缺项按损失的字段，不将其等同实际失败。

[可信原始评分](trials/reports-experiments/e-61aac3cdc265429c/evaluations/v-a2a1ee1ad5f34560/j-001/oracle/stdout.json)；PASS 20/20；原通过检查丢失 []，断言丢失 ['submit-close-on-flush/submission-notice-visit-valid-at-emission']。

|events行|工具|退出/状态|实际命令或文件|
|---:|---|---|---|
|7|command_execution|2|/usr/bin/bash -lc "pwd && rg --files -g '"'!node_modules'"' -g '"'!coverage'"' \| sort && rg -n \"createDraftEditor\|createTrailingTask\|submit\\(\|onSaved\|close\\(\" test* src package.json README.md 2>/dev/null"|
|10|file_change|completed|[{'path': '/workspace/src/editor.js', 'kind': 'update'}, {'path': '/workspace/src/workspace.js', 'kind': 'update'}]|
|12|file_change|completed|[{'path': '/workspace/src/editor.js', 'kind': 'update'}]|
|14|command_execution|1|/usr/bin/bash -lc 'git diff -- src/editor.js src/workspace.js && git status --short'|
|16|command_execution|0|/usr/bin/bash -lc 'cat package.json && cat src/timers.js'|
|19|command_execution|0|/usr/bin/bash -lc "node --input-type=module <<'EOF' ↵ import assert from 'node:assert/strict'; ↵ import { createWorkspace } from './src/workspace.js'; ↵ import { createDraftStore } from './src/draft-store.js'; ↵ import { createReceiptArchive } from './src/receipt-archive.js'; ↵ let now = 0, next = 0; ↵ const jobs = new Map(); ↵ const timers = { schedule(fn, delay) { const id = ++next; jobs.set(id, {fn, at: now + dela|
|21|command_execution|0|/usr/bin/bash -lc 'git status --short; git rev-parse --is-inside-work-tree; nl -ba src/editor.js; nl -ba src/workspace.js'|

控制决定：{'observe': 30}；同session=True；底层请求7。

## holdout/document-submit-snapshot-vanilla/B/K0/1

[prompt](trials/reports-experiments/e-90fad752b35a4baa/jobs/j-001/prompt.md) · [events](trials/reports-experiments/e-90fad752b35a4baa/jobs/j-001/events.jsonl) · [patch](trials/reports-experiments/e-90fad752b35a4baa/jobs/j-001/patch.diff) · [control](trials/reports-experiments/e-90fad752b35a4baa/jobs/j-001/control/hook-events.jsonl) · [result/usage](trials/reports-experiments/e-90fad752b35a4baa/jobs/j-001/result.json)

原断言显式失败：[]；未发出/不可逐项比较：['submit-close-on-flush/submission-notice-visit-valid-at-emission']。保留原机械缺项按损失的字段，不将其等同实际失败。

[可信原始评分](trials/reports-experiments/e-90fad752b35a4baa/evaluations/v-14947df37e83489a/j-001/oracle/stdout.json)；PASS 20/20；原通过检查丢失 []，断言丢失 ['submit-close-on-flush/submission-notice-visit-valid-at-emission']。

|events行|工具|退出/状态|实际命令或文件|
|---:|---|---|---|
|7|command_execution|0|/usr/bin/bash -lc "rg --files -g '"'!node_modules'"' -g '"'!coverage'"'"|
|9|command_execution|0|/usr/bin/bash -lc 'nl -ba src/workspace.js'|
|11|command_execution|0|/usr/bin/bash -lc 'nl -ba src/editor.js'|
|13|command_execution|0|/usr/bin/bash -lc 'nl -ba src/search-preview.js'|
|15|command_execution|0|/usr/bin/bash -lc 'nl -ba README.md'|
|17|command_execution|0|/usr/bin/bash -lc 'nl -ba package.json'|
|19|command_execution|0|/usr/bin/bash -lc 'nl -ba src/trailing-task.js'|
|22|command_execution|0|/usr/bin/bash -lc 'nl -ba src/draft-store.js src/save-status.js src/timers.js src/receipt-archive.js'|
|24|command_execution|0|/usr/bin/bash -lc "cat > /stage/checkpoint.json <<'EOF' ↵ {\"state\":\"inspect\",\"action_basis\":\"Use trailing task for 120 ms editor writes; flush accepted edits at synchronous navigation and submit boundaries.\",\"evidence\":[\"README.md:3\",\"README.md:9\",\"README.md:15\",\"src/editor.js:5\",\"src/editor.js:17\",\"src/workspace.js:11\",\"src/trailing-task.js:5\",\"src/search-preview.js:4\"],\"observations\":\"E|
|26|file_change|completed|[{'path': '/workspace/src/editor.js', 'kind': 'update'}, {'path': '/workspace/src/workspace.js', 'kind': 'update'}]|
|28|command_execution|0|/usr/bin/bash -lc "node --input-type=module <<'EOF' ↵ import assert from 'node:assert/strict'; ↵ import { createWorkspace } from './src/workspace.js'; ↵ import { createDraftStore } from './src/draft-store.js'; ↵ import { createReceiptArchive } from './src/receipt-archive.js'; ↵ import { createSearchPreview } from './src/search-preview.js'; ↵ let now=0, next=0; const jobs=new Map(); ↵ const timers={schedule(fn,delay){|
|31|command_execution|0|/usr/bin/bash -lc "node --input-type=module <<'EOF' ↵ import assert from 'node:assert/strict'; ↵ import { createWorkspace } from './src/workspace.js'; ↵ import { createDraftStore } from './src/draft-store.js'; ↵ import { createReceiptArchive } from './src/receipt-archive.js'; ↵ function fixture(onSaved){let clock=0,n=0;const pending=new Map(), docs=[], statuses=[], notices=[];const timers={schedule(fn,d){const id=++n|
|33|file_change|completed|[{'path': '/workspace/src/editor.js', 'kind': 'update'}]|
|35|command_execution|1|/usr/bin/bash -lc 'git diff -- src/editor.js src/workspace.js'|
|37|command_execution|129|/usr/bin/bash -lc 'git diff --check'|
|39|command_execution|0|/usr/bin/bash -lc "node --input-type=module <<'EOF' ↵ import assert from 'node:assert/strict'; ↵ import {createWorkspace} from './src/workspace.js'; ↵ import {createDraftStore} from './src/draft-store.js'; ↵ import {createReceiptArchive} from './src/receipt-archive.js'; ↵ let t=0,n=0;const q=new Map();const timers={schedule(f,d){let i=++n;q.set(i,{f,at:t+d});return i},cancel(i){q.delete(i)}};const tick=d=>{t+=d;for(c|
|41|command_execution|0|/usr/bin/bash -lc "cat > /stage/checkpoint.json <<'EOF' ↵ {\"state\":\"repair_validate\",\"action_basis\":\"Editor edits use a 120 ms trailing task; navigation and submit flush pending accepted text synchronously.\",\"evidence\":[\"README.md:3\",\"README.md:9\",\"README.md:15\",\"src/editor.js:1\",\"src/editor.js:6\",\"src/editor.js:17\",\"src/workspace.js:11\",\"src/trailing-task.js:5\"],\"observations\":\"Controlle|

控制决定：{'observe': 53, 'continue-with-observation': 4, 'allow-stop': 1}；同session=True；底层请求11。

## holdout/document-submit-snapshot-vanilla/B/K0/2

[prompt](trials/reports-experiments/e-df852a7599cd4e5e/jobs/j-001/prompt.md) · [events](trials/reports-experiments/e-df852a7599cd4e5e/jobs/j-001/events.jsonl) · [patch](trials/reports-experiments/e-df852a7599cd4e5e/jobs/j-001/patch.diff) · [control](trials/reports-experiments/e-df852a7599cd4e5e/jobs/j-001/control/hook-events.jsonl) · [result/usage](trials/reports-experiments/e-df852a7599cd4e5e/jobs/j-001/result.json)

原断言显式失败：[]；未发出/不可逐项比较：['submit-close-on-flush/submission-notice-visit-valid-at-emission']。保留原机械缺项按损失的字段，不将其等同实际失败。

[可信原始评分](trials/reports-experiments/e-df852a7599cd4e5e/evaluations/v-60b27937d5424a2a/j-001/oracle/stdout.json)；PASS 20/20；原通过检查丢失 []，断言丢失 ['submit-close-on-flush/submission-notice-visit-valid-at-emission']。

|events行|工具|退出/状态|实际命令或文件|
|---:|---|---|---|
|7|command_execution|0|/usr/bin/bash -lc "rg --files -g '"'!node_modules'"' -g '"'!dist'"'"|
|9|command_execution|0|/usr/bin/bash -lc 'nl -ba src/editor.js; nl -ba src/workspace.js; nl -ba src/trailing-task.js; cat package.json; nl -ba README.md'|
|12|command_execution|0|/usr/bin/bash -lc "cat > /stage/checkpoint.json <<'EOF' ↵ {\"state\":\"inspect\",\"action_basis\":\"Coalesce editor writes at 120 ms; flush accepted edits at synchronous close/open and before submit capture.\",\"evidence\":[\"src/editor.js:5\",\"src/editor.js:17\",\"src/workspace.js:11\",\"src/trailing-task.js:8\",\"README.md:5\",\"README.md:15\"],\"observations\":\"Editor writes every edit; helper flush retires pend|
|14|file_change|completed|[{'path': '/workspace/src/editor.js', 'kind': 'update'}, {'path': '/workspace/src/workspace.js', 'kind': 'update'}]|
|16|command_execution|1|/usr/bin/bash -lc "node --input-type=module <<'EOF' ↵ import assert from 'node:assert/strict'; ↵ import {createWorkspace} from './src/workspace.js'; ↵ import {createDraftStore} from './src/draft-store.js'; ↵ import {createReceiptArchive} from './src/receipt-archive.js'; ↵ const jobs = new Map(); let serial=0; ↵ const timers={schedule(fn,delay){assert.equal(delay,120); const id=++serial;jobs.set(id,fn);return id},canc|
|19|command_execution|0|/usr/bin/bash -lc "node --input-type=module <<'EOF' ↵ import assert from 'node:assert/strict'; ↵ import {createWorkspace} from './src/workspace.js'; ↵ import {createDraftStore} from './src/draft-store.js'; ↵ import {createReceiptArchive} from './src/receipt-archive.js'; ↵ function setup(onSaved=()=>{}) { const jobs=new Map();let n=0;const timers={schedule(fn,delay){assert.equal(delay,120);const id=++n;jobs.set(id,fn)|
|21|command_execution|128|/usr/bin/bash -lc 'git diff --check; git diff -- src/editor.js src/workspace.js; git status --short'|
|23|command_execution|0|/usr/bin/bash -lc "cat > /stage/checkpoint.json <<'EOF' ↵ {\"state\":\"repair_validate\",\"action_basis\":\"Editor uses per-visit 120 ms trailing saves; lifecycle boundaries flush synchronously and submit captures entry snapshot after persistence.\",\"evidence\":[\"src/editor.js:1\",\"src/editor.js:6\",\"src/editor.js:22\",\"src/editor.js:36\",\"src/workspace.js:11\",\"src/trailing-task.js:8\",\"README.md:5\",\"READM|

控制决定：{'observe': 32, 'continue-with-observation': 3, 'allow-stop': 1}；同session=True；底层请求9。

## holdout/document-submit-snapshot-vanilla/A/K0/2

[prompt](trials/reports-experiments/e-30e2006b13d94a13/jobs/j-001/prompt.md) · [events](trials/reports-experiments/e-30e2006b13d94a13/jobs/j-001/events.jsonl) · [patch](trials/reports-experiments/e-30e2006b13d94a13/jobs/j-001/patch.diff) · [control](trials/reports-experiments/e-30e2006b13d94a13/jobs/j-001/control/hook-events.jsonl) · [result/usage](trials/reports-experiments/e-30e2006b13d94a13/jobs/j-001/result.json)

原断言显式失败：[]；未发出/不可逐项比较：['submit-close-on-flush/submission-notice-visit-valid-at-emission']。保留原机械缺项按损失的字段，不将其等同实际失败。

[可信原始评分](trials/reports-experiments/e-30e2006b13d94a13/evaluations/v-1406028593e9479c/j-001/oracle/stdout.json)；PASS 20/20；原通过检查丢失 []，断言丢失 ['submit-close-on-flush/submission-notice-visit-valid-at-emission']。

|events行|工具|退出/状态|实际命令或文件|
|---:|---|---|---|
|7|command_execution|0|/usr/bin/bash -lc "rg --files -g '"'!node_modules'"' -g '"'!*.lock'"'"|
|9|command_execution|0|/usr/bin/bash -lc 'cat package.json src/workspace.js src/editor.js src/trailing-task.js src/timers.js'|
|12|file_change|completed|[{'path': '/workspace/src/editor.js', 'kind': 'update'}, {'path': '/workspace/src/workspace.js', 'kind': 'update'}]|
|14|file_change|completed|[{'path': '/workspace/src/editor.js', 'kind': 'update'}]|
|16|command_execution|0|/usr/bin/bash -lc "node --input-type=module <<'EOF' ↵ import assert from 'node:assert/strict'; ↵ import { createWorkspace } from './src/workspace.js'; ↵ import { createDraftStore } from './src/draft-store.js'; ↵ import { createReceiptArchive } from './src/receipt-archive.js'; ↵ function setup(onSaved = () => {}) { ↵   const callbacks = new Map(); let next = 0; ↵   const timers = { schedule(fn, delay) { assert.equal(d|
|18|command_execution|129|/usr/bin/bash -lc 'git diff --check && git diff -- src/editor.js src/workspace.js'|

控制决定：{'observe': 28}；同session=True；底层请求7。

## holdout/feature-flag-readiness-vue3/A/K0/2

[prompt](trials/reports-experiments/e-8c2c69a06bb84761/jobs/j-001/prompt.md) · [events](trials/reports-experiments/e-8c2c69a06bb84761/jobs/j-001/events.jsonl) · [patch](trials/reports-experiments/e-8c2c69a06bb84761/jobs/j-001/patch.diff) · [control](trials/reports-experiments/e-8c2c69a06bb84761/jobs/j-001/control/hook-events.jsonl) · [result/usage](trials/reports-experiments/e-8c2c69a06bb84761/jobs/j-001/result.json)

原断言显式失败：[]；未发出/不可逐项比较：[]。保留原机械缺项按损失的字段，不将其等同实际失败。

[可信原始评分](trials/reports-experiments/e-8c2c69a06bb84761/evaluations/v-ff579b2974fe4443/j-001/oracle/stdout.json)；PASS 4/4；原通过检查丢失 []，断言丢失 []。

|events行|工具|退出/状态|实际命令或文件|
|---:|---|---|---|
|7|command_execution|0|/usr/bin/bash -lc "pwd && rg --files -g '"'!node_modules'"' -g '"'!vendor'"' \| head -80 && rg -n \"premium\|emergency\|runTarget\|runAdjacent\" ."|
|9|command_execution|1|/usr/bin/bash -lc "cat package.json src/TargetView.vue src/AdjacentView.vue src/temporal-flow.js && rg --files -g 'AGENTS.md' -g '*test*' -g '*spec*'"|
|12|file_change|completed|[{'path': '/workspace/src/temporal-flow.js', 'kind': 'update'}]|
|14|command_execution|129|/usr/bin/bash -lc "node - <<'NODE' ↵ const assert = require('node:assert/strict'); ↵ const {runTarget, runAdjacent} = require('./src/temporal-flow.js'); ↵ (async () => { ↵   for (const clickBeforeReady of [true, false]) { ↵     assert.deepEqual(await runTarget({clickBeforeReady, loadedFlag: true}), {value:'premium-action', events:['premium-action']}); ↵     assert.deepEqual(await runTarget({clickBeforeReady, loadedFl|

控制决定：{'observe': 20}；同session=True；底层请求5。

## holdout/feature-flag-readiness-vue3/B/K0/2

[prompt](trials/reports-experiments/e-df1b3b3c84944e3a/jobs/j-001/prompt.md) · [events](trials/reports-experiments/e-df1b3b3c84944e3a/jobs/j-001/events.jsonl) · [patch](trials/reports-experiments/e-df1b3b3c84944e3a/jobs/j-001/patch.diff) · [control](trials/reports-experiments/e-df1b3b3c84944e3a/jobs/j-001/control/hook-events.jsonl) · [result/usage](trials/reports-experiments/e-df1b3b3c84944e3a/jobs/j-001/result.json)

原断言显式失败：[]；未发出/不可逐项比较：[]。保留原机械缺项按损失的字段，不将其等同实际失败。

[可信原始评分](trials/reports-experiments/e-df1b3b3c84944e3a/evaluations/v-bf59b64bb12f40dc/j-001/oracle/stdout.json)；PASS 4/4；原通过检查丢失 []，断言丢失 []。

|events行|工具|退出/状态|实际命令或文件|
|---:|---|---|---|
|7|command_execution|0|/usr/bin/bash -lc "pwd && rg --files -g '"'!node_modules'"' -g '"'!vendor'"' \| head -80 && rg -n \"runTarget\|runAdjacent\|premium-action\|emergency-action\|clickBeforeReady\|loadedFlag\" ."|
|9|command_execution|0|/usr/bin/bash -lc 'cat package.json && nl -ba src/temporal-flow.js && nl -ba src/TargetView.vue && nl -ba src/AdjacentView.vue && ls -la'|
|12|file_change|completed|[{'path': '/stage/checkpoint.json', 'kind': 'add'}]|
|14|file_change|completed|[{'path': '/workspace/src/temporal-flow.js', 'kind': 'update'}]|
|16|command_execution|129|/usr/bin/bash -lc "node - <<'NODE' ↵ const assert = require('node:assert/strict'); ↵ const {runTarget, runAdjacent} = require('./src/temporal-flow.js'); ↵ (async () => { ↵   for (const clickBeforeReady of [true, false]) { ↵     for (const loadedFlag of [true, false]) { ↵       const value = loadedFlag ? 'premium-action' : 'none'; ↵       assert.deepEqual(await runTarget({clickBeforeReady, loadedFlag}), {value, events|
|18|file_change|completed|[{'path': '/stage/checkpoint.json', 'kind': 'update'}]|

控制决定：{'observe': 24, 'continue-with-observation': 3, 'allow-stop': 1}；同session=True；底层请求7。
