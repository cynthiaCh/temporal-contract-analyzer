# 新仓库修改到可重放反例：三种方法的实际对照

**结果：工具无需新增规则便能迁移到新仓库，但本次没有观察到相对于既有 fast-check 通用模型的适配优势。普通断言也能用 20 行脚本复现。**

## 案例与边界

本地既有 external-tests 中未找到 Olical/EventEmitter 或旧名 Wolfy87 的记录。选用其真实历史修复：

- 问题版：`b587eb94d1f95cba98814d4319e734dda27c085a`。
- 修复版：[53a2875](https://github.com/Olical/EventEmitter/commit/53a28759584ab31c8a3629cc6f679da5ea2bf023)，关联 [issue 54](https://github.com/Olical/EventEmitter/issues/54)。
- 原始实现为一个约 15 KB 的文件，问题版 449 行、修复版 455 行，包含大量 API 注释。保留原始字节及 README 中的 MIT 许可证；修复版文件另与 GitHub Git blob SHA 校验一致。
- API：构造实例，`on/off/emit/once`；行为要求：显式注册的一次性监听器在一次嵌套触发中只执行一次。返回特殊值后自动移除的普通监听器不在本次要求内。

这是**未用于开发引擎的新仓库迁移**，不是盲测：实施者在运行前已经看过上游修复说明及 diff，也知道涉及重入。不能写成“工具在未知修改中自动发现了未知缺陷”。固定条件见 [PROTOCOL.md](PROTOCOL.md)。两个候选仓库中 component/emitter 的连接器搜索返回 422，没有运行它；本次不作成功案例筛选后的多项目统计。

## 从输入到证据的实际步骤

1. 两侧共同准备：确定父提交和修复提交，保存源码，确认模块导出、API、行为要求和运行环境。这部分工作两侧均需要，未计为工具独有优势。
2. P 工具：填写 [plan.json](plan.json)，调用既有引擎。它自动执行预置场景、配对两侧并保存回调轨迹；没有新增场景或规则。
3. F fast-check：向之前已独立实现的通用属性模型提供**完全同一份 plan**，按固定三个种子运行，再配对重放。没有为该仓库新增测试函数，也没有调用 P 的生成器、执行器或判断器。
4. N 普通断言：运行预先写好的 [plain-assert.cjs](plain-assert.cjs)。脚本创建一次性监听器，第一次调用时再 emit 一次，输出计数与调用帧，然后断言计数为 1。同一脚本在两侧各执行两次。

| 可观察工作与产物 | P：工具 | F：既有 fast-check 通用模型 | N：普通 Node assert |
| --- | --- | --- | --- |
| 本次输入 | 23 行 JSON，13 个叶字段 | 同一份 JSON | 两个源码路径 |
| 本次新增可执行场景/断言代码 | 0 行 | 0 行 | 20 行脚本，可复用于相同接口 |
| 运行后修补源码/引擎/谓词 | 0 次 | 0 次 | 0 次 |
| 首次运行获得问题版反例 | 是 | 是，三个种子均获得 | 是 |
| 同一输入验证修复版 | 通过 | 通过 | 通过 |
| 相同反例再次重放 | 一致 | native seed/path 重放一致 | 两次新进程结果一致 |
| 逆向修改识别新违约 | 是 | 是 | 同一脚本在正确版通过、问题版失败 |
| 修复版→同一修复版控制 | 0 违约、0 差异 | 三个种子均未失败 | 修复版两次均通过 |
| 回调调用位置 | 默认记录 | 通用模型已附加调用帧 | 脚本附加调用帧 |

**这些行数和字段数是产物清单，不是人力或易用性测量。**P 和 F 都提前拥有回调领域知识；不能把 F 的公共属性模型算作这个新项目的成本。N 的 20 行是本次新写的，但接口相同的下一项目也可以复用它，不能假定每次重写。

公共实现成本：P 既有 `probe.py` 205 行及 `runner.mjs` 116 行；F 既有属性模型 189 行及准备/运行辅助脚本 132 行。它们职责并不完全相同，不能按行数排名。本次另写的 157 行 `run.py` 是三侧的实验编排/日志代码，`validate.py` 用于结果审计，并非隐藏在某一侧的项目业务实现。

## 真实反例与证据位置

最小行为是：注册一个 once 监听器，在它第一次执行时立即 emit 同一事件一次。

```text
问题版：外层进入回调 → 再次 emit → 再次进入同一回调 → 之后才移除
        总执行次数 2，违反 once_delivery
修复版：先移除 → 外层进入回调 → 再次 emit 找不到该监听器
        总执行次数 1，满足此场景的要求
```

P 的单监听器和双监听器场景均展示修复；逆向修改均引入违约。F 缩减出的输入为：

```json
{"listeners": 1, "reenter": true, "emissions": 1}
```

seed 17 的 path 为 `0:0:1`，正常缩减 2 次，原生报告位于 `run-01/F-repair/before/seed-17-once_delivery.txt`。三个种子均得到同一个最小输入。

问题版的回调调用位置为 `EventEmitter.js:368`，修复版为 `EventEmitter.js:373`。调用帧定位调用点；“移除发生在调用前还是后”的根因解释仍需结合周围源码，不能说堆栈已自动证明根因。

- P 完整观察：`run-01/P-repair/report.json`；单场景重放：`run-01/P-repair/replay.json`。
- P 反向修改及控制：`run-01/P-regression/`、`run-01/P-control/`。
- F：`run-01/F-{repair,regression,control}/{before,after}/seed-*.json`，含缩减输入、原生重放和调用帧。
- N：`run-01/N-snapshots/{before,after}-{1,2}.{json,stdout,stderr}`。问题版进程退出 1 是断言按预期失败，不是基础设施错误。
- 全部首次运行状态/机械耗时：`run-01/SUMMARY.json`；核查结论：`run-01/VALIDATION.json`。
- 原始来源、issue、diff、README 与树元数据：`upstream/PAYLOADS.json`；冻结 73 个文件的 SHA-256：`FROZEN.json`。

首次 F 编排只将 before 发现的输入传给 after，因此逆向修改的 before 无失败，尚未反向配对。随后 `validate.py` 从 after 的原始反例提取输入，额外启动 **1 个 worker**，在正确的 before 版重放并通过。原始结果保留于原目录，补充过程位于 `run-01/F-regression/backward-paired-replay/`。这一步补齐预定证据要求，没有修改冻结引擎、谓词或种子，也不能隐去该编排缺口后声称整个实验无需补充工作。

首轮编排中，P 执行 52 个场景侧进程，F 执行 18 个 worker，N 执行 4 个进程。之后 F 的配对核查补充 1 个 worker；文档里的 P 单场景 CLI 命令也实际执行了一次，另有 2 个场景侧进程，保留于 `probe-replay-02.json`。这些过程的生成范围、重复次数和隔离粒度不同，不能用进程数或秒数推出开发者效率。没有基础设施错误；所有冻结文件在前后校验一致。

## 如何解释价值

这次证明了：**在 API 和要求匹配时，工具能在一个新仓库上直接给出可以重放的前后违约证据，迁移无需增加特例。**

这次没有证明：**比直接使用现有通用属性模型更省配置、更快或更准确。**两侧的新增场景代码都是零，配置相同；如果已知应检查重入，一个很短的普通断言也足够。相对于完全没有领域模型的测试框架，工具封装了场景设计、执行和前后报告，但这里只展示了这项封装能工作，没有测出开发者实际节省多少工作。

因此，本轮结论是“迁移可用，适配优势未显示”。不能凭该样本支持通用效率提升或论文已经具备充分贡献。若继续验证价值，应先用独立选取的多种真实修改和未参与开发的使用者测量端到端任务，包含 API/要求判断与配置错误；不应继续靠挑同类小案例累积成功数。

## 重放

从 analyzer 仓库根目录运行。输出路径必须尚不存在。

工具只重放该反例：

```sh
python3 tools/temporal-behavior-probe/probe.py \
  external-tests/new-change-replay-comparison-v1/plan.json \
  --scenario once-reentry-1 \
  --output external-tests/new-change-replay-comparison-v1/probe-replay-02.json
```

重跑 F 的三个种子、修复/逆向/控制：

```sh
python3 -B external-tests/new-change-replay-comparison-v1/run.py \
  --arm F --output external-tests/new-change-replay-comparison-v1/fc-replay-02
```

普通断言重放问题版（预期退出 1，显示实际 2、预期 1）：

```sh
ELECTRON_RUN_AS_NODE=1 "/Applications/Visual Studio Code.app/Contents/MacOS/Code" \
  external-tests/new-change-replay-comparison-v1/plain-assert.cjs \
  external-tests/new-change-replay-comparison-v1/snapshots/before/EventEmitter.js
```

将最后一个路径中的 `before` 改成 `after`，预期退出 0。默认运行时来自本机 VS Code；若换成普通 Node，可直接用 node 执行该脚本。

本次仅新增此目录；没有改工具引擎、静态规则、其他实验或 bench 仓库，没有新增产品依赖，没有创建 Git 提交。核查由实施者执行，没有独立审查或用户研究。
