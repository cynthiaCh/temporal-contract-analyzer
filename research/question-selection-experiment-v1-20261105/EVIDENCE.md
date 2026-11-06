# 轨迹与补丁证据索引

选题审查先于正式调用；这里是行为完成后的证据核对。链接全部相对本实验目录，评分路径指向实际被冻结评分的候选，不能以workspace后续内容替代。

## handoff-redirect-reentrancy-vanilla R / repeat 1

交付 TCQ-003：[prompt](trials/lane1/reports-experiments/e-824f8dba6876454a/jobs/j-001/prompt.md)；[轨迹](trials/lane1/reports-experiments/e-824f8dba6876454a/jobs/j-001/events.jsonl)；[补丁](trials/lane1/reports-experiments/e-824f8dba6876454a/jobs/j-001/changes.json)；[原始评分](trials/lane1/reports-experiments/e-824f8dba6876454a/evaluations/v-564abebc13bc4c86/j-001/oracle/stdout.json)。

- 读代码，events.jsonl 第 5 行，退出码 0：`/bin/bash -lc "pwd && rg --files -g '"'!node_modules'"' -g '"'! .git'"' && rg -n \"createWorkspace|onHandoff|retire\\(\" ."`
- 可执行核查，events.jsonl 第 10 行，退出码 0：`/bin/bash -lc "node --input-type=module <<'EOF'`

这些命令证明接触了相关源码并运行了相应检查；不能从成功/自述推断题目是因果原因，也不能认为覆盖全部事件顺序。

## listener-registration-order-vanilla R / repeat 1

交付 TCQ-001, TCQ-003：[prompt](trials/lane0/reports-experiments/e-6bcfa862f92b43aa/jobs/j-001/prompt.md)；[轨迹](trials/lane0/reports-experiments/e-6bcfa862f92b43aa/jobs/j-001/events.jsonl)；[补丁](trials/lane0/reports-experiments/e-6bcfa862f92b43aa/jobs/j-001/changes.json)；[原始评分](trials/lane0/reports-experiments/e-6bcfa862f92b43aa/evaluations/v-ab32f43af9964344/j-001/oracle/stdout.json)。

- 读代码，events.jsonl 第 5 行，退出码 0：`/bin/bash -lc "pwd && rg --files -g '"'!node_modules'"' && rg -n \"subscribeChannel|createPresencePanel|renderPresence|navigation|test\" ."`
- 读代码，events.jsonl 第 7 行，退出码 0：`/bin/bash -lc 'cat package.json src/*.js'`
- 可执行核查，events.jsonl 第 12 行，退出码 0：`/bin/bash -lc "node --input-type=module <<'EOF'`
- 可执行核查，events.jsonl 第 14 行，退出码 0：`/bin/bash -lc "node --input-type=module <<'EOF'`

这些命令证明接触了相关源码并运行了相应检查；不能从成功/自述推断题目是因果原因，也不能认为覆盖全部事件顺序。

## document-submit-snapshot-vanilla R / repeat 1

交付 TCQ-003, TCQ-004：[prompt](trials/lane1/reports-experiments/e-0ee7fc5f3bae4217/jobs/j-001/prompt.md)；[轨迹](trials/lane1/reports-experiments/e-0ee7fc5f3bae4217/jobs/j-001/events.jsonl)；[补丁](trials/lane1/reports-experiments/e-0ee7fc5f3bae4217/jobs/j-001/changes.json)；[原始评分](trials/lane1/reports-experiments/e-0ee7fc5f3bae4217/evaluations/v-3fd78360ea404359/j-001/oracle/stdout.json)。

- 读代码，events.jsonl 第 5 行，退出码 0：`/bin/bash -lc "rg --files -g '"'!node_modules'"' -g '"'!coverage'"'"`
- 读代码，events.jsonl 第 7 行，退出码 0：`/bin/bash -lc 'cat src/editor.js src/workspace.js src/trailing-task.js'`
- 读代码，events.jsonl 第 9 行，退出码 0：`/bin/bash -lc 'cat README.md'`
- 读代码，events.jsonl 第 11 行，退出码 0：`/bin/bash -lc 'cat package.json'`
- 可执行核查，events.jsonl 第 16 行，退出码 0：`/bin/bash -lc "node --input-type=module <<'EOF'`

这些命令证明接触了相关源码并运行了相应检查；不能从成功/自述推断题目是因果原因，也不能认为覆盖全部事件顺序。

## handoff-redirect-reentrancy-vanilla R / repeat 2

交付 TCQ-003：[prompt](trials/lane0/reports-experiments/e-b118db4c99354b5b/jobs/j-001/prompt.md)；[轨迹](trials/lane0/reports-experiments/e-b118db4c99354b5b/jobs/j-001/events.jsonl)；[补丁](trials/lane0/reports-experiments/e-b118db4c99354b5b/jobs/j-001/changes.json)；[原始评分](trials/lane0/reports-experiments/e-b118db4c99354b5b/evaluations/v-dc6c2307a37945af/j-001/oracle/stdout.json)。

- 读代码，events.jsonl 第 5 行，退出码 0：`/bin/bash -lc "rg --files -g '"'!node_modules'"' && rg -n \"open\\(|handoff|close\\(|dispose\\(\" ."`
- 可执行核查，events.jsonl 第 10 行，退出码 0：`/bin/bash -lc "node --input-type=module <<'EOF'`

