# 逐运行证据索引

只列实际工具调用与归档，不以 Agent 自述确认效果。完整 stdout 在对应 events.jsonl，可信结果在 raw-vectors.json 所指 oracle。

## 01 download-polling-restoration-low-cue-react18 / B1

[prompt](trials/reports-experiments/e-46b34adef8794a04/jobs/j-001/prompt.md) · [轨迹](trials/reports-experiments/e-46b34adef8794a04/jobs/j-001/events.jsonl) · [补丁](trials/reports-experiments/e-46b34adef8794a04/jobs/j-001/changes.json) · [回答](trials/reports-experiments/e-46b34adef8794a04/jobs/j-001/cli-output/answer.md)

分类 `execution-tool-unavailable`；工具 0；阶段记录 0 字符；修改路径：无。

输入token 54823；输出token 229；模型运行秒 26.540788。

|轨迹行|退出码|实际命令（前180字符；完整内容见轨迹）|
|---:|---:|---|

阶段格式检查：False；阶段1/2记录早于首个补丁：None。

## 02 download-polling-restoration-low-cue-react18 / A1

[prompt](trials/reports-experiments/e-10084c8571e848ef/jobs/j-001/prompt.md) · [轨迹](trials/reports-experiments/e-10084c8571e848ef/jobs/j-001/events.jsonl) · [补丁](trials/reports-experiments/e-10084c8571e848ef/jobs/j-001/changes.json) · [回答](trials/reports-experiments/e-10084c8571e848ef/jobs/j-001/cli-output/answer.md)

分类 `behavior-pass`；工具 6；阶段记录 0 字符；修改路径：src/usePreparation.js。

输入token 136093；输出token 1428；模型运行秒 56.865037。

|轨迹行|退出码|实际命令（前180字符；完整内容见轨迹）|
|---:|---:|---|
|5|0|/usr/bin/bash -lc "rg --files -g '"'!node_modules'"' -g '"'!*.lock'"' . && rg -n \"usePreparation\|DownloadDialog\|checkPreparation\|retryScheduled\|completed\" . -g '"'!node_modules'"|
|7|1|/usr/bin/bash -lc "cat src/usePreparation.js && cat src/BackgroundExportPanel.jsx && cat package.json && rg --files -g 'AGENTS.md' -g '*/AGENTS.md' /workspace /stage"|
|14|1|/usr/bin/bash -lc "node -e \"require('./src/usePreparation.js'); require('./src/DownloadDialog.jsx')\" && git diff --check && git diff -- src/usePreparation.js"|
|16|129|/usr/bin/bash -lc 'node --check src/usePreparation.js && git diff --check && git status --short'|

可信评分：[PASS](trials/reports-experiments/e-10084c8571e848ef/evaluations/v-6d8f45ed584a4fae/j-001/oracle/stdout.json)，必需 8/8，缺失 []。

## 03 feature-flag-readiness-vue3 / B1

[prompt](trials/reports-experiments/e-0f8a5ad595704f0a/jobs/j-001/prompt.md) · [轨迹](trials/reports-experiments/e-0f8a5ad595704f0a/jobs/j-001/events.jsonl) · [补丁](trials/reports-experiments/e-0f8a5ad595704f0a/jobs/j-001/changes.json) · [回答](trials/reports-experiments/e-0f8a5ad595704f0a/jobs/j-001/cli-output/answer.md)

分类 `behavior-pass`；工具 6；阶段记录 1399 字符；修改路径：src/temporal-flow.js。

输入token 131853；输出token 1210；模型运行秒 48.464724。

|轨迹行|退出码|实际命令（前180字符；完整内容见轨迹）|
|---:|---:|---|
|5|0|/usr/bin/bash -lc "pwd && rg --files -g '"'!node_modules'"' -g '"'!vendor'"' && rg -n \"runTarget\|runAdjacent\|premium-action\|emergency-action\|loadedFlag\" ."|
|7|0|/usr/bin/bash -lc 'cat package.json src/TargetView.vue src/AdjacentView.vue src/temporal-flow.js; find . -name AGENTS.md -print'|
|10|0|/usr/bin/bash -lc "mkdir -p /stage && printf '%s\\n' '{\"stage\":1,\"event\":\"complete\",\"evidence\":\"User: entitled first premium click after opening billing must work; emergen|
|14|129|/usr/bin/bash -lc "node - <<'NODE' ↵ const assert = require('node:assert/strict'); ↵ const {runTarget, runAdjacent} = require('./src/temporal-flow.js'); ↵ (async () => { ↵   for (const cli|
|16|0|/usr/bin/bash -lc "node --check src/temporal-flow.js && sed -n '1,8p' src/temporal-flow.js && printf '%s\\n' '{\"stage\":3,\"event\":\"complete\",\"result\":\"Changed only src/temp|