这些命令证明接触了相关源码并运行了相应检查；不能从成功/自述推断题目是因果原因，也不能认为覆盖全部事件顺序。

## listener-registration-order-vanilla R / repeat 2

交付 TCQ-001, TCQ-003：[prompt](trials/lane0/reports-experiments/e-67c3b7a27e9d4a13/jobs/j-001/prompt.md)；[轨迹](trials/lane0/reports-experiments/e-67c3b7a27e9d4a13/jobs/j-001/events.jsonl)；[补丁](trials/lane0/reports-experiments/e-67c3b7a27e9d4a13/jobs/j-001/changes.json)；[原始评分](trials/lane0/reports-experiments/e-67c3b7a27e9d4a13/evaluations/v-6ab45c52007c4d85/j-001/oracle/stdout.json)。

- 读代码，events.jsonl 第 5 行，退出码 0：`/bin/bash -lc "pwd; rg --files -g '"'!node_modules'"' -g '"'!vendor'"'; rg -n \"subscribeChannel|createPresencePanel|createWorkspaceNavigation|renderPresence\" ."`
- 读代码，events.jsonl 第 7 行，退出码 0：`/bin/bash -lc 'cat package.json; cat src/presence-panel.js; cat src/subscription.js; cat src/workspace-navigation.js; git status --short'`
- 可执行核查，events.jsonl 第 12 行，退出码 0：`/bin/bash -lc "node --input-type=module <<'EOF'`

这些命令证明接触了相关源码并运行了相应检查；不能从成功/自述推断题目是因果原因，也不能认为覆盖全部事件顺序。

## document-submit-snapshot-vanilla R / repeat 2

交付 TCQ-003, TCQ-004：[prompt](trials/lane2/reports-experiments/e-a603713e4f204b37/jobs/j-001/prompt.md)；[轨迹](trials/lane2/reports-experiments/e-a603713e4f204b37/jobs/j-001/events.jsonl)；[补丁](trials/lane2/reports-experiments/e-a603713e4f204b37/jobs/j-001/changes.json)；[原始评分](trials/lane2/reports-experiments/e-a603713e4f204b37/evaluations/v-276a10ada34d4469/j-001/oracle/stdout.json)。

- 读代码，events.jsonl 第 5 行，退出码 0：`/bin/bash -lc "pwd && rg --files -g 'AGENTS.md' -g 'package.json' -g 'src/**' -g 'test/**' -g 'tests/**' -g 'README.md'"`
- 读代码，events.jsonl 第 7 行，退出码 0：`/bin/bash -lc 'rg --files && cat package.json && cat src/editor.js && cat src/workspace.js && cat src/trailing-task.js'`
- 可执行核查，events.jsonl 第 14 行，退出码 0：`/bin/bash -lc "node --input-type=module <<'EOF'`

这些命令证明接触了相关源码并运行了相应检查；不能从成功/自述推断题目是因果原因，也不能认为覆盖全部事件顺序。

## 不适用案例的改动范围

- S / repeat 1：仅改target flow文件=True，adjacent源码逐字保留=True；[补丁](trials/lane0/reports-experiments/e-9c865f9d8ddd4ded/jobs/j-001/changes.json)，[评分](trials/lane0/reports-experiments/e-9c865f9d8ddd4ded/evaluations/v-926e146200e742c7/j-001/oracle/stdout.json)。
- R / repeat 1：仅改target flow文件=True，adjacent源码逐字保留=True；[补丁](trials/lane1/reports-experiments/e-62757bdff6b94ad3/jobs/j-001/changes.json)，[评分](trials/lane1/reports-experiments/e-62757bdff6b94ad3/evaluations/v-6af161fdb6a74c1e/j-001/oracle/stdout.json)。
- F / repeat 1：仅改target flow文件=True，adjacent源码逐字保留=True；[补丁](trials/lane2/reports-experiments/e-33895ad58f154b19/jobs/j-001/changes.json)，[评分](trials/lane2/reports-experiments/e-33895ad58f154b19/evaluations/v-c5e9ad8e7eac4616/j-001/oracle/stdout.json)。
- R / repeat 2：仅改target flow文件=True，adjacent源码逐字保留=True；[补丁](trials/lane1/reports-experiments/e-f23bfe69c3584c62/jobs/j-001/changes.json)，[评分](trials/lane1/reports-experiments/e-f23bfe69c3584c62/evaluations/v-49454599cf254a5e/j-001/oracle/stdout.json)。
- S / repeat 2：仅改target flow文件=True，adjacent源码逐字保留=True；[补丁](trials/lane2/reports-experiments/e-8f1ffb53b5d548c0/jobs/j-001/changes.json)，[评分](trials/lane2/reports-experiments/e-8f1ffb53b5d548c0/evaluations/v-d963646c59a04656/j-001/oracle/stdout.json)。
- F / repeat 2：仅改target flow文件=True，adjacent源码逐字保留=True；[补丁](trials/lane0/reports-experiments/e-79884cb35f8e4f1d/jobs/j-001/changes.json)，[评分](trials/lane0/reports-experiments/e-79884cb35f8e4f1d/evaluations/v-a41488fe664b4c6f/j-001/oracle/stdout.json)。