阶段格式检查：True；阶段1/2记录早于首个补丁：True。


可信评分：[PASS](trials/reports-experiments/e-0f8a5ad595704f0a/evaluations/v-cce197be0f2f4f9f/j-001/oracle/stdout.json)，必需 4/4，缺失 []。

## 04 feature-flag-readiness-vue3 / A1

[prompt](trials/reports-experiments/e-d99eb108b5e74bf7/jobs/j-001/prompt.md) · [轨迹](trials/reports-experiments/e-d99eb108b5e74bf7/jobs/j-001/events.jsonl) · [补丁](trials/reports-experiments/e-d99eb108b5e74bf7/jobs/j-001/changes.json) · [回答](trials/reports-experiments/e-d99eb108b5e74bf7/jobs/j-001/cli-output/answer.md)

分类 `behavior-pass`；工具 8；阶段记录 0 字符；修改路径：src/temporal-flow.js。

输入token 87471；输出token 691；模型运行秒 36.548721。

|轨迹行|退出码|实际命令（前180字符；完整内容见轨迹）|
|---:|---:|---|
|5|0|/usr/bin/bash -lc "pwd && rg --files -g '"'!node_modules'"' -g '"'! .git'"' \| head -80"|
|7|1|/usr/bin/bash -lc 'find .. -name AGENTS.md -print'|
|10|0|/usr/bin/bash -lc 'cat src/AdjacentView.vue'|
|11|0|/usr/bin/bash -lc 'cat src/TargetView.vue'|
|13|0|/usr/bin/bash -lc 'cat package.json'|
|15|0|/usr/bin/bash -lc 'cat src/temporal-flow.js'|
|20|0|/usr/bin/bash -lc "node - <<'NODE' ↵ const {runTarget,runAdjacent}=require('./src/temporal-flow.js'); ↵ (async()=>{ ↵   for(const clickBeforeReady of [true,false]) for(const loadedFlag o|

可信评分：[PASS](trials/reports-experiments/e-d99eb108b5e74bf7/evaluations/v-47245e5153994f8e/j-001/oracle/stdout.json)，必需 4/4，缺失 []。

## 05 transfer-progress-composition-v4-vanilla / B1

[prompt](trials/reports-experiments/e-6d84c7da010043e7/jobs/j-001/prompt.md) · [轨迹](trials/reports-experiments/e-6d84c7da010043e7/jobs/j-001/events.jsonl) · [补丁](trials/reports-experiments/e-6d84c7da010043e7/jobs/j-001/changes.json) · [回答](trials/reports-experiments/e-6d84c7da010043e7/jobs/j-001/cli-output/answer.md)

分类 `behavior-failure`；工具 13；阶段记录 1707 字符；修改路径：src/progress.js, src/queue.js。

输入token 256662；输出token 3484；模型运行秒 104.204786。

|轨迹行|退出码|实际命令（前180字符；完整内容见轨迹）|
|---:|---:|---|
|5|0|/usr/bin/bash -lc "rg --files -g '"'!*node_modules*'"' -g '"'!*.lock'"'"|
|7|2|/usr/bin/bash -lc 'rg -n "watchTransferProgress\|collectProgressTelemetry\|createTransfer\|progress\|cancel" src test* README.md 2>/dev/null'|
|9|0|/usr/bin/bash -lc 'cat package.json README.md'|
|11|0|/usr/bin/bash -lc 'cat src/transfer.js src/progress.js src/queue.js src/panel.js src/notice.js src/progress-source.js src/telemetry.js'|
|14|0|/usr/bin/bash -lc "cat > /stage/records.jsonl <<'EOF' ↵ {\"stage\":1,\"event\":\"complete\",\"evidence\":\"README.md:8-24 requires warm initial progress, decoded full frames, stable |
|18|1|/usr/bin/bash -lc "node --input-type=module <<'EOF' ↵ import assert from 'node:assert/strict'; ↵ import { createTransferWorkspace, createProgressFeed, collectProgressTelemetry } from '|
|21|0|/usr/bin/bash -lc "node --input-type=module <<'EOF' ↵ import assert from 'node:assert/strict'; ↵ import { createTransferWorkspace, createProgressFeed, collectProgressTelemetry } from '|
|25|0|/usr/bin/bash -lc "node --input-type=module <<'EOF' ↵ import assert from 'node:assert/strict'; ↵ import { createTransferWorkspace, createProgressFeed, collectProgressTelemetry } from '|
|28|128|/usr/bin/bash -lc 'git status --short'|
|29|1|/usr/bin/bash -lc 'git diff -- src/progress.js src/queue.js'|
|31|0|/usr/bin/bash -lc "cat >> /stage/records.jsonl <<'EOF' ↵ {\"stage\":3,\"event\":\"complete\",\"result\":\"Changed src/progress.js to subscribe before start, clean listener if start t|

阶段格式检查：True；阶段1/2记录早于首个补丁：True。


可信评分：[UNDERREACH](trials/reports-experiments/e-6d84c7da010043e7/evaluations/v-563579510fa349cd/j-001/oracle/stdout.json)，必需 9/10，缺失 ['start-switch-admission']。

## 06 transfer-progress-composition-v4-vanilla / A1

[prompt](trials/reports-experiments/e-80296d19b4f641db/jobs/j-001/prompt.md) · [轨迹](trials/reports-experiments/e-80296d19b4f641db/jobs/j-001/events.jsonl) · [补丁](trials/reports-experiments/e-80296d19b4f641db/jobs/j-001/changes.json) · [回答](trials/reports-experiments/e-80296d19b4f641db/jobs/j-001/cli-output/answer.md)

分类 `behavior-failure`；工具 9；阶段记录 0 字符；修改路径：src/progress.js。

输入token 138880；输出token 1987；模型运行秒 58.971577。

|轨迹行|退出码|实际命令（前180字符；完整内容见轨迹）|
|---:|---:|---|
|5|0|/usr/bin/bash -lc "rg --files -g 'AGENTS.md' -g 'src/**' -g 'test/**' -g 'tests/**' -g 'package.json' -g 'README.md'"|
|7|0|/usr/bin/bash -lc 'cat src/queue.js'|
|9|0|/usr/bin/bash -lc 'cat src/progress.js'|
|11|0|/usr/bin/bash -lc 'cat src/transfer.js'|
|13|0|/usr/bin/bash -lc 'cat package.json'|
|18|1|/usr/bin/bash -lc "node --input-type=module <<'EOF' ↵ import assert from 'node:assert/strict'; ↵ import { createTransferWorkspace, createProgressFeed, collectProgressTelemetry } from '|
|20|1|/usr/bin/bash -lc "node --input-type=module <<'EOF' ↵ import assert from 'node:assert/strict'; ↵ import { createTransferWorkspace, createProgressFeed, collectProgressTelemetry } from '|
|22|0|/usr/bin/bash -lc "node --input-type=module <<'EOF' ↵ import assert from 'node:assert/strict'; ↵ import { createTransferWorkspace, createProgressFeed, collectProgressTelemetry } from '|

可信评分：[UNDERREACH](trials/reports-experiments/e-80296d19b4f641db/evaluations/v-1471f9834abd418b/j-001/oracle/stdout.json)，必需 8/10，缺失 ['start-switch-admission', 'retry-preserved']。

## 07 local-config-readiness-low-cue-vue2 / A1

[prompt](trials/reports-experiments/e-738b9fa633134d5a/jobs/j-001/prompt.md) · [轨迹](trials/reports-experiments/e-738b9fa633134d5a/jobs/j-001/events.jsonl) · [补丁](trials/reports-experiments/e-738b9fa633134d5a/jobs/j-001/changes.json) · [回答](trials/reports-experiments/e-738b9fa633134d5a/jobs/j-001/cli-output/answer.md)

分类 `behavior-pass`；工具 4；阶段记录 0 字符；修改路径：src/editors/PersonnelEditor.vue。

输入token 94300；输出token 1121；模型运行秒 39.859641。

|轨迹行|退出码|实际命令（前180字符；完整内容见轨迹）|
|---:|---:|---|
|5|0|/usr/bin/bash -lc "pwd && rg --files -g 'AGENTS.md' -g 'package.json' -g 'src/**' -g '*test*' -g '*spec*'"|
|7|128|/usr/bin/bash -lc 'cat package.json src/editors/PersonnelEditor.vue src/components/SchemaForm.vue && git status --short'|
|12|0|/usr/bin/bash -lc "node -e 'const fs=require(\"fs\"); const s=fs.readFileSync(\"src/editors/PersonnelEditor.vue\",\"utf8\"); const c=JSON.parse(fs.readFileSync(\"src/config/personn|

可信评分：[PASS](trials/reports-experiments/e-738b9fa633134d5a/evaluations/v-3f39d8268c794bd1/j-001/oracle/stdout.json)，必需 7/7，缺失 []。

## 08 local-config-readiness-low-cue-vue2 / B1

[prompt](trials/reports-experiments/e-78aa1633c1e34cb3/jobs/j-001/prompt.md) · [轨迹](trials/reports-experiments/e-78aa1633c1e34cb3/jobs/j-001/events.jsonl) · [补丁](trials/reports-experiments/e-78aa1633c1e34cb3/jobs/j-001/changes.json) · [回答](trials/reports-experiments/e-78aa1633c1e34cb3/jobs/j-001/cli-output/answer.md)

分类 `behavior-pass`；工具 7；阶段记录 1224 字符；修改路径：src/editors/PersonnelEditor.vue。

输入token 164481；输出token 1907；模型运行秒 71.488586。

|轨迹行|退出码|实际命令（前180字符；完整内容见轨迹）|
|---:|---:|---|
|5|0|/usr/bin/bash -lc "pwd && rg --files -g 'AGENTS.md' -g 'src/**' -g '*test*' -g 'package.json'"|
|7|0|/usr/bin/bash -lc "cat src/components/SchemaForm.vue && cat package.json && rg -n 'getPageConfig\|applyConfig\|getStaticConfig\|PersonnelEditor\|StructureEditor' ."|
|10|0|/usr/bin/bash -lc "cat >> /stage/records.jsonl <<'EOF' ↵ {\"stage\":1,\"event\":\"complete\",\"evidence\":\"Requirement: replace Personnel remote config with src/config/personnel-for|
|14|129|/usr/bin/bash -lc "git diff --check && git diff -- src/editors/PersonnelEditor.vue && rg -n 'getStaticConfig\|personnelConfig\|setValue' src/editors/PersonnelEditor.vue src/editors/S|
|17|0|/usr/bin/bash -lc "node - <<'NODE' ↵ const fs = require('fs'); ↵ const p = fs.readFileSync('src/editors/PersonnelEditor.vue', 'utf8'); ↵ const s = fs.readFileSync('src/editors/StructureE|
|19|0|/usr/bin/bash -lc "cat >> /stage/records.jsonl <<'EOF' ↵ {\"stage\":3,\"event\":\"complete\",\"result\":\"PersonnelEditor.vue imports local personnel-form.json; getPageConfig waits f|

阶段格式检查：True；阶段1/2记录早于首个补丁：True。


可信评分：[PASS](trials/reports-experiments/e-78aa1633c1e34cb3/evaluations/v-a8d842ead25b4505/j-001/oracle/stdout.json)，必需 7/7，缺失 []。

## 09 transfer-progress-composition-v4-vanilla / A2

[prompt](trials/reports-experiments/e-9378bc8988034f2d/jobs/j-001/prompt.md) · [轨迹](trials/reports-experiments/e-9378bc8988034f2d/jobs/j-001/events.jsonl) · [补丁](trials/reports-experiments/e-9378bc8988034f2d/jobs/j-001/changes.json) · [回答](trials/reports-experiments/e-9378bc8988034f2d/jobs/j-001/cli-output/answer.md)

分类 `behavior-failure`；工具 5；阶段记录 0 字符；修改路径：src/progress.js。

输入token 117021；输出token 1518；模型运行秒 47.871047。

|轨迹行|退出码|实际命令（前180字符；完整内容见轨迹）|
|---:|---:|---|
|5|0|/usr/bin/bash -lc "rg --files -g 'AGENTS.md' -g 'package.json' -g 'src/**' -g 'test/**' -g 'tests/**' -g 'README.md'"|
|7|0|/usr/bin/bash -lc 'cat src/transfer.js src/progress.js src/queue.js package.json'|
|12|1|/usr/bin/bash -lc "node --input-type=module <<'EOF' ↵ import assert from 'node:assert/strict'; ↵ import { createProgressFeed, createTransferWorkspace, collectProgressTelemetry } from '|
|14|0|/usr/bin/bash -lc "node --input-type=module <<'EOF' ↵ import assert from 'node:assert/strict'; ↵ import { createProgressFeed, createTransferWorkspace, collectProgressTelemetry } from '|

可信评分：[UNDERREACH](trials/reports-experiments/e-9378bc8988034f2d/evaluations/v-bc1c60a5ebfd41fc/j-001/oracle/stdout.json)，必需 8/10，缺失 ['start-switch-admission', 'retry-preserved']。

## 10 transfer-progress-composition-v4-vanilla / B2

[prompt](trials/reports-experiments/e-e4dcafb3c28f47d7/jobs/j-001/prompt.md) · [轨迹](trials/reports-experiments/e-e4dcafb3c28f47d7/jobs/j-001/events.jsonl) · [补丁](trials/reports-experiments/e-e4dcafb3c28f47d7/jobs/j-001/changes.json) · [回答](trials/reports-experiments/e-e4dcafb3c28f47d7/jobs/j-001/cli-output/answer.md)

分类 `behavior-failure`；工具 12；阶段记录 1744 字符；修改路径：src/progress.js。

输入token 235457；输出token 3362；模型运行秒 100.416999。

|轨迹行|退出码|实际命令（前180字符；完整内容见轨迹）|
|---:|---:|---|
|5|0|/usr/bin/bash -lc "rg --files -g 'AGENTS.md' -g 'src/**' -g 'test/**' -g 'tests/**' -g 'package.json' -g 'README.md'"|
|7|0|/usr/bin/bash -lc "rg -n 'watchTransferProgress\|createTransfer\|recordProgress\|showProgress\|decode\|start\\(' src README.md"|
|9|0|/usr/bin/bash -lc "cat package.json README.md; rg --files -g '"'!node_modules/**'"'"|
|11|0|/usr/bin/bash -lc 'cat src/transfer.js src/notice.js src/progress.js src/queue.js src/panel.js src/retry.js src/progress-source.js src/telemetry.js'|
|14|0|/usr/bin/bash -lc "cat > /stage/records.jsonl <<'EOF' ↵ {\"stage\":1,\"event\":\"complete\",\"evidence\":\"README.md:10-25 requires cached start, async decode, preserved queue/retry/|
|18|1|/usr/bin/bash -lc "node --input-type=module <<'EOF' ↵ import assert from 'node:assert/strict'; ↵ import { createTransferWorkspace, createProgressFeed, collectProgressTelemetry } from '|
|21|1|/usr/bin/bash -lc "node --input-type=module <<'EOF' ↵ import assert from 'node:assert/strict'; ↵ import { createTransferWorkspace, createProgressFeed, collectProgressTelemetry } from '|
|23|0|/usr/bin/bash -lc "node --input-type=module <<'EOF' ↵ import assert from 'node:assert/strict'; ↵ import { createTransferWorkspace, createProgressFeed, collectProgressTelemetry } from '|
|25|128|/usr/bin/bash -lc 'git diff -- src/progress.js; git status --short'|
|27|0|/usr/bin/bash -lc 'node --check src/progress.js'|
|29|0|/usr/bin/bash -lc "cat >> /stage/records.jsonl <<'EOF' ↵ {\"stage\":3,\"event\":\"complete\",\"result\":\"Changed src/progress.js: listener is installed before start; start exception|

阶段格式检查：True；阶段1/2记录早于首个补丁：True。


可信评分：[UNDERREACH](trials/reports-experiments/e-e4dcafb3c28f47d7/evaluations/v-9d42273fe9bc4e56/j-001/oracle/stdout.json)，必需 8/10，缺失 ['start-switch-admission', 'retry-preserved']。

## 11 download-polling-restoration-low-cue-react18 / A2

[prompt](trials/reports-experiments/e-6d4ad750c39d4ae6/jobs/j-001/prompt.md) · [轨迹](trials/reports-experiments/e-6d4ad750c39d4ae6/jobs/j-001/events.jsonl) · [补丁](trials/reports-experiments/e-6d4ad750c39d4ae6/jobs/j-001/changes.json) · [回答](trials/reports-experiments/e-6d4ad750c39d4ae6/jobs/j-001/cli-output/answer.md)

分类 `behavior-pass`；工具 6；阶段记录 0 字符；修改路径：src/usePreparation.js。

输入token 95745；输出token 1168；模型运行秒 39.754152。

|轨迹行|退出码|实际命令（前180字符；完整内容见轨迹）|
|---:|---:|---|
|5|0|/usr/bin/bash -lc "rg --files -g '"'!node_modules'"' -g '"'!package-lock.json'"'"|
|7|0|/usr/bin/bash -lc "rg -n \"usePreparation\|DownloadDialog\|schedulePreparationRetry\|checkPreparation\" . -g '"'!node_modules'"'"|
|9|0|/usr/bin/bash -lc 'cat src/usePreparation.js && cat package.json && ls -la'|
|14|129|/usr/bin/bash -lc 'git diff -- src/usePreparation.js'|
|16|0|/usr/bin/bash -lc 'node --check src/usePreparation.js'|

可信评分：[PASS](trials/reports-experiments/e-6d4ad750c39d4ae6/evaluations/v-e620a86101724033/j-001/oracle/stdout.json)，必需 8/8，缺失 []。

## 12 download-polling-restoration-low-cue-react18 / B2

[prompt](trials/reports-experiments/e-a5daf9ad644d47cc/jobs/j-001/prompt.md) · [轨迹](trials/reports-experiments/e-a5daf9ad644d47cc/jobs/j-001/events.jsonl) · [补丁](trials/reports-experiments/e-a5daf9ad644d47cc/jobs/j-001/changes.json) · [回答](trials/reports-experiments/e-a5daf9ad644d47cc/jobs/j-001/cli-output/answer.md)

分类 `behavior-failure`；工具 9；阶段记录 1974 字符；修改路径：src/usePreparation.js。

输入token 207326；输出token 2869；模型运行秒 75.280487。

|轨迹行|退出码|实际命令（前180字符；完整内容见轨迹）|
|---:|---:|---|
|5|0|/usr/bin/bash -lc "pwd && rg --files -g '"'!node_modules'"' -g '"'!*.lock'"' \| sort && rg -n \"usePreparation\|DownloadDialog\|checkPreparation\|schedulePreparationRetry\|completed\|pen|
|7|128|/usr/bin/bash -lc 'cat src/BackgroundExportPanel.jsx src/usePreparation.js src/preparation-api.js src/DownloadDialog.jsx && git status --short && cat package.json'|
|10|0|/usr/bin/bash -lc "mkdir -p /stage && printf '%s\\n' '{\"stage\":1,\"event\":\"complete\",\"evidence\":\"src/usePreparation.js:20-28 checks once and treats any truthy status as com|
|12|0|/usr/bin/bash -lc "printf '%s\\n' '{\"stage\":2,\"event\":\"complete\",\"plan\":\"Change src/usePreparation.js only. Accept ready for true, ready string, or {status: ready}; false/|
|16|1|/usr/bin/bash -lc 'ls -d node_modules/react node_modules/react-dom 2>/dev/null; node --check src/usePreparation.js; node --check src/DownloadDialog.jsx'|
|19|0|/usr/bin/bash -lc "node --check src/usePreparation.js && node -e 'const fs=require(\"fs\"); new Function(fs.readFileSync(\"src/DownloadDialog.jsx\", \"utf8\")); console.log(\"synta|
|21|0|/usr/bin/bash -lc "cat > /tmp/check-preparation.js <<'EOF' ↵ const assert = require('assert'); ↵ const Module = require('module'); ↵ const originalLoad = Module._load; ↵ let refs = [], cur|
|23|0|/usr/bin/bash -lc "printf '%s\\n' '{\"stage\":3,\"event\":\"complete\",\"result\":\"src/usePreparation.js now recognizes explicit ready results, schedules pending retries, deduplic|

阶段格式检查：True；阶段1/2记录早于首个补丁：True。


可信评分：[UNDERREACH](trials/reports-experiments/e-a5daf9ad644d47cc/evaluations/v-0e1e41fd58a34aac/j-001/oracle/stdout.json)，必需 7/8，缺失 ['download-waits-after-pending']。

## 13 feature-flag-readiness-vue3 / A2

[prompt](trials/reports-experiments/e-2b1dec9309af43ad/jobs/j-001/prompt.md) · [轨迹](trials/reports-experiments/e-2b1dec9309af43ad/jobs/j-001/events.jsonl) · [补丁](trials/reports-experiments/e-2b1dec9309af43ad/jobs/j-001/changes.json) · [回答](trials/reports-experiments/e-2b1dec9309af43ad/jobs/j-001/cli-output/answer.md)

分类 `behavior-pass`；工具 4；阶段记录 0 字符；修改路径：src/temporal-flow.js。

输入token 86018；输出token 638；模型运行秒 32.345936。

|轨迹行|退出码|实际命令（前180字符；完整内容见轨迹）|
|---:|---:|---|
|5|0|/usr/bin/bash -lc "pwd && rg --files -g '"'!node_modules'"' -g '"'!vendor'"' && find . -name AGENTS.md -print"|
|7|0|/usr/bin/bash -lc 'cat package.json src/TargetView.vue src/AdjacentView.vue src/temporal-flow.js'|
|12|0|/usr/bin/bash -lc "node - <<'NODE' ↵ const assert = require('node:assert/strict'); ↵ const { runTarget, runAdjacent } = require('./src/temporal-flow'); ↵ (async () => { ↵   for (const clic|

可信评分：[PASS](trials/reports-experiments/e-2b1dec9309af43ad/evaluations/v-8912e1f67c4346c1/j-001/oracle/stdout.json)，必需 4/4，缺失 []。

## 14 feature-flag-readiness-vue3 / B2

[prompt](trials/reports-experiments/e-5516b7310c7b4f73/jobs/j-001/prompt.md) · [轨迹](trials/reports-experiments/e-5516b7310c7b4f73/jobs/j-001/events.jsonl) · [补丁](trials/reports-experiments/e-5516b7310c7b4f73/jobs/j-001/changes.json) · [回答](trials/reports-experiments/e-5516b7310c7b4f73/jobs/j-001/cli-output/answer.md)

分类 `behavior-pass`；工具 6；阶段记录 1202 字符；修改路径：src/temporal-flow.js。

输入token 131803；输出token 1181；模型运行秒 45.756377。

|轨迹行|退出码|实际命令（前180字符；完整内容见轨迹）|
|---:|---:|---|
|5|0|/usr/bin/bash -lc "pwd && rg --files -g '"'!node_modules'"' -g '"'!vendor'"' \| head -80 && rg -n \"runTarget\|runAdjacent\|premium-action\|emergency-action\|loadedFlag\" ."|
|7|1|/usr/bin/bash -lc "cat package.json src/TargetView.vue src/AdjacentView.vue src/temporal-flow.js && rg --files -g 'AGENTS.md' -g '*test*' -g '*spec*' /workspace /stage"|
|10|0|/usr/bin/bash -lc "mkdir -p /stage && cat >> /stage/records.jsonl <<'EOF' ↵ {\"stage\":1,\"event\":\"complete\",\"evidence\":\"src/temporal-flow.js:3 initializes enabled=false, check|
|14|129|/usr/bin/bash -lc "node - <<'NODE' ↵ const assert = require('node:assert/strict'); ↵ const {runTarget, runAdjacent} = require('./src/temporal-flow.js'); ↵ (async () => { ↵   for (const cli|
|16|0|/usr/bin/bash -lc "cat >> /stage/records.jsonl <<'EOF' ↵ {\"stage\":3,\"event\":\"complete\",\"result\":\"Changed only src/temporal-flow.js:3: wait for readiness before evaluating lo|

阶段格式检查：True；阶段1/2记录早于首个补丁：True。


可信评分：[PASS](trials/reports-experiments/e-5516b7310c7b4f73/evaluations/v-b846dcff52da499e/j-001/oracle/stdout.json)，必需 4/4，缺失 []。

## 15 local-config-readiness-low-cue-vue2 / B2

[prompt](trials/reports-experiments/e-d70803a2c29e4ae2/jobs/j-001/prompt.md) · [轨迹](trials/reports-experiments/e-d70803a2c29e4ae2/jobs/j-001/events.jsonl) · [补丁](trials/reports-experiments/e-d70803a2c29e4ae2/jobs/j-001/changes.json) · [回答](trials/reports-experiments/e-d70803a2c29e4ae2/jobs/j-001/cli-output/answer.md)

分类 `behavior-pass`；工具 6；阶段记录 1351 字符；修改路径：src/editors/PersonnelEditor.vue。

输入token 141934；输出token 1816；模型运行秒 57.873229。

|轨迹行|退出码|实际命令（前180字符；完整内容见轨迹）|
|---:|---:|---|
|5|2|/usr/bin/bash -lc "pwd; rg --files -g '"'!node_modules'"' -g '"'!dist'"' \| sort; rg -n \"getStaticConfig\|PersonnelEditor\|SchemaForm\|applyConfig\|setValue\" src test tests 2>/dev/nul|
|7|128|/usr/bin/bash -lc 'cat src/components/SchemaForm.vue; cat package.json; cat src/editors/PersonnelEditor.vue; git status --short'|
|10|0|/usr/bin/bash -lc "mkdir -p /stage; cat >> /stage/records.jsonl <<'EOF' ↵ {\"stage\":1,\"event\":\"complete\",\"evidence\":\"Task: replace Personnel remote request with src/config/pe|
|14|0|/usr/bin/bash -lc "node <<'NODE' ↵ const fs = require('fs'); ↵ const vm = require('vm'); ↵ const assert = require('assert'); ↵ const source = fs.readFileSync('src/editors/PersonnelEditor.v|
|16|0|/usr/bin/bash -lc "cat >> /stage/records.jsonl <<'EOF' ↵ {\"stage\":3,\"event\":\"complete\",\"result\":\"PersonnelEditor.vue imports local JSON, queues it until formApi.setValue is |

阶段格式检查：True；阶段1/2记录早于首个补丁：True。


可信评分：[PASS](trials/reports-experiments/e-d70803a2c29e4ae2/evaluations/v-02be17afb4b74c00/j-001/oracle/stdout.json)，必需 7/7，缺失 []。

## 16 local-config-readiness-low-cue-vue2 / A2

[prompt](trials/reports-experiments/e-7c445bb89d7a4cfd/jobs/j-001/prompt.md) · [轨迹](trials/reports-experiments/e-7c445bb89d7a4cfd/jobs/j-001/events.jsonl) · [补丁](trials/reports-experiments/e-7c445bb89d7a4cfd/jobs/j-001/changes.json) · [回答](trials/reports-experiments/e-7c445bb89d7a4cfd/jobs/j-001/cli-output/answer.md)

分类 `behavior-pass`；工具 5；阶段记录 0 字符；修改路径：src/editors/PersonnelEditor.vue。

输入token 117265；输出token 1078；模型运行秒 41.849075。

|轨迹行|退出码|实际命令（前180字符；完整内容见轨迹）|
|---:|---:|---|
|5|0|/usr/bin/bash -lc "pwd && rg --files -g 'AGENTS.md' -g 'src/**' -g 'package.json' -g '*test*'"|
|7|0|/usr/bin/bash -lc 'cat src/editors/PersonnelEditor.vue src/components/SchemaForm.vue package.json'|
|12|129|/usr/bin/bash -lc 'git diff -- src/editors/PersonnelEditor.vue && git status --short'|
|14|0|/usr/bin/bash -lc "sed -n '7,65p' src/editors/PersonnelEditor.vue"|

可信评分：[PASS](trials/reports-experiments/e-7c445bb89d7a4cfd/evaluations/v-6e211487e7114cb7/j-001/oracle/stdout.json)，必需 7/7，缺失 []。

